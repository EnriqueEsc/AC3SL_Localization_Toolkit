from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, 
                             QListWidget, QLineEdit, QLabel, 
                             QTextEdit, QComboBox, QPushButton, QMessageBox)
from PyQt5.QtCore import Qt

class TabDepurador(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout_principal = QHBoxLayout()

        # ==========================================
        # PANEL IZQUIERDO: Búsqueda y Lista
        # ==========================================
        panel_izquierdo = QVBoxLayout()
        
        self.barra_busqueda = QLineEdit()
        self.barra_busqueda.setPlaceholderText("🔍 Buscar texto original...")
        
        self.lista_textos = QListWidget()
        # Aquí cargaremos el JSON después. Por ahora, datos de prueba:
        self.lista_textos.addItems(["WEIGHT", "SAVE GAME DATA?", "褂[EC][F2][DD] (Basura)"])

        panel_izquierdo.addWidget(QLabel("Entradas en Bruto:"))
        panel_izquierdo.addWidget(self.barra_busqueda)
        panel_izquierdo.addWidget(self.lista_textos)

        # ==========================================
        # PANEL DERECHO: Visualización y Banderas
        # ==========================================
        panel_derecho = QVBoxLayout()

        self.visor_texto = QTextEdit()
        self.visor_texto.setReadOnly(True) # Para no editar accidentalmente el original
        self.visor_texto.setStyleSheet("background-color: #f0f0f0; font-size: 14px;")

        self.combo_banderas = QComboBox()
        self.combo_banderas.addItems([
            "0. NO TRADUCIR (Ignorar/Basura)",
            "1. Menú del Sistema (Fuente Angular)",
            "2. Diálogo / Briefing (Fuente Genérica)",
            "3. Nombres de Piezas / Tienda",
            "4. Interfaz / HUD de Combate"
        ])

        self.btn_guardar_siguiente = QPushButton("Guardar Bandera y Siguiente ->")
        self.btn_guardar_siguiente.setMinimumHeight(40)
        self.btn_guardar_siguiente.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")

        self.btn_exportar = QPushButton("💾 EXPORTAR PLANTILLA MAESTRA")
        self.btn_exportar.setMinimumHeight(50)
        self.btn_exportar.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")

        panel_derecho.addWidget(QLabel("Texto Original Seleccionado:"))
        panel_derecho.addWidget(self.visor_texto)
        panel_derecho.addWidget(QLabel("Etiqueta de Clasificación:"))
        panel_derecho.addWidget(self.combo_banderas)
        panel_derecho.addSpacing(20)
        panel_derecho.addWidget(self.btn_guardar_siguiente)
        panel_derecho.addStretch() # Empuja el botón de exportar hacia abajo
        panel_derecho.addWidget(self.btn_exportar)

        # Proporciones (Izquierda toma 1/3, Derecha toma 2/3)
        layout_principal.addLayout(panel_izquierdo, 1)
        layout_principal.addLayout(panel_derecho, 2)

        self.setLayout(layout_principal)
        
        # Conexiones (Eventos)
        self.lista_textos.currentItemChanged.connect(self.actualizar_visor)

    def actualizar_visor(self, current, previous):
        if current:
            self.visor_texto.setText(current.text())