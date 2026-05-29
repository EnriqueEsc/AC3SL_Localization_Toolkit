import os
import json
import re
import subprocess
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QTextEdit, QFileDialog, QGroupBox, QMessageBox)
from PyQt5.QtCore import QThread, pyqtSignal, QObject

class EmittingStream(QObject):
    textWritten = pyqtSignal(str)
    def write(self, text):
        self.textWritten.emit(str(text))
    def flush(self):
        pass

class WorkerCompilador(QThread):
    finished = pyqtSignal()
    
    def __init__(self, rutas, char_map, simplificar_acentos):
        super().__init__()
        self.rutas = rutas
        self.char_map = char_map
        self.simplificar_acentos = simplificar_acentos
        self.patron_texto = re.compile(b'((?:[\x20-\x7E\x0A\x0D]|[\x81-\x9F\xE0-\xEF][\x40-\x7E\x80-\xFC]){4,})(\x00*)')

    def decodificar_bloque(self, bloque_bytes):
        texto = ""
        i = 0
        while i < len(bloque_bytes):
            b = bloque_bytes[i]
            if b in (10, 13):
                texto += '\\n' if b == 10 else ''
                i += 1
            elif 32 <= b <= 126:
                texto += chr(b)
                i += 1
            elif (0x81 <= b <= 0x9F or 0xE0 <= b <= 0xEF) and i + 1 < len(bloque_bytes):
                try:
                    texto += bloque_bytes[i:i+2].decode('shift_jis')
                except:
                    texto += f"[{b:02X}{bloque_bytes[i+1]:02X}]"
                i += 2
            else:
                texto += f"[{b:02X}]"
                i += 1
        return texto

    def preparar_bytes_inyeccion(self, traduccion, max_bytes_bloque):
        trad_mod = traduccion

        # 0. Simplificación de acentos (Si está activado en Preferencias)
        if self.simplificar_acentos:
            trad_mod = trad_mod.translate(str.maketrans('áéíóúÁÉÍÓÚäëïöüÄËÏÖÜ', 'aeiouAEIOUaeiouAEIOU'))

        # 1. Reemplazo de caracteres especiales in-game dinámico basado en config
        for char_real, char_juego in self.char_map.items():
            trad_mod = trad_mod.replace(char_real, char_juego)
        
        # 2. Conversión de saltos de línea visuales (\n) a bytes reales (0x0A)
        trad_mod = trad_mod.replace('\\n', '\n')
        
        # 3. Codificación a Shift-JIS
        trad_bytes = trad_mod.encode('shift_jis', errors='ignore')
        
        # 4. Truncado de emergencia y Relleno
        limite = max_bytes_bloque - 1 
        if len(trad_bytes) > limite:
            trad_bytes = trad_bytes[:limite]
            
        padding = max_bytes_bloque - len(trad_bytes)
        return trad_bytes + (b'\x00' * padding)

    def procesar_archivo(self, ruta_origen, ruta_destino, plantilla):
        with open(ruta_origen, 'rb') as f:
            datos = f.read()

        nuevo_archivo = bytearray()
        ultimo_indice = 0
        reemplazos = 0

        for match in self.patron_texto.finditer(datos):
            bloque_texto = match.group(1)
            bloque_ceros = match.group(2)
            texto_original = self.decodificar_bloque(bloque_texto)
            
            nuevo_archivo.extend(datos[ultimo_indice:match.start()])
            
            if texto_original in plantilla and plantilla[texto_original].get("traduccion", "").strip():
                trad = plantilla[texto_original]["traduccion"]
                espacio_disponible = len(bloque_texto) + len(bloque_ceros)
                
                bytes_inyectados = self.preparar_bytes_inyeccion(trad, espacio_disponible)
                nuevo_archivo.extend(bytes_inyectados)
                reemplazos += 1
            else:
                nuevo_archivo.extend(match.group(0))
                
            ultimo_indice = match.end()

        nuevo_archivo.extend(datos[ultimo_indice:])
        
        with open(ruta_destino, 'wb') as f:
            f.write(nuevo_archivo)
            
        return reemplazos

    def run(self):
        try:
            print("=== INICIANDO COMPILACIÓN ===")
            
            # 1. Cargar Plantilla
            ruta_plantilla = os.path.join("translation", "Plantilla_Maestra.json")
            if not os.path.exists(ruta_plantilla):
                print(f"ERROR: No se encontró la plantilla en {ruta_plantilla}")
                return
            with open(ruta_plantilla, 'r', encoding='utf-8') as f:
                plantilla = json.load(f)
            
            # 2. Preparar directorios de salida
            ruta_build_dats = os.path.join("build", "dats")
            os.makedirs(ruta_build_dats, exist_ok=True)
            os.makedirs(os.path.join("build", "slus"), exist_ok=True)
            
            # 3. Procesar DATs
            ruta_dats = self.rutas.get('dats')
            if ruta_dats and os.path.exists(ruta_dats):
                print("\n[1/3] Inyectando traducciones en archivos .DAT...")
                archivos = [f for f in os.listdir(ruta_dats) if f.endswith('.dat')]
                total_modificados = 0
                for f in archivos:
                    reemplazos = self.procesar_archivo(
                        os.path.join(ruta_dats, f),
                        os.path.join(ruta_build_dats, f),
                        plantilla
                    )
                    if reemplazos > 0:
                        total_modificados += 1
                print(f"-> {total_modificados} archivos .DAT modificados exitosamente.")
            
            # 4. Procesar SLUS
            ruta_slus = self.rutas.get('slus')
            if ruta_slus and os.path.exists(ruta_slus):
                print("\n[2/3] Inyectando traducciones en el Ejecutable (SLUS)...")
                nombre_slus = os.path.basename(ruta_slus)
                ruta_slus_out = os.path.join("build", "slus", nombre_slus)
                reemplazos = self.procesar_archivo(ruta_slus, ruta_slus_out, plantilla)
                print(f"-> Se reescribieron {reemplazos} cadenas en el ejecutable.")
            
            # 5. Reconstruir BIN con QuickBMS
            print("\n[3/3] Reconstruyendo AC3DATA.BIN con QuickBMS...")
            qbms_exe = self.rutas.get('qbms_exe')
            qbms_script = self.rutas.get('qbms_script')
            ruta_bin = self.rutas.get('bin')
            
            if all([qbms_exe, qbms_script, ruta_bin]):
                comando = [qbms_exe, "-w", "-r", qbms_script, ruta_bin, ruta_build_dats]
                print(f"Ejecutando: {' '.join(comando)}")
                
                proceso = subprocess.Popen(comando, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                for linea in proceso.stdout:
                    print(linea.strip())
                proceso.wait()
                
                if proceso.returncode == 0:
                    print("\n=== COMPILACIÓN EXITOSA ===")
                    print("El archivo AC3DATA.BIN ha sido actualizado con tus traducciones.")
                    print("¡Listo para empaquetar en la ISO!")
                else:
                    print(f"\nERROR: QuickBMS terminó con código {proceso.returncode}")
            else:
                print("\nSaltando reconstrucción de BIN (Faltan rutas de QuickBMS en la configuración).")
                print("=== INYECCIÓN EXITOSA EN CARPETA 'BUILD' ===")

        except Exception as e:
            print(f"\n[ERROR CRÍTICO]: {e}")
        finally:
            self.finished.emit()


class TabCompilador(QWidget):
    def __init__(self):
        super().__init__()
        self.ruta_config = "config_toolkit.json"
        self.config = self.cargar_configuracion()
        self.inicializar_diccionario_caracteres()
        
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
            print(f"Error guardando config: {e}")

    def inicializar_diccionario_caracteres(self):
        if 'char_map' not in self.config:
            self.config['char_map'] = {
                "ñ": "@",
                "Ñ": "*",
                "¿": "&",
                "¡": "_"
            }
            self.guardar_configuracion()

    # ==========================================
    # ACTUALIZACIÓN AUTOMÁTICA DE PREFERENCIAS
    # ==========================================
    def showEvent(self, event):
        """Se ejecuta automáticamente cada que la pestaña se vuelve visible."""
        super().showEvent(event)
        self.config = self.cargar_configuracion()
        
        # Sincronizamos los cuadros de texto con las preferencias frescas
        if 'dats' in self.config and self.config['dats']:
            self.txt_dats.setText(self.config['dats'])
        if 'slus' in self.config and self.config['slus']:
            self.txt_slus.setText(self.config['slus'])
        if 'qbms_exe' in self.config and self.config['qbms_exe']:
            self.txt_exe.setText(self.config['qbms_exe'])
        if 'qbms_script' in self.config and self.config['qbms_script']:
            self.txt_script.setText(self.config['qbms_script'])
        if 'bin' in self.config and self.config['bin']:
            self.txt_bin.setText(self.config['bin'])

    def init_ui(self):
        layout_principal = QVBoxLayout()
        layout_principal.setSpacing(15)

        # Grupo 1: Archivos Originales (Autocompletado desde Config)
        grupo_origen = QGroupBox("1. Archivos Originales del Juego")
        layout_origen = QVBoxLayout()
        
        l_dats = QHBoxLayout()
        self.txt_dats = QLineEdit()
        self.txt_dats.setReadOnly(True)
        self.txt_dats.setText(self.config.get('dats', ''))
        self.txt_dats.setPlaceholderText("Carpeta con los archivos DAT extraídos...")
        
        btn_dats = QPushButton("Examinar Carpeta")
        btn_dats.clicked.connect(lambda: self.seleccionar_ruta(self.txt_dats, 'dats', True))
        l_dats.addWidget(self.txt_dats)
        l_dats.addWidget(btn_dats)
        
        l_slus = QHBoxLayout()
        self.txt_slus = QLineEdit()
        self.txt_slus.setReadOnly(True)
        self.txt_slus.setText(self.config.get('slus', ''))
        self.txt_slus.setPlaceholderText("Ruta del ejecutable original SLUS_206.44...")
        
        btn_slus = QPushButton("Examinar Archivo")
        btn_slus.clicked.connect(lambda: self.seleccionar_ruta(self.txt_slus, 'slus', False, "Ejecutables (*.44 *.ELF)"))
        l_slus.addWidget(self.txt_slus)
        l_slus.addWidget(btn_slus)

        layout_origen.addLayout(l_dats)
        layout_origen.addLayout(l_slus)
        grupo_origen.setLayout(layout_origen)

        # Grupo 2: Herramientas QuickBMS (Autocompletado desde Config)
        grupo_qbms = QGroupBox("2. Configuración de Reconstrucción (QuickBMS)")
        layout_qbms = QVBoxLayout()
        
        l_exe = QHBoxLayout()
        self.txt_exe = QLineEdit()
        self.txt_exe.setReadOnly(True)
        self.txt_exe.setText(self.config.get('qbms_exe', ''))
        self.txt_exe.setPlaceholderText("Ruta a quickbms.exe...")
        
        btn_exe = QPushButton("Examinar .exe")
        btn_exe.clicked.connect(lambda: self.seleccionar_ruta(self.txt_exe, 'qbms_exe', False, "Ejecutables (*.exe)"))
        l_exe.addWidget(self.txt_exe)
        l_exe.addWidget(btn_exe)
        
        l_script = QHBoxLayout()
        self.txt_script = QLineEdit()
        self.txt_script.setReadOnly(True)
        self.txt_script.setText(self.config.get('qbms_script', ''))
        self.txt_script.setPlaceholderText("Ruta al script de extracción (.bms)...")
        
        btn_script = QPushButton("Examinar .bms")
        btn_script.clicked.connect(lambda: self.seleccionar_ruta(self.txt_script, 'qbms_script', False, "Scripts (*.bms)"))
        l_script.addWidget(self.txt_script)
        l_script.addWidget(btn_script)
        
        l_bin = QHBoxLayout()
        self.txt_bin = QLineEdit()
        self.txt_bin.setReadOnly(True)
        self.txt_bin.setText(self.config.get('bin', ''))
        self.txt_bin.setPlaceholderText("Ruta a tu copia de AC3DATA.BIN (Copia de respaldo)...")
        
        btn_bin = QPushButton("Examinar BIN")
        btn_bin.clicked.connect(lambda: self.seleccionar_ruta(self.txt_bin, 'bin', False, "Archivos BIN (*.BIN *.bin)"))
        l_bin.addWidget(self.txt_bin)
        l_bin.addWidget(btn_bin)

        layout_qbms.addLayout(l_exe)
        layout_qbms.addLayout(l_script)
        layout_qbms.addLayout(l_bin)
        grupo_qbms.setLayout(layout_qbms)

        # Log y Botón de Acción
        self.consola = QTextEdit()
        self.consola.setReadOnly(True)
        self.consola.setStyleSheet("background-color: #121212; color: #4CAF50; font-family: 'Consolas', monospace; font-size: 13px; border: 1px solid #444444;")

        self.btn_compilar = QPushButton("⚙️ INYECTAR Y COMPILAR ISO")
        self.btn_compilar.setMinimumHeight(50)
        self.btn_compilar.setStyleSheet("""
            QPushButton { background-color: #E91E63; color: white; font-weight: bold; border-radius: 4px; font-size: 16px; }
            QPushButton:hover { background-color: #D81B60; }
            QPushButton:disabled { background-color: #555555; color: #888888; }
        """)
        self.btn_compilar.clicked.connect(self.iniciar_compilacion)

        layout_principal.addWidget(grupo_origen)
        layout_principal.addWidget(grupo_qbms)
        layout_principal.addWidget(self.btn_compilar)
        layout_principal.addWidget(QLabel("Registro de Compilación (Log):"))
        layout_principal.addWidget(self.consola)

        self.setLayout(layout_principal)

    def escribir_log(self, texto):
        self.consola.insertPlainText(texto + "\n" if not texto.endswith("\n") else texto)
        self.consola.ensureCursorVisible()

    def seleccionar_ruta(self, line_edit, clave_config, es_carpeta, filtro="Todos (*.*)"):
        dir_inicial = os.path.dirname(line_edit.text()) if line_edit.text() else ""
        
        if es_carpeta:
            ruta = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta", dir_inicial)
        else:
            ruta, _ = QFileDialog.getOpenFileName(self, "Seleccionar Archivo", dir_inicial, filtro)
        
        if ruta:
            ruta_abs = os.path.abspath(ruta)
            line_edit.setText(ruta_abs)
            self.config[clave_config] = ruta_abs
            self.guardar_configuracion()

    def iniciar_compilacion(self):
        if not self.config.get('dats') and not self.config.get('slus'):
            QMessageBox.warning(self, "Faltan rutas", "Debes configurar al menos la ruta de los DATs o el SLUS para inyectar traducciones.")
            return

        import sys
        sys.stdout = self.stream
        
        self.btn_compilar.setEnabled(False)
        self.consola.clear()
        
        # Leemos el estado del simplificador de acentos desde la configuración
        simplificar = self.config.get('simplificar_acentos', True)
        
        # Instanciamos el worker con el nuevo parámetro
        self.worker = WorkerCompilador(self.config, self.config.get('char_map', {}), simplificar)
        self.worker.finished.connect(self.finalizar_compilacion)
        self.worker.start()

    def finalizar_compilacion(self):
        import sys
        sys.stdout = sys.__stdout__ 
        self.btn_compilar.setEnabled(True)