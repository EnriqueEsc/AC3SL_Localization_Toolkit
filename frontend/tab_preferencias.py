import os
import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QFileDialog, QGroupBox, 
                             QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
                             QComboBox, QCheckBox)
from PyQt5.QtCore import Qt

class TabPreferencias(QWidget):
    def __init__(self):
        super().__init__()
        self.ruta_config = "config_toolkit.json"
        self.config = self.cargar_configuracion()
        
        self.char_map_default = {
            "ñ": "@",
            "Ñ": "*",
            "¿": "&",
            "¡": "_"
        }
        
        self.caracteres_permitidos = list("$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~")
        
        self.init_ui()

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
            return True
        except Exception as e:
            print(f"Error guardando config: {e}")
            return False

    def init_ui(self):
        layout_principal = QVBoxLayout()
        layout_principal.setSpacing(15)

        # ==========================================
        # GRUPO 1: RUTAS GLOBALES
        # ==========================================
        grupo_rutas = QGroupBox("Rutas Globales de Herramientas y Archivos")
        layout_rutas = QVBoxLayout()

        ruta_defecto_dat = os.path.abspath(os.path.join("data", "dats"))

        l_dats = QHBoxLayout()
        self.txt_dats = QLineEdit(self.config.get('dats', ruta_defecto_dat))
        self.txt_dats.setPlaceholderText("Carpeta de contenedores .DAT...")
        btn_dats = QPushButton("Examinar")
        btn_dats.clicked.connect(lambda: self.seleccionar_ruta(self.txt_dats, 'dats', True))
        l_dats.addWidget(QLabel("Carpeta de Textos (.DAT):"), 1)
        l_dats.addWidget(self.txt_dats, 3)
        l_dats.addWidget(btn_dats, 1)

        l_slus = QHBoxLayout()
        self.txt_slus = QLineEdit(self.config.get('slus', ''))
        self.txt_slus.setPlaceholderText("Ruta del ejecutable original SLUS_206.44...")
        btn_slus = QPushButton("Examinar")
        btn_slus.clicked.connect(lambda: self.seleccionar_ruta(self.txt_slus, 'slus', False, "Ejecutables (*.44 *.ELF)"))
        l_slus.addWidget(QLabel("Ejecutable del Juego (SLUS):"), 1)
        l_slus.addWidget(self.txt_slus, 3)
        l_slus.addWidget(btn_slus, 1)

        l_exe = QHBoxLayout()
        self.txt_exe = QLineEdit(self.config.get('qbms_exe', ''))
        self.txt_exe.setPlaceholderText("Ruta a quickbms.exe...")
        btn_exe = QPushButton("Examinar")
        btn_exe.clicked.connect(lambda: self.seleccionar_ruta(self.txt_exe, 'qbms_exe', False, "Ejecutables (*.exe)"))
        l_exe.addWidget(QLabel("Herramienta QuickBMS (.exe):"), 1)
        l_exe.addWidget(self.txt_exe, 3)
        l_exe.addWidget(btn_exe, 1)

        l_script = QHBoxLayout()
        self.txt_script = QLineEdit(self.config.get('qbms_script', ''))
        self.txt_script.setPlaceholderText("Ruta al script silent_line.bms...")
        btn_script = QPushButton("Examinar")
        btn_script.clicked.connect(lambda: self.seleccionar_ruta(self.txt_script, 'qbms_script', False, "Scripts (*.bms)"))
        l_script.addWidget(QLabel("Script Extracción (.bms):"), 1)
        l_script.addWidget(self.txt_script, 3)
        l_script.addWidget(btn_script, 1)

        l_bin = QHBoxLayout()
        self.txt_bin = QLineEdit(self.config.get('bin', ''))
        self.txt_bin.setPlaceholderText("Ruta a tu copia de AC3DATA.BIN...")
        btn_bin = QPushButton("Examinar")
        btn_bin.clicked.connect(lambda: self.seleccionar_ruta(self.txt_bin, 'bin', False, "Archivos BIN (*.BIN *.bin)"))
        l_bin.addWidget(QLabel("Archivo Contenedor (BIN):"), 1)
        l_bin.addWidget(self.txt_bin, 3)
        l_bin.addWidget(btn_bin, 1)

        layout_rutas.addLayout(l_dats)
        layout_rutas.addLayout(l_slus)
        layout_rutas.addLayout(l_exe)
        layout_rutas.addLayout(l_script)
        layout_rutas.addLayout(l_bin)
        grupo_rutas.setLayout(layout_rutas)

        # ==========================================
        # GRUPO 2: MAPEO DE CARACTERES Y REGLAS
        # ==========================================
        grupo_chars = QGroupBox("Reglas de Texto y Mapeo de Caracteres Especiales")
        layout_chars = QVBoxLayout()

        # Checkbox de Simplificación de Acentos (Activado por defecto)
        self.chk_simplificar = QCheckBox("Simplificar caracteres con acentos automáticamente (á, é, í, ó, ú -> a, e, i, o, u)")
        self.chk_simplificar.setChecked(self.config.get('simplificar_acentos', True))
        self.chk_simplificar.setStyleSheet("color: #dddddd; font-size: 13px; font-weight: normal; margin-bottom: 5px;")
        layout_chars.addWidget(self.chk_simplificar)

        # Tabla de caracteres
        self.tabla_chars = QTableWidget(0, 2)
        self.tabla_chars.setHorizontalHeaderLabels(["Caracter a Escribir (Ej. ñ, ¿)", "Caracter In-Game (Asignado)"])
        self.tabla_chars.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_chars.setStyleSheet("""
            QTableWidget { background-color: #1e1e1e; color: #ffffff; gridline-color: #444444; border: 1px solid #555555; }
            QHeaderView::section { background-color: #2b2b2b; color: #dddddd; padding: 5px; border: 1px solid #444444; font-weight: bold; }
        """)

        self.cargar_tabla()

        layout_controles_tabla = QHBoxLayout()
        btn_agregar_fila = QPushButton("➕ Agregar Nueva Regla")
        btn_agregar_fila.setStyleSheet("QPushButton { background-color: #388E3C; color: white; padding: 5px; border-radius: 3px; font-weight: bold; }")
        btn_agregar_fila.clicked.connect(lambda: self.agregar_fila("", self.caracteres_permitidos[0]))

        btn_eliminar_fila = QPushButton("➖ Eliminar Regla Seleccionada")
        btn_eliminar_fila.setStyleSheet("QPushButton { background-color: #D32F2F; color: white; padding: 5px; border-radius: 3px; font-weight: bold; }")
        btn_eliminar_fila.clicked.connect(self.eliminar_fila)

        layout_controles_tabla.addWidget(btn_agregar_fila)
        layout_controles_tabla.addWidget(btn_eliminar_fila)
        layout_controles_tabla.addStretch()

        layout_chars.addWidget(self.tabla_chars)
        layout_chars.addLayout(layout_controles_tabla)
        grupo_chars.setLayout(layout_chars)

        # ==========================================
        # BOTÓN GUARDAR
        # ==========================================
        self.btn_guardar_todo = QPushButton("💾 GUARDAR PREFERENCIAS GLOBALES")
        self.btn_guardar_todo.setMinimumHeight(45)
        self.btn_guardar_todo.setStyleSheet("""
            QPushButton { background-color: #1976D2; color: white; font-weight: bold; border-radius: 4px; font-size: 14px; }
            QPushButton:hover { background-color: #1E88E5; }
        """)
        self.btn_guardar_todo.clicked.connect(self.guardar_todas_preferencias)

        layout_principal.addWidget(grupo_rutas)
        layout_principal.addWidget(grupo_chars)
        layout_principal.addWidget(self.btn_guardar_todo)
        
        self.setLayout(layout_principal)

    def seleccionar_ruta(self, line_edit, clave_config, es_carpeta, filtro="Todos (*.*)"):
        dir_inicial = os.path.dirname(line_edit.text()) if line_edit.text() else ""
        if es_carpeta:
            ruta = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta", dir_inicial)
        else:
            ruta, _ = QFileDialog.getOpenFileName(self, "Seleccionar Archivo", dir_inicial, filtro)
        
        if ruta:
            line_edit.setText(os.path.abspath(ruta))

    def cargar_tabla(self):
        char_map = self.config.get('char_map', self.char_map_default)
        self.tabla_chars.setRowCount(0)
        for char_real, char_juego in char_map.items():
            self.agregar_fila(char_real, char_juego)

    def agregar_fila(self, char_real, char_juego):
        row_position = self.tabla_chars.rowCount()
        self.tabla_chars.insertRow(row_position)
        
        item_real = QTableWidgetItem(char_real)
        item_real.setTextAlignment(Qt.AlignCenter)
        self.tabla_chars.setItem(row_position, 0, item_real)
        
        combo_in_game = QComboBox()
        combo_in_game.addItems(self.caracteres_permitidos)
        combo_in_game.setStyleSheet("""
            QComboBox { background-color: #2b2b2b; color: #ffffff; border: none; padding: 2px; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background-color: #323232; color: #ffffff; selection-background-color: #2196F3; }
        """)
        
        if char_juego in self.caracteres_permitidos:
            combo_in_game.setCurrentText(char_juego)
            
        self.tabla_chars.setCellWidget(row_position, 1, combo_in_game)

    def eliminar_fila(self):
        filas_seleccionadas = self.tabla_chars.selectionModel().selectedRows()
        if not filas_seleccionadas:
            QMessageBox.warning(self, "Aviso", "Selecciona una fila para eliminar.")
            return
        for index in sorted(filas_seleccionadas, reverse=True):
            self.tabla_chars.removeRow(index.row())

    def guardar_todas_preferencias(self):
        # 1. Guardar Estado de Acentos
        self.config['simplificar_acentos'] = self.chk_simplificar.isChecked()

        # 2. Guardar Rutas
        self.config['dats'] = self.txt_dats.text().strip()
        self.config['slus'] = self.txt_slus.text().strip()
        self.config['qbms_exe'] = self.txt_exe.text().strip()
        self.config['qbms_script'] = self.txt_script.text().strip()
        self.config['bin'] = self.txt_bin.text().strip()

        # 3. Validación y Guardado de Tabla
        nuevo_char_map = {}
        valores_in_game_usados = set()

        for row in range(self.tabla_chars.rowCount()):
            item_real = self.tabla_chars.item(row, 0)
            combo_juego = self.tabla_chars.cellWidget(row, 1) 
            
            if item_real and combo_juego:
                char_real = item_real.text().strip()
                char_juego = combo_juego.currentText()
                
                if not char_real: # Ignorar filas vacías
                    continue
                
                # Validación 1: El caracter real está duplicado (Ej: dos filas intentan mapear la 'ñ')
                if char_real in nuevo_char_map:
                    QMessageBox.warning(self, "Error de Mapeo", f"El caracter '{char_real}' está repetido en la columna izquierda. Revisa las reglas.")
                    return
                
                # Validación 2: El caracter del juego ya fue usado (Ej: intentan asignar la 'ñ' al @, y la 'Ñ' también al @)
                if char_juego in valores_in_game_usados:
                    QMessageBox.warning(self, "Error de Mapeo", f"El caracter in-game '{char_juego}' ya está asignado a otro valor.\nCada caracter del juego debe ser único.")
                    return

                nuevo_char_map[char_real] = char_juego
                valores_in_game_usados.add(char_juego)

        self.config['char_map'] = nuevo_char_map

        if self.guardar_configuracion():
            QMessageBox.information(self, "Guardado Exitoso", "Las preferencias y reglas de texto han sido actualizadas correctamente.")