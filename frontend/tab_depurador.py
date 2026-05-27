import os
import json
import re
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, 
                             QListWidget, QLineEdit, QLabel, QCheckBox,
                             QTextEdit, QPushButton, QMessageBox, QRadioButton, 
                             QButtonGroup, QProgressBar, QFileDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut

class WorkerCargaJSON(QThread):
    terminado = pyqtSignal(list, dict, dict)
    progreso = pyqtSignal(int)

    def __init__(self, rutas_json):
        super().__init__()
        self.rutas_json = rutas_json

    def run(self):
        textos_unicos = {}      # { "texto": min_max_bytes }
        tags_importados = {}    # { "texto": id_etiqueta }
        total_items = 0
        data_archivos = []
        
        # 1. Cargamos todos los archivos a memoria y calculamos su tamaño real
        for ruta in self.rutas_json:
            with open(ruta, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data_archivos.append(data)
                
                if not data:
                    continue
                    
                # Detectamos la estructura del JSON analizando su primer elemento
                primer_valor = next(iter(data.values()))
                
                if isinstance(primer_valor, list):
                    # Formato crudo de extractores: {"02032.dat": [ {...}, {...} ]}
                    total_items += sum(len(v) for v in data.values() if isinstance(v, list))
                else:
                    # Formato Plantilla {"Texto": {...}} o Progreso {"Texto": 1}
                    total_items += len(data)

        if total_items == 0:
            self.terminado.emit([], {}, {})
            return

        contador = 0
        
        # 2. Procesamiento Inteligente Multiformato
        for data in data_archivos:
            if not data:
                continue
                
            primer_valor = next(iter(data.values()))
            
            # TIPO A: Es un JSON en bruto de los extractores (dict de listas)
            if isinstance(primer_valor, list):
                for archivo, entradas in data.items():
                    if not isinstance(entradas, list): continue
                    for entrada in entradas:
                        original = entrada.get("original", "")
                        
                        # Filtro de basura visual
                        if len(original) > 4 and not re.search(r'\[[A-F0-9]{2}\]', original):
                            mb = entrada.get("max_bytes", 9999)
                            if original not in textos_unicos or mb < textos_unicos[original]:
                                textos_unicos[original] = mb
                        
                        contador += 1
                        if contador % 1000 == 0:
                            self.progreso.emit(int((contador / total_items) * 100))
                            
            # TIPO B: Es la Plantilla Maestra (dict de dicts)
            elif isinstance(primer_valor, dict):
                for texto, info in data.items():
                    if "tipo" in info:
                        tags_importados[texto] = info["tipo"]
                    
                    mb = info.get("max_bytes", 9999)
                    if texto not in textos_unicos or mb < textos_unicos[texto]:
                        textos_unicos[texto] = mb
                    
                    contador += 1
                    if contador % 1000 == 0:
                        self.progreso.emit(int((contador / total_items) * 100))
                        
            # TIPO C: Es un archivo de progreso simple (dict de enteros)
            elif isinstance(primer_valor, int):
                for texto, flag in data.items():
                    tags_importados[texto] = flag
                    # Si no tenemos el texto en memoria, lo agregamos con un límite seguro
                    if texto not in textos_unicos:
                        textos_unicos[texto] = 9999 
                        
                    contador += 1
                    if contador % 1000 == 0:
                        self.progreso.emit(int((contador / total_items) * 100))
        
        # Emitimos los datos procesados a la interfaz
        lista_ordenada = sorted(list(textos_unicos.keys()))
        self.terminado.emit(lista_ordenada, textos_unicos, tags_importados)

class TabDepurador(QWidget):
    def __init__(self):
        super().__init__()
        self.progreso = {}
        self.metadata_textos = {} # Guardará los max_bytes
        self.archivo_temporal = os.path.join("data", "raw_output", "progreso_depuracion.json")
        self.cargar_progreso()
        
        self.init_ui()
        self.configurar_atajos()

    def cargar_progreso(self):
        if os.path.exists(self.archivo_temporal):
            try:
                with open(self.archivo_temporal, 'r', encoding='utf-8') as f:
                    self.progreso = json.load(f)
            except Exception as e:
                print(f"Error cargando progreso temporal: {e}")

    def guardar_progreso(self):
        os.makedirs(os.path.dirname(self.archivo_temporal), exist_ok=True)
        with open(self.archivo_temporal, 'w', encoding='utf-8') as f:
            json.dump(self.progreso, f, ensure_ascii=False, indent=4)
        self.lbl_estado_guardado.setText("✅ Guardado automático")

    def init_ui(self):
        layout_principal = QHBoxLayout()

        # ==========================================
        # PANEL IZQUIERDO: Búsqueda y Lista
        # ==========================================
        panel_izquierdo = QVBoxLayout()

        self.btn_cargar = QPushButton("📂 Cargar JSON(s) para Depurar o Merge")
        self.btn_cargar.setStyleSheet("background-color: #607D8B; color: white; font-weight: bold; padding: 8px;")
        self.btn_cargar.clicked.connect(self.abrir_archivo_json)
        
        self.barra_progreso = QProgressBar()
        self.barra_progreso.setValue(0)
        self.barra_progreso.setTextVisible(False)
        self.barra_progreso.setFixedHeight(10)
        
        layout_busqueda = QHBoxLayout()
        self.barra_busqueda = QLineEdit()
        self.barra_busqueda.setPlaceholderText("🔍 Buscar texto...")
        self.barra_busqueda.textChanged.connect(self.filtrar_lista)
        
        layout_filtros = QVBoxLayout()
        self.chk_mayusculas = QCheckBox("Aa Coincidir mayúsculas")
        self.chk_mayusculas.stateChanged.connect(self.filtrar_lista)
        
        self.chk_ocultar = QCheckBox("🚫 Excluir ya etiquetados")
        self.chk_ocultar.stateChanged.connect(self.filtrar_lista)
        
        layout_filtros.addWidget(self.chk_mayusculas)
        layout_filtros.addWidget(self.chk_ocultar)
        
        layout_busqueda.addWidget(self.barra_busqueda)
        layout_busqueda.addLayout(layout_filtros)
        
        self.lista_textos = QListWidget()
        self.lista_textos.setSelectionMode(QListWidget.ExtendedSelection)
        
        # --- LOS TRES TRUCOS ANTI-SALTOS DE UX ---
        self.lista_textos.setUniformItemSizes(True) # Truco 1: Evita el recálculo de alto
        self.lista_textos.setWordWrap(False)        # Truco 2: Fuerza que sea una sola línea visual
        self.lista_textos.setLayoutMode(QListWidget.Batched) # Truco 3: Dibuja por lotes
        
        self.textos_originales = ["(Carga un JSON para comenzar)"]
        self.poblar_lista()

        panel_izquierdo.addWidget(self.btn_cargar)
        panel_izquierdo.addWidget(self.barra_progreso)
        panel_izquierdo.addSpacing(10)
        panel_izquierdo.addWidget(QLabel("Entradas en Bruto (Usa Shift/Ctrl para selección múltiple):"))
        panel_izquierdo.addLayout(layout_busqueda)
        panel_izquierdo.addWidget(self.lista_textos)

        # ==========================================
        # PANEL DERECHO: Visualización y Banderas
        # ==========================================
        panel_derecho = QVBoxLayout()

        self.visor_texto = QTextEdit()
        self.visor_texto.setReadOnly(True)
        self.visor_texto.setStyleSheet("background-color: #f0f0f0; font-size: 16px; padding: 10px;")

        self.grupo_banderas = QButtonGroup(self)
        
        opciones = [
            (0, "0. NO TRADUCIR (Ignorar/Basura)"),
            (1, "1. Menú / Interfaz (SIEMPRE MAYÚSCULAS)"),
            (2, "2. Diálogo / Descripción (Usa \\n)"),
            (3, "3. Mails / Correos (Usa <BR>)"),
            (4, "4. Briefings de Misión (Códigos & y *)")
        ]

        panel_derecho.addWidget(QLabel("Texto Original Seleccionado:"))
        panel_derecho.addWidget(self.visor_texto)
        panel_derecho.addWidget(QLabel("Clasificación Rápida (Usa las teclas 0-4):"))

        self.radios = {}
        for id_opcion, texto in opciones:
            radio = QRadioButton(texto)
            radio.setStyleSheet("font-size: 14px; padding: 5px;")
            self.grupo_banderas.addButton(radio, id_opcion)
            panel_derecho.addWidget(radio)
            self.radios[id_opcion] = radio

        self.grupo_banderas.buttonClicked.connect(self.registrar_clasificacion)

        self.lbl_estado_guardado = QLabel("")
        self.lbl_estado_guardado.setStyleSheet("color: gray; font-style: italic;")

        self.btn_exportar = QPushButton("💾 EXPORTAR PLANTILLA MAESTRA")
        self.btn_exportar.setMinimumHeight(50)
        self.btn_exportar.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; font-size: 14px;")
        self.btn_exportar.clicked.connect(self.exportar_plantilla)

        panel_derecho.addSpacing(20)
        panel_derecho.addWidget(self.lbl_estado_guardado)
        panel_derecho.addStretch()
        panel_derecho.addWidget(self.btn_exportar)

        layout_principal.addLayout(panel_izquierdo, 1)
        layout_principal.addLayout(panel_derecho, 2)
        self.setLayout(layout_principal)
        
        self.lista_textos.currentItemChanged.connect(self.actualizar_visor)

    def configurar_atajos(self):
        for i in range(5):
            atajo = QShortcut(QKeySequence(str(i)), self)
            atajo.activated.connect(lambda val=i: self.atajo_presionado(val))

    def atajo_presionado(self, id_opcion):
        if self.lista_textos.selectedItems():
            self.radios[id_opcion].setChecked(True)
            self.registrar_clasificacion(self.radios[id_opcion])

    def poblar_lista(self):
        self.lista_textos.clear()
        
        self.lista_textos.setUpdatesEnabled(False) # Congelamos la vista mientras llenamos
        for texto in self.textos_originales:
            prefijo = "[✓] " if texto in self.progreso else ""
            self.lista_textos.addItem(prefijo + texto)
        self.lista_textos.setUpdatesEnabled(True)  # Descongelamos
        
        self.lista_textos.scrollToTop()
        self.filtrar_lista()

    def filtrar_lista(self):
        busqueda = self.barra_busqueda.text()
        case_sensitive = self.chk_mayusculas.isChecked()
        ocultar_etiquetados = self.chk_ocultar.isChecked()

        self.lista_textos.setUpdatesEnabled(False) # Congelamos gráficos

        for i in range(self.lista_textos.count()):
            item = self.lista_textos.item(i)
            es_etiquetado = item.text().startswith("[✓]")
            texto_limpio = item.text().replace("[✓] ", "") 
            
            if ocultar_etiquetados and es_etiquetado:
                item.setHidden(True)
                continue

            if case_sensitive:
                match = busqueda in texto_limpio
            else:
                match = busqueda.lower() in texto_limpio.lower()
                
            item.setHidden(not match)

        self.lista_textos.setUpdatesEnabled(True) # Descongelamos gráficos

    def actualizar_visor(self, current, previous):
        if current:
            texto_limpio = current.text().replace("[✓] ", "")
            self.visor_texto.setText(texto_limpio)
            self.lbl_estado_guardado.setText("")
            
            if texto_limpio in self.progreso:
                id_guardado = self.progreso[texto_limpio]
                self.radios[id_guardado].setChecked(True)
            else:
                self.grupo_banderas.setExclusive(False)
                for btn in self.grupo_banderas.buttons():
                    btn.setChecked(False)
                self.grupo_banderas.setExclusive(True)

    def registrar_clasificacion(self, button):
        items_seleccionados = self.lista_textos.selectedItems()
        if not items_seleccionados: return

        # Guardamos la posición exacta del scroll
        scrollbar = self.lista_textos.verticalScrollBar()
        posicion_actual = scrollbar.value()

        id_opcion = self.grupo_banderas.id(button)
        ultima_fila = 0

        self.lista_textos.setUpdatesEnabled(False) # Evitamos el parpadeo y los saltos

        for item in items_seleccionados:
            texto_limpio = item.text().replace("[✓] ", "")
            self.progreso[texto_limpio] = id_opcion

            if not item.text().startswith("[✓]"):
                item.setText("[✓] " + texto_limpio)
            
            fila = self.lista_textos.row(item)
            if fila > ultima_fila:
                ultima_fila = fila

        self.guardar_progreso()
        self.lista_textos.setUpdatesEnabled(True)

        self.filtrar_lista() # El filtro se encarga de esconder si la exclusión está activa

        self.lista_textos.clearSelection()

        # Restauramos el scroll, a menos que hayamos excluido el elemento de la vista
        if not self.chk_ocultar.isChecked():
            scrollbar.setValue(posicion_actual)

        # Buscamos la siguiente fila que no esté oculta y avanzamos a ella
        siguiente_fila = ultima_fila + 1
        while siguiente_fila < self.lista_textos.count():
            item_siguiente = self.lista_textos.item(siguiente_fila)
            if not item_siguiente.isHidden():
                self.lista_textos.setCurrentRow(siguiente_fila)
                self.lista_textos.scrollToItem(item_siguiente)
                break
            siguiente_fila += 1
    
    def abrir_archivo_json(self):
        rutas, _ = QFileDialog.getOpenFileNames(self, "Seleccionar JSON(s)", "", "JSON (*.json)")
        
        if rutas:
            self.barra_progreso.setValue(0)
            self.worker = WorkerCargaJSON(rutas)
            self.worker.progreso.connect(self.barra_progreso.setValue)
            self.worker.terminado.connect(self.cargar_lista_final)
            self.worker.start()

    def cargar_lista_final(self, lista_textos, metadata_textos, tags_importados):
        self.textos_originales = lista_textos
        self.metadata_textos = metadata_textos
        
        if tags_importados:
            self.progreso.update(tags_importados)
            self.guardar_progreso()
            QMessageBox.information(self, "Merge Exitoso", f"Se importaron {len(tags_importados)} etiquetas previas.")

        self.poblar_lista()
        self.barra_progreso.setValue(100)

    def exportar_plantilla(self):
        if not self.progreso:
            QMessageBox.warning(self, "Aviso", "No hay datos clasificados para exportar.")
            return

        plantilla_final = {}
        for texto, flag in self.progreso.items():
            if flag == 0:
                continue
            
            mb = self.metadata_textos.get(texto, 255) 
            
            plantilla_final[texto] = {
                "traduccion": "",
                "max_bytes": mb,
                "tipo": flag
            }

        ruta_salida = os.path.join("translation", "Plantilla_Maestra.json")
        os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
        
        with open(ruta_salida, 'w', encoding='utf-8') as f:
            json.dump(plantilla_final, f, ensure_ascii=False, indent=4)
            
        QMessageBox.information(self, "Exportación Exitosa", 
                                f"Se ha construido la Plantilla Maestra en la carpeta 'translation'.\n"
                                f"Contiene {len(plantilla_final)} cadenas listas para ser traducidas.")