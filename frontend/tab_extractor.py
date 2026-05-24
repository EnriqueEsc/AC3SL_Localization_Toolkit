import sys
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QTextEdit, QFileDialog, QGroupBox)
from PyQt5.QtCore import QThread, pyqtSignal, QObject

# Importamos tu backend
from backend.acsl_extractor import generar_diccionario_json
from backend.slus_extractor import extraer_textos_elf

# Clase mágica que redirige los "print" de la consola a nuestra GUI
class EmittingStream(QObject):
    textWritten = pyqtSignal(str)
    def write(self, text):
        self.textWritten.emit(str(text))
    def flush(self):
        pass

# Hilo secundario para que la interfaz no se congele durante la extracción
class ExtractionWorker(QThread):
    finished = pyqtSignal()
    
    def __init__(self, tipo_extraccion, ruta):
        super().__init__()
        self.tipo_extraccion = tipo_extraccion
        self.ruta = ruta

    def run(self):
        try:
            if self.tipo_extraccion == 'acsl':
                generar_diccionario_json(self.ruta)
            elif self.tipo_extraccion == 'slus':
                extraer_textos_elf(self.ruta)
        except Exception as e:
            print(f"\n[ERROR CRÍTICO]: {e}")
        finally:
            self.finished.emit()

class TabExtractor(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

        # Redirigir stdout (los prints) a nuestra caja de texto
        self.stream = EmittingStream()
        self.stream.textWritten.connect(self.escribir_log)
        sys.stdout = self.stream

    def init_ui(self):
        layout_principal = QVBoxLayout()

        # --- GRUPO 1: Extractor de .DATs ---
        grupo_dat = QGroupBox("1. Extracción de Contenedores (.DAT)")
        layout_dat = QHBoxLayout()
        
        self.txt_ruta_dat = QLineEdit()
        self.txt_ruta_dat.setReadOnly(True)
        self.txt_ruta_dat.setPlaceholderText("Selecciona la carpeta 'dats'...")
        
        btn_buscar_dat = QPushButton("Examinar Carpeta")
        btn_buscar_dat.clicked.connect(self.seleccionar_carpeta_dat)
        
        self.btn_extraer_dat = QPushButton("▶ Extraer Textos (.DAT)")
        self.btn_extraer_dat.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        self.btn_extraer_dat.clicked.connect(self.iniciar_extraccion_dat)

        layout_dat.addWidget(self.txt_ruta_dat)
        layout_dat.addWidget(btn_buscar_dat)
        layout_dat.addWidget(self.btn_extraer_dat)
        grupo_dat.setLayout(layout_dat)

        # --- GRUPO 2: Extractor del Ejecutable (SLUS) ---
        grupo_slus = QGroupBox("2. Extracción del Ejecutable (ELF / SLUS)")
        layout_slus = QHBoxLayout()
        
        self.txt_ruta_slus = QLineEdit()
        self.txt_ruta_slus.setReadOnly(True)
        self.txt_ruta_slus.setPlaceholderText("Selecciona el archivo SLUS_206.44...")
        
        btn_buscar_slus = QPushButton("Examinar Archivo")
        btn_buscar_slus.clicked.connect(self.seleccionar_archivo_slus)
        
        self.btn_extraer_slus = QPushButton("▶ Extraer Textos (SLUS)")
        self.btn_extraer_slus.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
        self.btn_extraer_slus.clicked.connect(self.iniciar_extraccion_slus)

        layout_slus.addWidget(self.txt_ruta_slus)
        layout_slus.addWidget(btn_buscar_slus)
        layout_slus.addWidget(self.btn_extraer_slus)
        grupo_slus.setLayout(layout_slus)

        # --- CONSOLA DE REGISTROS (LOG) ---
        self.consola = QTextEdit()
        self.consola.setReadOnly(True)
        self.consola.setStyleSheet("background-color: #1e1e1e; color: #4CAF50; font-family: Consolas;")

        layout_principal.addWidget(grupo_dat)
        layout_principal.addWidget(grupo_slus)
        layout_principal.addWidget(QLabel("Registro de Actividad (Log):"))
        layout_principal.addWidget(self.consola)

        self.setLayout(layout_principal)

    def escribir_log(self, texto):
        # Inserta el texto en la consola y hace scroll hacia abajo
        self.consola.insertPlainText(texto)
        self.consola.ensureCursorVisible()

    def seleccionar_carpeta_dat(self):
        carpeta = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta con los .dat")
        if carpeta:
            self.txt_ruta_dat.setText(carpeta)

    def seleccionar_archivo_slus(self):
        archivo, _ = QFileDialog.getOpenFileName(self, "Seleccionar ejecutable SLUS", "", "Archivos ejecutables (*.44 *.ELF);;Todos los archivos (*)")
        if archivo:
            self.txt_ruta_slus.setText(archivo)

    def iniciar_extraccion_dat(self):
        ruta = self.txt_ruta_dat.text()
        if not ruta:
            print("Por favor selecciona la carpeta de los .dat primero.\n")
            return
        self.ejecutar_hilo('acsl', ruta, self.btn_extraer_dat)

    def iniciar_extraccion_slus(self):
        ruta = self.txt_ruta_slus.text()
        if not ruta:
            print("Por favor selecciona el archivo SLUS primero.\n")
            return
        self.ejecutar_hilo('slus', ruta, self.btn_extraer_slus)

    def ejecutar_hilo(self, tipo, ruta, boton):
        # Deshabilitamos el botón para evitar doble clic
        boton.setEnabled(False)
        self.consola.clear()
        
        self.worker = ExtractionWorker(tipo, ruta)
        self.worker.finished.connect(lambda: boton.setEnabled(True))
        self.worker.start()