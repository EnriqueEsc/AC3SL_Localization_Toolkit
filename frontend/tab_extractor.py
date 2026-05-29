import sys
import os
import json
import subprocess
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QTextEdit, QFileDialog, 
                             QGroupBox, QMessageBox)
from PyQt5.QtCore import QThread, pyqtSignal, QObject

from backend.acsl_extractor import generar_diccionario_json
from backend.slus_extractor import extraer_textos_elf

class EmittingStream(QObject):
    textWritten = pyqtSignal(str)
    def write(self, text):
        self.textWritten.emit(str(text))
    def flush(self):
        pass

class ExtractionWorker(QThread):
    finished = pyqtSignal()
    
    def __init__(self, tipo_extraccion, ruta, extras=None):
        super().__init__()
        self.tipo_extraccion = tipo_extraccion
        self.ruta = ruta
        self.extras = extras or {}

    def run(self):
        try:
            if self.tipo_extraccion == 'acsl':
                generar_diccionario_json(self.ruta)
            elif self.tipo_extraccion == 'slus':
                extraer_textos_elf(self.ruta)
            elif self.tipo_extraccion == 'bin_qbms':
                print("=== INICIANDO EXTRACCIÓN DE BIN CON QUICKBMS ===")
                qbms_exe = self.extras.get('qbms_exe')
                qbms_script = self.extras.get('qbms_script')
                ruta_bin = self.extras.get('bin')
                carpeta_salida = self.ruta
                
                # Agregamos el argumento "-o" (overwrite) para que sobreescriba sin preguntar
                # Esto evita el bloqueo infinito (hang) del proceso en segundo plano
                comando = [qbms_exe, "-o", qbms_script, ruta_bin, carpeta_salida]
                print(f"Ejecutando: {' '.join(comando)}\n")
                
                proceso = subprocess.Popen(comando, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                for linea in proceso.stdout:
                    print(linea.strip())
                proceso.wait()
                
                if proceso.returncode == 0:
                    print("\n=== EXTRACCIÓN DE BIN COMPLETADA CON ÉXITO ===")
                else:
                    print(f"\nERROR: QuickBMS terminó con código de salida {proceso.returncode}")
        except Exception as e:
            print(f"\n[ERROR CRÍTICO EN HILO]: {e}")
        finally:
            self.finished.emit()


class TabExtractor(QWidget):
    def __init__(self):
        super().__init__()
        self.ruta_config = "config_toolkit.json"
        self.config = self.cargar_configuracion()
        
        self.init_ui()
        self.stream = EmittingStream()
        self.stream.textWritten.connect(self.escribir_log)

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
            print(f"No se pudo guardar la configuración: {e}")

    def showEvent(self, event):
        """Sincroniza la UI si las preferencias se modificaron en otra pestaña."""
        super().showEvent(event)
        self.config = self.cargar_configuracion()
        
        if 'bin' in self.config and self.config['bin']:
            self.txt_ruta_bin.setText(self.config['bin'])
        if 'dats' in self.config and self.config['dats']:
            self.txt_ruta_dat.setText(self.config['dats'])
        if 'slus' in self.config and self.config['slus']:
            self.txt_ruta_slus.setText(self.config['slus'])

    def init_ui(self):
        layout_principal = QVBoxLayout()
        layout_principal.setSpacing(15)

        # ==========================================
        # GRUPO 0: Desempaquetado (Ahora balanceado visualmente)
        # ==========================================
        grupo_bin = QGroupBox("0. Desempaquetado de Archivo ISO / BIN")
        layout_bin = QHBoxLayout()
        
        self.txt_ruta_bin = QLineEdit()
        self.txt_ruta_bin.setReadOnly(True)
        self.txt_ruta_bin.setPlaceholderText("Selecciona el archivo AC3DATA.BIN original...")
        if self.config.get('bin') and os.path.exists(self.config['bin']):
            self.txt_ruta_bin.setText(self.config['bin'])
            
        btn_buscar_bin = QPushButton("Examinar Archivo")
        btn_buscar_bin.clicked.connect(self.seleccionar_archivo_bin)
        
        self.btn_extraer_bin = QPushButton("▶ Desempaquetar (BIN)")
        self.btn_extraer_bin.setStyleSheet("""
            QPushButton { background-color: #388E3C; color: white; font-weight: bold; border-radius: 4px; padding: 5px 15px; }
            QPushButton:hover { background-color: #43A047; }
            QPushButton:disabled { background-color: #555555; color: #888888; }
        """)
        self.btn_extraer_bin.clicked.connect(self.iniciar_extraccion_bin)
        
        layout_bin.addWidget(self.txt_ruta_bin)
        layout_bin.addWidget(btn_buscar_bin)
        layout_bin.addWidget(self.btn_extraer_bin)
        grupo_bin.setLayout(layout_bin)

        # ==========================================
        # GRUPO 1: Extractor DAT
        # ==========================================
        grupo_dat = QGroupBox("1. Extracción de Textos de Contenedores (.DAT)")
        layout_dat = QHBoxLayout()
        
        self.txt_ruta_dat = QLineEdit()
        self.txt_ruta_dat.setReadOnly(True)
        self.txt_ruta_dat.setPlaceholderText("Selecciona la carpeta donde se extrajeron los .dat...")
        
        ruta_defecto_dat = self.config.get('dats', os.path.abspath(os.path.join("data", "dats")))
        if os.path.exists(ruta_defecto_dat):
            self.txt_ruta_dat.setText(ruta_defecto_dat)
        
        btn_buscar_dat = QPushButton("Examinar Carpeta")
        btn_buscar_dat.clicked.connect(self.seleccionar_carpeta_dat)
        
        self.btn_extraer_dat = QPushButton("▶ Extraer Textos (.DAT)")
        self.btn_extraer_dat.setStyleSheet("""
            QPushButton { background-color: #1976D2; color: white; font-weight: bold; border-radius: 4px; padding: 5px 15px; }
            QPushButton:hover { background-color: #1E88E5; }
            QPushButton:disabled { background-color: #555555; color: #888888; }
        """)
        self.btn_extraer_dat.clicked.connect(self.iniciar_extraccion_dat)

        layout_dat.addWidget(self.txt_ruta_dat)
        layout_dat.addWidget(btn_buscar_dat)
        layout_dat.addWidget(self.btn_extraer_dat)
        grupo_dat.setLayout(layout_dat)

        # ==========================================
        # GRUPO 2: Extractor SLUS
        # ==========================================
        grupo_slus = QGroupBox("2. Extracción de Textos del Ejecutable (ELF / SLUS)")
        layout_slus = QHBoxLayout()
        
        self.txt_ruta_slus = QLineEdit()
        self.txt_ruta_slus.setReadOnly(True)
        self.txt_ruta_slus.setPlaceholderText("Selecciona el archivo ejecutable original SLUS_206.44...")
        
        if self.config.get('slus') and os.path.exists(self.config['slus']):
            self.txt_ruta_slus.setText(self.config['slus'])
        
        btn_buscar_slus = QPushButton("Examinar Archivo")
        btn_buscar_slus.clicked.connect(self.seleccionar_archivo_slus)
        
        self.btn_extraer_slus = QPushButton("▶ Extraer Textos (SLUS)")
        self.btn_extraer_slus.setStyleSheet("""
            QPushButton { background-color: #F57C00; color: white; font-weight: bold; border-radius: 4px; padding: 5px 15px; }
            QPushButton:hover { background-color: #FB8C00; }
            QPushButton:disabled { background-color: #555555; color: #888888; }
        """)
        self.btn_extraer_slus.clicked.connect(self.iniciar_extraccion_slus)

        layout_slus.addWidget(self.txt_ruta_slus)
        layout_slus.addWidget(btn_buscar_slus)
        layout_slus.addWidget(self.btn_extraer_slus)
        grupo_slus.setLayout(layout_slus)

        # LOG
        self.consola = QTextEdit()
        self.consola.setReadOnly(True)
        self.consola.setStyleSheet("background-color: #121212; color: #4CAF50; font-family: 'Consolas', monospace; font-size: 13px; border: 1px solid #444444;")

        layout_principal.addWidget(grupo_bin)
        layout_principal.addWidget(grupo_dat)
        layout_principal.addWidget(grupo_slus)
        layout_principal.addWidget(QLabel("Registro de Actividad (Log):"))
        layout_principal.addWidget(self.consola)

        self.setLayout(layout_principal)

    def escribir_log(self, texto):
        self.consola.insertPlainText(texto)
        self.consola.ensureCursorVisible()

    def verificar_y_solicitar_rutas_qbms(self):
        # Ahora solo verificamos el exe y el script, porque el .BIN ya tiene su propio campo visible
        if not self.config.get('qbms_exe') or not os.path.exists(self.config['qbms_exe']):
            QMessageBox.information(self, "Configuración requerida", "No se ha detectado 'quickbms.exe'. Por favor selecciónalo a continuación.")
            ruta, _ = QFileDialog.getOpenFileName(self, "Seleccionar quickbms.exe", "", "Ejecutables (*.exe)")
            if not ruta: return False
            self.config['qbms_exe'] = os.path.abspath(ruta)
            self.guardar_configuracion()

        if not self.config.get('qbms_script') or not os.path.exists(self.config['qbms_script']):
            ruta_por_defecto = os.path.abspath(os.path.join("scripts_quickbms", "silent_line.bms"))
            if os.path.exists(ruta_por_defecto):
                self.config['qbms_script'] = ruta_por_defecto
            else:
                QMessageBox.information(self, "Configuración requerida", "No se detectó el script BMS. Por favor selecciónalo.")
                ruta, _ = QFileDialog.getOpenFileName(self, "Seleccionar script .bms", "", "Scripts (*.bms)")
                if not ruta: return False
                self.config['qbms_script'] = os.path.abspath(ruta)
            self.guardar_configuracion()

        return True

    def seleccionar_archivo_bin(self):
        archivo, _ = QFileDialog.getOpenFileName(self, "Seleccionar AC3DATA.BIN", "", "Archivos BIN (*.BIN *.bin);;Todos los archivos (*)")
        if archivo:
            ruta_abs = os.path.abspath(archivo)
            self.txt_ruta_bin.setText(ruta_abs)
            self.config['bin'] = ruta_abs
            self.guardar_configuracion()

    def seleccionar_carpeta_dat(self):
        carpeta = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta con los archivos .dat")
        if carpeta:
            ruta_abs = os.path.abspath(carpeta)
            self.txt_ruta_dat.setText(ruta_abs)
            self.config['dats'] = ruta_abs
            self.guardar_configuracion()

    def seleccionar_archivo_slus(self):
        archivo, _ = QFileDialog.getOpenFileName(self, "Seleccionar ejecutable SLUS", "", "Archivos ejecutables (*.44 *.ELF);;Todos los archivos (*)")
        if archivo:
            ruta_abs = os.path.abspath(archivo)
            self.txt_ruta_slus.setText(ruta_abs)
            self.config['slus'] = ruta_abs
            self.guardar_configuracion()

    def iniciar_extraccion_bin(self):
        ruta_bin = self.txt_ruta_bin.text()
        if not ruta_bin or not os.path.exists(ruta_bin):
            QMessageBox.warning(self, "Ruta inválida", "Por favor, selecciona tu archivo AC3DATA.BIN original primero.")
            return
            
        if not self.verificar_y_solicitar_rutas_qbms():
            return
            
        carpeta_salida = self.txt_ruta_dat.text()
        if not carpeta_salida:
            carpeta_salida = os.path.abspath(os.path.join("data", "dats"))
            os.makedirs(carpeta_salida, exist_ok=True)
            self.txt_ruta_dat.setText(carpeta_salida)
            self.config['dats'] = carpeta_salida
            self.guardar_configuracion()

        extras = {
            'qbms_exe': self.config['qbms_exe'],
            'qbms_script': self.config['qbms_script'],
            'bin': ruta_bin
        }
        self.ejecutar_hilo('bin_qbms', carpeta_salida, self.btn_extraer_bin, extras)

    def iniciar_extraccion_dat(self):
        ruta = self.txt_ruta_dat.text()
        if not ruta or not os.path.exists(ruta):
            QMessageBox.warning(self, "Ruta inválida", "Por favor, selecciona una carpeta de archivos .DAT válida primero.")
            return
        self.ejecutar_hilo('acsl', ruta, self.btn_extraer_dat)

    def iniciar_extraccion_slus(self):
        ruta = self.txt_ruta_slus.text()
        if not ruta or not os.path.exists(ruta):
            QMessageBox.warning(self, "Archivo no encontrado", "Por favor, selecciona el archivo del ejecutable (SLUS) original.")
            return
        self.ejecutar_hilo('slus', ruta, self.btn_extraer_slus)

    def ejecutar_hilo(self, tipo, ruta, boton, extras=None):
        boton.setEnabled(False)
        self.consola.clear()
        
        sys.stdout = self.stream
        
        self.worker = ExtractionWorker(tipo, ruta, extras)
        self.worker.finished.connect(lambda: self.finalizar_hilo(boton))
        self.worker.start()

    def finalizar_hilo(self, boton):
        sys.stdout = sys.__stdout__
        boton.setEnabled(True)