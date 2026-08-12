import os
import json
import re
import shutil # <-- NUEVA IMPORTACIÓN PARA CREAR BACKUPS
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, 
                             QListWidget, QLineEdit, QLabel, QCheckBox,
                             QTextEdit, QPushButton, QMessageBox, QRadioButton, 
                             QButtonGroup, QProgressBar, QFileDialog, QGroupBox,
                             QApplication)
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
        textos_unicos = {}      
        tags_importados = {}    
        total_items = 0
        data_archivos = []
        
        for ruta in self.rutas_json:
            with open(ruta, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data_archivos.append(data)
                
                if not data:
                    continue
                    
                primer_valor = next(iter(data.values()))
                
                if isinstance(primer_valor, list):
                    total_items += sum(len(v) for v in data.values() if isinstance(v, list))
                else:
                    total_items += len(data)

        if total_items == 0:
            self.terminado.emit([], {}, {})
            return

        contador = 0
        
        for data in data_archivos:
            if not data:
                continue
                
            primer_valor = next(iter(data.values()))
            
            if isinstance(primer_valor, list):
                for archivo, entradas in data.items():
                    if not isinstance(entradas, list): continue
                    for entrada in entradas:
                        original = entrada.get("original", "")
                        
                        if len(original) >= 4 and not re.search(r'\[[A-F0-9]{2}\]', original):
                            mb = entrada.get("max_bytes", 9999)
                            if original not in textos_unicos or mb < textos_unicos[original]:
                                textos_unicos[original] = mb
                        
                        contador += 1
                        if contador % 1000 == 0:
                            self.progreso.emit(int((contador / total_items) * 100))
                            
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
                        
            elif isinstance(primer_valor, int):
                for texto, flag in data.items():
                    tags_importados[texto] = flag
                    if texto not in textos_unicos:
                        textos_unicos[texto] = 9999 
                        
                    contador += 1
                    if contador % 1000 == 0:
                        self.progreso.emit(int((contador / total_items) * 100))
        
        lista_ordenada = sorted(list(textos_unicos.keys()))
        self.terminado.emit(lista_ordenada, textos_unicos, tags_importados)


class TabDepurador(QWidget):
    def __init__(self):
        super().__init__()
        self.progreso = {}
        self.metadata_textos = {}
        self.archivo_temporal = os.path.join("data", "raw_output", "progreso_depuracion.json")
        self.ruta_config = "config_toolkit.json"
        self.config = self.cargar_configuracion()
        
        self.cargar_progreso()
        self.init_ui()
        self.configurar_atajos()

    def cargar_configuracion(self):
        if os.path.exists(self.ruta_config):
            try:
                with open(self.ruta_config, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def guardar_configuracion(self):
        try:
            with open(self.ruta_config, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error guardando config: {e}")

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
        self.lbl_estado_guardado.setText("✅ Guardado automático local")

    def init_ui(self):
        layout_principal = QHBoxLayout()

        # ==========================================
        # PANEL IZQUIERDO: Búsqueda y Lista
        # ==========================================
        grupo_izquierdo = QGroupBox("Archivos y Filtros de Depuración")
        panel_izquierdo = QVBoxLayout()

        self.btn_cargar = QPushButton("📂 Cargar JSON(s) para Depurar o Merge")
        self.btn_cargar.setStyleSheet("""
            QPushButton { background-color: #455A64; color: white; font-weight: bold; border-radius: 4px; padding: 8px; }
            QPushButton:hover { background-color: #546E7A; }
        """)
        self.btn_cargar.clicked.connect(self.abrir_archivo_json)
        
        self.barra_progreso = QProgressBar()
        self.barra_progreso.setValue(0)
        self.barra_progreso.setTextVisible(False)
        self.barra_progreso.setFixedHeight(8)
        
        layout_busqueda = QHBoxLayout()
        self.barra_busqueda = QLineEdit()
        self.barra_busqueda.setPlaceholderText("🔍 Buscar texto... (Presiona Enter)")
        self.barra_busqueda.returnPressed.connect(self.filtrar_lista)
        
        layout_filtros = QVBoxLayout()
        
        estilo_checks = "color: #dddddd; font-size: 13px;"
        
        self.chk_mayusculas = QCheckBox("Aa Coincidir mayúsculas")
        self.chk_mayusculas.setStyleSheet(estilo_checks)
        self.chk_mayusculas.stateChanged.connect(self.filtrar_lista)
        
        self.chk_ocultar = QCheckBox("🚫 Excluir ya etiquetados")
        self.chk_ocultar.setStyleSheet(estilo_checks)
        self.chk_ocultar.stateChanged.connect(self.filtrar_lista)
        
        layout_filtros.addWidget(self.chk_mayusculas)
        layout_filtros.addWidget(self.chk_ocultar)
        
        layout_busqueda.addWidget(self.barra_busqueda)
        layout_busqueda.addLayout(layout_filtros)
        
        self.lista_textos = QListWidget()
        self.lista_textos.setSelectionMode(QListWidget.ExtendedSelection)
        self.lista_textos.setUniformItemSizes(True) 
        self.lista_textos.setWordWrap(False)        
        self.lista_textos.setLayoutMode(QListWidget.Batched) 
        
        self.textos_originales = ["(Carga un JSON para comenzar)"]
        self.poblar_lista()

        panel_izquierdo.addWidget(self.btn_cargar)
        panel_izquierdo.addWidget(self.barra_progreso)
        panel_izquierdo.addSpacing(10)
        panel_izquierdo.addWidget(QLabel("Entradas en Bruto (Usa Shift/Ctrl para selección múltiple):"))
        panel_izquierdo.addLayout(layout_busqueda)
        panel_izquierdo.addWidget(self.lista_textos)
        grupo_izquierdo.setLayout(panel_izquierdo)

        # ==========================================
        # PANEL DERECHO: Visualización y Banderas
        # ==========================================
        grupo_derecho = QGroupBox("Visor y Clasificación Rápida")
        panel_derecho = QVBoxLayout()

        self.visor_texto = QTextEdit()
        self.visor_texto.setReadOnly(True)
        self.visor_texto.setStyleSheet("background-color: #121212; color: #ffffff; font-size: 15px; padding: 10px; border: 1px solid #444444; border-radius: 4px;")

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
        panel_derecho.addSpacing(10)
        panel_derecho.addWidget(QLabel("Clasificación Rápida (Atajos: Teclas 0 al 4):"))

        self.radios = {}
        for id_opcion, texto in opciones:
            radio = QRadioButton(texto)
            radio.setStyleSheet("color: #dddddd; font-size: 14px; padding: 3px;")
            self.grupo_banderas.addButton(radio, id_opcion)
            panel_derecho.addWidget(radio)
            self.radios[id_opcion] = radio

        self.grupo_banderas.buttonClicked.connect(self.registrar_clasificacion)

        self.lbl_estado_guardado = QLabel("")
        self.lbl_estado_guardado.setStyleSheet("color: #888888; font-style: italic;")

        self.btn_exportar = QPushButton("💾 EXPORTAR PLANTILLA MAESTRA")
        self.btn_exportar.setMinimumHeight(45)
        self.btn_exportar.setStyleSheet("""
            QPushButton { background-color: #1976D2; color: white; font-weight: bold; border-radius: 4px; font-size: 14px; }
            QPushButton:hover { background-color: #1E88E5; }
        """)
        self.btn_exportar.clicked.connect(self.exportar_plantilla)

        panel_derecho.addSpacing(20)
        panel_derecho.addWidget(self.lbl_estado_guardado)
        panel_derecho.addStretch()
        panel_derecho.addWidget(self.btn_exportar)
        grupo_derecho.setLayout(panel_derecho)

        layout_principal.addWidget(grupo_izquierdo, 1)
        layout_principal.addWidget(grupo_derecho, 2)
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
        self.lista_textos.setUpdatesEnabled(False)
        for texto in self.textos_originales:
            prefijo = "[✓] " if texto in self.progreso else ""
            self.lista_textos.addItem(prefijo + texto)
        self.lista_textos.setUpdatesEnabled(True) 
        
        self.lista_textos.scrollToTop()
        self.filtrar_lista()

    def filtrar_lista(self):
        busqueda = self.barra_busqueda.text()
        case_sensitive = self.chk_mayusculas.isChecked()
        ocultar_etiquetados = self.chk_ocultar.isChecked()

        total_items = self.lista_textos.count()
        if total_items == 0:
            return

        self.barra_busqueda.setEnabled(False)
        self.chk_mayusculas.setEnabled(False)
        self.chk_ocultar.setEnabled(False)
        self.lista_textos.setUpdatesEnabled(False)

        self.barra_progreso.setMaximum(total_items)
        self.barra_progreso.setValue(0)

        for i in range(total_items):
            item = self.lista_textos.item(i)
            es_etiquetado = item.text().startswith("[✓]")
            texto_limpio = item.text().replace("[✓] ", "") 
            
            if ocultar_etiquetados and es_etiquetado:
                item.setHidden(True)
            else:
                if case_sensitive:
                    match = busqueda in texto_limpio
                else:
                    match = busqueda.lower() in texto_limpio.lower()
                    
                item.setHidden(not match)

            if i % 150 == 0:
                self.barra_progreso.setValue(i)
                QApplication.processEvents()

        self.barra_progreso.setValue(total_items)
        self.lista_textos.setUpdatesEnabled(True)
        
        self.barra_busqueda.setEnabled(True)
        self.chk_mayusculas.setEnabled(True)
        self.chk_ocultar.setEnabled(True)
        self.barra_busqueda.setFocus()

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

        scrollbar = self.lista_textos.verticalScrollBar()
        posicion_actual = scrollbar.value()

        id_opcion = self.grupo_banderas.id(button)
        ultima_fila = 0
        ocultar_activo = self.chk_ocultar.isChecked() 

        self.lista_textos.setUpdatesEnabled(False)

        for item in items_seleccionados:
            texto_limpio = item.text().replace("[✓] ", "")
            self.progreso[texto_limpio] = id_opcion

            if not item.text().startswith("[✓]"):
                item.setText("[✓] " + texto_limpio)
            
            if ocultar_activo:
                item.setHidden(True)
            
            fila = self.lista_textos.row(item)
            if fila > ultima_fila:
                ultima_fila = fila

        self.guardar_progreso()
        
        self.lista_textos.clearSelection()

        if not ocultar_activo:
            scrollbar.setValue(posicion_actual)

        siguiente_fila = ultima_fila + 1
        while siguiente_fila < self.lista_textos.count():
            item_siguiente = self.lista_textos.item(siguiente_fila)
            if not item_siguiente.isHidden():
                self.lista_textos.setCurrentRow(siguiente_fila)
                self.lista_textos.scrollToItem(item_siguiente)
                break
            siguiente_fila += 1
            
        self.lista_textos.setUpdatesEnabled(True)
    
    def abrir_archivo_json(self):
        dir_inicial = self.config.get("ultimo_dir_json", "")
        rutas, _ = QFileDialog.getOpenFileNames(self, "Seleccionar JSON(s)", dir_inicial, "JSON (*.json)")
        
        if rutas:
            self.config["ultimo_dir_json"] = os.path.dirname(os.path.abspath(rutas[0]))
            self.guardar_configuracion()
            
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

    # ==========================================
    # NUEVA LÓGICA DE EXPORTACIÓN CON MERGE Y BACKUP
    # ==========================================
    def exportar_plantilla(self):
        if not self.progreso:
            QMessageBox.warning(self, "Aviso", "No hay datos clasificados para exportar.")
            return

        ruta_salida = os.path.join("translation", "Plantilla_Maestra.json")
        os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)

        plantilla_existente = {}
        backup_creado = False

        # 1. Crear backup y leer la plantilla antigua si ya existe
        if os.path.exists(ruta_salida):
            try:
                ruta_backup = os.path.join("translation", "Plantilla_Maestra_backup.json")
                shutil.copy2(ruta_salida, ruta_backup)
                backup_creado = True
                
                with open(ruta_salida, 'r', encoding='utf-8') as f:
                    plantilla_existente = json.load(f)
            except Exception as e:
                print(f"No se pudo respaldar o leer la plantilla existente: {e}")

        plantilla_final = {}
        textos_recuperados = 0

        # 2. Construir la nueva plantilla fusionando datos
        for texto, flag in self.progreso.items():
            if flag == 0:
                continue
            
            mb = self.metadata_textos.get(texto, 255) 
            
            # Rescatar la traducción si el texto ya estaba en la plantilla anterior
            traduccion_previa = ""
            if texto in plantilla_existente:
                traduccion_previa = plantilla_existente[texto].get("traduccion", "")
                if traduccion_previa.strip():
                    textos_recuperados += 1
            
            plantilla_final[texto] = {
                "traduccion": traduccion_previa,
                "max_bytes": mb,
                "tipo": flag
            }

        # 3. Sobreescribir con los datos combinados
        with open(ruta_salida, 'w', encoding='utf-8') as f:
            json.dump(plantilla_final, f, ensure_ascii=False, indent=4)
            
        mensaje_final = f"Se ha construido la Plantilla Maestra en la carpeta 'translation'.\nContiene {len(plantilla_final)} cadenas."
        
        if backup_creado:
            mensaje_final += f"\n\nSe respetaron {textos_recuperados} traducciones previas mediante Merge."
            mensaje_final += "\nSe creó una copia de seguridad (Plantilla_Maestra_backup.json)."

        QMessageBox.information(self, "Exportación Exitosa", mensaje_final)