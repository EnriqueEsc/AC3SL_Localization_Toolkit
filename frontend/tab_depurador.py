import os
import json
import re
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, 
                             QListWidget, QLineEdit, QLabel, QCheckBox,
                             QTextEdit, QPushButton, QMessageBox, QRadioButton, 
                             QButtonGroup, QProgressBar, QFileDialog) # <-- Añadimos QFileDialog aquí
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut
from PyQt5.QtWidgets import QProgressBar
from PyQt5.QtCore import QThread, pyqtSignal

class WorkerCargaJSON(QThread):
    progreso = pyqtSignal(int)
    terminado = pyqtSignal(list)

    def __init__(self, rutas_json):
        super().__init__()
        self.rutas_json = rutas_json # Ahora recibe una lista de rutas

    def run(self):
        textos_unicos = set()
        contador = 0
        total_items = 0
        data_archivos = []
        
        # 1. Primero cargamos todos los archivos a la memoria y calculamos el total
        for ruta in self.rutas_json:
            with open(ruta, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data_archivos.append(data)
                total_items += sum(len(v) for v in data.values())

        if total_items == 0:
            self.terminado.emit([])
            return

        # 2. Procesamos y unificamos todo
        for data in data_archivos:
            for archivo, entradas in data.items():
                for entrada in entradas:
                    original = entrada.get("original", "")
                    
                    # Filtro rápido de basura visual antes de mostrar en la GUI
                    if len(original) > 4 and not re.search(r'\[[A-F0-9]{2}\]', original):
                        textos_unicos.add(original)
                    
                    contador += 1
                    # Actualizar la barra de progreso cada 1000 items para no saturar la UI
                    if contador % 1000 == 0:
                        self.progreso.emit(int((contador / total_items) * 100))
        
        # Emitimos la lista final ordenada alfabéticamente
        self.terminado.emit(sorted(list(textos_unicos)))

class TabDepurador(QWidget):
    def __init__(self):
        super().__init__()
        # Diccionario en memoria para guardar el progreso { "texto": "bandera" }
        self.progreso = {}
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
        # Aseguramos que la carpeta exista
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

        # 1. El botón de cargar y la barra de progreso
        self.btn_cargar = QPushButton("📂 Cargar JSON Maestro")
        self.btn_cargar.setStyleSheet("background-color: #607D8B; color: white; font-weight: bold; padding: 5px;")
        self.btn_cargar.clicked.connect(self.abrir_archivo_json)
        
        self.barra_progreso = QProgressBar()
        self.barra_progreso.setValue(0)
        self.barra_progreso.setTextVisible(False) # La hacemos discreta
        self.barra_progreso.setFixedHeight(10)
        
        # 2. Fila de búsqueda
        layout_busqueda = QHBoxLayout()
        self.barra_busqueda = QLineEdit()
        self.barra_busqueda.setPlaceholderText("🔍 Buscar texto...")
        self.barra_busqueda.textChanged.connect(self.filtrar_lista)
        
        self.chk_mayusculas = QCheckBox("Aa Coincidir mayúsculas")
        self.chk_mayusculas.stateChanged.connect(self.filtrar_lista)
        
        layout_busqueda.addWidget(self.barra_busqueda)
        layout_busqueda.addWidget(self.chk_mayusculas)
        
        self.lista_textos = QListWidget()
        self.textos_originales = ["(Carga un JSON para comenzar)"]
        self.poblar_lista()

        # 3. Ensamblamos todo el panel izquierdo (¡AQUÍ FALTABAN LOS ADDWIDGET!)
        panel_izquierdo.addWidget(self.btn_cargar)
        panel_izquierdo.addWidget(self.barra_progreso)
        panel_izquierdo.addSpacing(10)
        panel_izquierdo.addWidget(QLabel("Entradas en Bruto:"))
        panel_izquierdo.addLayout(layout_busqueda)
        panel_izquierdo.addWidget(self.lista_textos)

        # ==========================================
        # PANEL DERECHO: Visualización y Banderas
        # ==========================================
        # (El resto de tu código del panel derecho sigue igual...)

        # ==========================================
        # PANEL DERECHO: Visualización y Banderas
        # ==========================================
        panel_derecho = QVBoxLayout()

        self.visor_texto = QTextEdit()
        self.visor_texto.setReadOnly(True)
        self.visor_texto.setStyleSheet("background-color: #f0f0f0; font-size: 16px; padding: 10px;")

        # Panel de Banderas (Radio Buttons para mejor UX)
        self.grupo_banderas = QButtonGroup(self)
        
        opciones = [
            (0, "0. NO TRADUCIR (Ignorar/Basura)"),
            (1, "1. Menú del Sistema (Fuente Angular)"),
            (2, "2. Diálogo / Briefing (Fuente Genérica)"),
            (3, "3. Nombres de Piezas / Tienda"),
            (4, "4. Interfaz / HUD de Combate")
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

        # Evento cuando cambias de radio button
        self.grupo_banderas.buttonClicked.connect(self.registrar_clasificacion)

        self.lbl_estado_guardado = QLabel("")
        self.lbl_estado_guardado.setStyleSheet("color: gray; font-style: italic;")

        self.btn_exportar = QPushButton("💾 CONSTRUIR PLANTILLA MAESTRA")
        self.btn_exportar.setMinimumHeight(50)
        self.btn_exportar.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; font-size: 14px;")

        panel_derecho.addSpacing(20)
        panel_derecho.addWidget(self.lbl_estado_guardado)
        panel_derecho.addStretch()
        panel_derecho.addWidget(self.btn_exportar)

        # Proporciones
        layout_principal.addLayout(panel_izquierdo, 1)
        layout_principal.addLayout(panel_derecho, 2)
        self.setLayout(layout_principal)
        
        self.lista_textos.currentItemChanged.connect(self.actualizar_visor)

    def configurar_atajos(self):
        # Atajos de teclado para clasificar a la velocidad de la luz
        for i in range(5):
            atajo = QShortcut(QKeySequence(str(i)), self)
            # Usamos un parámetro por defecto (val=i) en la lambda para atrapar el valor en el bucle
            atajo.activated.connect(lambda val=i: self.atajo_presionado(val))

    def atajo_presionado(self, id_opcion):
        if self.lista_textos.currentItem():
            # Selecciona el radio button visualmente
            self.radios[id_opcion].setChecked(True)
            # Registra y avanza
            self.registrar_clasificacion(self.radios[id_opcion])

    def poblar_lista(self):
        self.lista_textos.clear()
        for texto in self.textos_originales:
            # Si el texto ya tiene una bandera asignada, le ponemos un indicativo visual (✓)
            prefijo = "[✓] " if texto in self.progreso else ""
            self.lista_textos.addItem(prefijo + texto)

    def filtrar_lista(self):
        busqueda = self.barra_busqueda.text()
        case_sensitive = self.chk_mayusculas.isChecked()

        for i in range(self.lista_textos.count()):
            item = self.lista_textos.item(i)
            # Quitamos el prefijo [✓] para hacer la búsqueda limpia
            texto_limpio = item.text().replace("[✓] ", "") 
            
            if case_sensitive:
                match = busqueda in texto_limpio
            else:
                match = busqueda.lower() in texto_limpio.lower()
                
            item.setHidden(not match)

    def actualizar_visor(self, current, previous):
        if current:
            texto_limpio = current.text().replace("[✓] ", "")
            self.visor_texto.setText(texto_limpio)
            self.lbl_estado_guardado.setText("")
            
            # Si ya habíamos clasificado este texto antes, recuperar su bandera
            if texto_limpio in self.progreso:
                id_guardado = self.progreso[texto_limpio]
                self.radios[id_guardado].setChecked(True)
            else:
                # Quitar selecciones si es nuevo
                self.grupo_banderas.setExclusive(False)
                for btn in self.grupo_banderas.buttons():
                    btn.setChecked(False)
                self.grupo_banderas.setExclusive(True)

    def registrar_clasificacion(self, button):
        item_actual = self.lista_textos.currentItem()
        if not item_actual: return

        # Guardar en el diccionario en memoria
        texto_limpio = item_actual.text().replace("[✓] ", "")
        id_opcion = self.grupo_banderas.id(button)
        self.progreso[texto_limpio] = id_opcion

        # Marcar visualmente en la lista
        if not item_actual.text().startswith("[✓]"):
            item_actual.setText("[✓] " + texto_limpio)

        # Disparar Auto-Guardado en archivo
        self.guardar_progreso()

        # ¡Magia de UX! Saltar automáticamente al siguiente elemento de la lista
        fila_actual = self.lista_textos.currentRow()
        if fila_actual < self.lista_textos.count() - 1:
            self.lista_textos.setCurrentRow(fila_actual + 1)
    
    def abrir_archivo_json(self):
        # Usamos getOpenFileNames (plural) para seleccionar varios archivos a la vez
        rutas, _ = QFileDialog.getOpenFileNames(self, "Seleccionar JSON(s)", "", "JSON (*.json)")
        
        if rutas: # 'rutas' ahora es una lista de archivos, ej: ['SilentLine_Master.json', 'SLUS_Master.json']
            self.barra_progreso.setValue(0)
            self.worker = WorkerCargaJSON(rutas) # Le pasamos la lista entera al Worker
            self.worker.progreso.connect(self.barra_progreso.setValue)
            self.worker.terminado.connect(self.cargar_lista_final)
            self.worker.start()

    def cargar_lista_final(self, lista_textos):
        self.textos_originales = lista_textos
        self.poblar_lista()
        self.barra_progreso.setValue(100)