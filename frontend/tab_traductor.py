import os
import json
import re
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, 
                             QListWidget, QLineEdit, QLabel, QCheckBox,
                             QPushButton, QMessageBox, QProgressBar, QPlainTextEdit, 
                             QTextEdit, QSplitter, QGroupBox, QFileDialog)
from PyQt5.QtCore import Qt

class TabTraductor(QWidget):
    def __init__(self):
        super().__init__()
        self.ruta_config = "config_toolkit.json"
        self.config = self.cargar_configuracion()
        
        self.plantilla = {}
        self.archivo_plantilla = None
        self.llave_actual = None
        
        self.init_ui()

    def cargar_configuracion(self):
        if os.path.exists(self.ruta_config):
            try:
                with open(self.ruta_config, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def showEvent(self, event):
        """Sincroniza las preferencias globales cada vez que se abre la pestaña."""
        super().showEvent(event)
        self.config = self.cargar_configuracion()
        
        simplificar = self.config.get('simplificar_acentos', True)
        if simplificar:
            self.lbl_ayuda_trad.setText("Tu Traducción (ñ, ¿, ¡ permitidos. Acentos se simplifican auto):")
        else:
            self.lbl_ayuda_trad.setText("Tu Traducción (Acentos permitidos según tu mapeo):")

    def init_ui(self):
        layout_principal = QHBoxLayout()

        # ==========================================
        # PANEL IZQUIERDO: Lista de Textos
        # ==========================================
        grupo_izquierdo = QGroupBox("1. Explorador de Plantilla")
        panel_izquierdo = QVBoxLayout()

        self.btn_cargar = QPushButton("📂 Cargar Plantilla JSON")
        self.btn_cargar.setStyleSheet("""
            QPushButton { background-color: #455A64; color: white; font-weight: bold; border-radius: 4px; padding: 8px; }
            QPushButton:hover { background-color: #546E7A; }
        """)
        self.btn_cargar.clicked.connect(self.cargar_plantilla)

        layout_busqueda = QHBoxLayout()
        self.barra_busqueda = QLineEdit()
        # -> CAMBIO: Instrucción visual para el usuario
        self.barra_busqueda.setPlaceholderText("🔍 Buscar original o traducción... (Presiona Enter)")
        # -> CAMBIO: Reemplazamos textChanged por returnPressed
        self.barra_busqueda.returnPressed.connect(self.filtrar_lista)
        
        self.chk_pendientes = QCheckBox("Mostrar solo pendientes")
        self.chk_pendientes.setStyleSheet("color: #dddddd; font-size: 13px;")
        self.chk_pendientes.stateChanged.connect(self.filtrar_lista)

        layout_busqueda.addWidget(self.barra_busqueda)
        layout_busqueda.addWidget(self.chk_pendientes)

        self.lista_textos = QListWidget()
        self.lista_textos.setUniformItemSizes(True)
        self.lista_textos.currentItemChanged.connect(self.cargar_traduccion)

        panel_izquierdo.addWidget(self.btn_cargar)
        panel_izquierdo.addSpacing(10)
        panel_izquierdo.addWidget(QLabel("Textos a Traducir:"))
        panel_izquierdo.addLayout(layout_busqueda)
        panel_izquierdo.addWidget(self.lista_textos)
        grupo_izquierdo.setLayout(panel_izquierdo)

        # ==========================================
        # PANEL DERECHO: Dos Columnas de Edición
        # ==========================================
        grupo_derecho = QGroupBox("2. Área de Trabajo y Previsualización")
        panel_derecho = QVBoxLayout()
        
        splitter_columnas = QSplitter(Qt.Horizontal)

        # --- COLUMNA 1: ORIGINAL ---
        widget_orig = QWidget()
        layout_orig = QVBoxLayout(widget_orig)
        layout_orig.setContentsMargins(0, 0, 10, 0)

        layout_orig.addWidget(QLabel("Texto Original (Crudo):"))
        self.txt_original = QPlainTextEdit()
        self.txt_original.setReadOnly(True)
        self.txt_original.setStyleSheet("background-color: #2a2a2a; color: #aaaaaa; border: 1px solid #444444; border-radius: 4px; font-family: Consolas; font-size: 14px;")
        layout_orig.addWidget(self.txt_original)

        layout_orig.addWidget(QLabel("Vista Previa (Original):"))
        self.preview_orig = QTextEdit()
        self.preview_orig.setReadOnly(True)
        self.preview_orig.setStyleSheet("background-color: #0a0a0a; border: 1px solid #444444; border-radius: 4px; font-family: Arial; font-size: 16px; padding: 5px;")
        layout_orig.addWidget(self.preview_orig)

        # --- COLUMNA 2: TRADUCCIÓN ---
        widget_trad = QWidget()
        layout_trad = QVBoxLayout(widget_trad)
        layout_trad.setContentsMargins(10, 0, 0, 0)

        self.lbl_ayuda_trad = QLabel("Tu Traducción (ñ, ¿, ¡ permitidos. Sin acentos):")
        layout_trad.addWidget(self.lbl_ayuda_trad)
        
        self.txt_traduccion = QPlainTextEdit()
        self.txt_traduccion.setStyleSheet("background-color: #121212; color: #ffffff; border: 2px solid #2196F3; border-radius: 4px; font-family: Consolas; font-size: 14px;")
        self.txt_traduccion.textChanged.connect(self.actualizar_preview_y_bytes)
        layout_trad.addWidget(self.txt_traduccion)

        self.lbl_bytes = QLabel("Bytes en la ISO: 0 / 0")
        self.lbl_bytes.setStyleSheet("font-weight: bold; font-size: 13px; color: #dddddd;")
        self.barra_bytes = QProgressBar()
        self.barra_bytes.setTextVisible(False)
        self.barra_bytes.setFixedHeight(12)
        layout_trad.addWidget(self.lbl_bytes)
        layout_trad.addWidget(self.barra_bytes)

        layout_trad.addSpacing(5)
        layout_trad.addWidget(QLabel("Vista Previa (Traducción):"))
        self.txt_preview = QTextEdit()
        self.txt_preview.setReadOnly(True)
        self.txt_preview.setStyleSheet("background-color: #0a0a0a; border: 1px solid #444444; border-radius: 4px; font-family: Arial; font-size: 16px; padding: 5px;")
        layout_trad.addWidget(self.txt_preview)

        splitter_columnas.addWidget(widget_orig)
        splitter_columnas.addWidget(widget_trad)
        panel_derecho.addWidget(splitter_columnas)

        # --- BOTONES DE ACCIÓN ---
        layout_botones = QHBoxLayout()
        self.btn_guardar = QPushButton("💾 Guardar Traducción")
        self.btn_guardar.setStyleSheet("""
            QPushButton { background-color: #388E3C; color: white; font-weight: bold; border-radius: 4px; padding: 10px; }
            QPushButton:hover { background-color: #43A047; }
        """)
        self.btn_guardar.clicked.connect(self.guardar_traduccion_actual)

        self.btn_siguiente = QPushButton("Siguiente ⏭")
        self.btn_siguiente.setStyleSheet("""
            QPushButton { background-color: #F57C00; color: white; font-weight: bold; border-radius: 4px; padding: 10px; }
            QPushButton:hover { background-color: #FB8C00; }
        """)
        self.btn_siguiente.clicked.connect(self.saltar_siguiente)

        layout_botones.addWidget(self.btn_guardar)
        layout_botones.addWidget(self.btn_siguiente)
        panel_derecho.addLayout(layout_botones)
        grupo_derecho.setLayout(panel_derecho)

        splitter_principal = QSplitter(Qt.Horizontal)
        splitter_principal.addWidget(grupo_izquierdo)
        splitter_principal.addWidget(grupo_derecho)
        splitter_principal.setSizes([300, 800]) 

        layout_principal.addWidget(splitter_principal)
        self.setLayout(layout_principal)

    def cargar_plantilla(self):
        dir_inicial = os.path.abspath("translation")
        os.makedirs(dir_inicial, exist_ok=True)
        
        ruta, _ = QFileDialog.getOpenFileName(self, "Seleccionar Archivo JSON de Traducción", dir_inicial, "JSON (*.json)")
        
        if not ruta:
            return 
            
        self.archivo_plantilla = ruta
        
        try:
            with open(self.archivo_plantilla, 'r', encoding='utf-8') as f:
                self.plantilla = json.load(f)

            self.poblar_lista()
            nombre_archivo = os.path.basename(self.archivo_plantilla)
            QMessageBox.information(self, "Éxito", f"Archivo cargado: '{nombre_archivo}'\nTotal de entradas: {len(self.plantilla)}.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el archivo:\n{e}")

    def poblar_lista(self):
        self.lista_textos.clear()
        self.lista_textos.setUpdatesEnabled(False)

        for original, datos in self.plantilla.items():
            trad = datos.get("traduccion", "")
            prefijo = "[✓] " if trad.strip() else "[ ] "
            mostrar = original[:40] + "..." if len(original) > 40 else original
            self.lista_textos.addItem(f"{prefijo}{mostrar}")

        self.lista_textos.setUpdatesEnabled(True)
        self.filtrar_lista()

    def filtrar_lista(self):
        busqueda = self.barra_busqueda.text().lower()
        solo_pendientes = self.chk_pendientes.isChecked()

        self.lista_textos.setUpdatesEnabled(False)
        for i in range(self.lista_textos.count()):
            item = self.lista_textos.item(i)
            llave_original = list(self.plantilla.keys())[i]
            datos = self.plantilla[llave_original]
            
            texto_trad = datos.get("traduccion", "").lower()
            texto_orig = llave_original.lower()
            
            es_pendiente = item.text().startswith("[ ]")
            
            if solo_pendientes and not es_pendiente:
                item.setHidden(True)
                continue

            if busqueda and busqueda not in texto_orig and busqueda not in texto_trad:
                item.setHidden(True)
                continue

            item.setHidden(False)
            
        self.lista_textos.setUpdatesEnabled(True)

    def cargar_traduccion(self, current, previous):
        if not current: return
        
        indice = self.lista_textos.row(current)
        self.llave_actual = list(self.plantilla.keys())[indice]
        datos = self.plantilla[self.llave_actual]

        self.txt_traduccion.blockSignals(True)
        
        self.txt_original.setPlainText(self.llave_actual)
        self.txt_traduccion.setPlainText(datos.get("traduccion", ""))
        
        tipo = datos.get("tipo", 2)
        
        # Bloquear el scroll de la vista previa original al cambiar de item (opcional pero recomendado)
        scrollbar_orig = self.preview_orig.verticalScrollBar()
        pos_orig = scrollbar_orig.value()
        self.preview_orig.setHtml(self.generar_html_preview(self.llave_actual, tipo))
        scrollbar_orig.setValue(pos_orig)
        
        self.txt_traduccion.blockSignals(False)
        self.actualizar_preview_y_bytes()

    def calcular_bytes_reales(self, texto):
        texto_procesado = texto.replace('\\n', '\n')
        return len(texto_procesado)

    def generar_html_preview(self, texto, tipo):
        preview = texto.replace('<', '&lt;').replace('>', '&gt;')
        
        if tipo == 4:
            preview = re.sub(r'(?i)&[xpg]\([^)]*\)', '', preview)
            preview = preview.replace('*', '').replace('/', '')
            
            tokens = re.split(r'(?i)(&c\(\d+\)|\\n|&lt;BR&gt;|\n)', preview)
            html_out = ""
            is_red = False
            
            for token in tokens:
                if not token: continue
                token_lower = token.lower()
                
                if re.match(r'(?i)&c\([1-9]\d*\)', token):
                    if not is_red:
                        html_out += '<span style="color: #FF5252; font-weight: bold;">'
                        is_red = True
                elif token_lower == '&c(0)':
                    if is_red:
                        html_out += '</span>'
                        is_red = False
                elif token_lower in ['\\n', '&lt;br&gt;', '\n']:
                    if is_red:
                        html_out += '</span><br><span style="color: #FF5252; font-weight: bold;">'
                    else:
                        html_out += '<br>'
                else:
                    html_out += token
            
            if is_red:
                html_out += '</span>'
                
            return f'<div style="color: #82B1FF;">{html_out}</div>'
        else:
            preview = preview.replace('\\n', '<br>').replace('&lt;BR&gt;', '<br>')
            return f'<div style="color: #FFFFFF;">{preview}</div>'

    def actualizar_preview_y_bytes(self):
        if not self.llave_actual: return

        texto = self.txt_traduccion.toPlainText()
        datos = self.plantilla[self.llave_actual]
        max_bytes = datos.get("max_bytes", 255)
        limite_bytes = max_bytes 
        tipo = datos.get("tipo", 2)

        texto_limpio = texto
        
        if self.config.get('simplificar_acentos', True):
            texto_limpio = texto_limpio.translate(str.maketrans('áéíóúÁÉÍÓÚäëïöüÄËÏÖÜ', 'aeiouAEIOUaeiouAEIOU'))
            
        if tipo == 1:
            texto_limpio = texto_limpio.upper()
            
        if texto != texto_limpio:
            self.txt_traduccion.blockSignals(True)
            cursor = self.txt_traduccion.textCursor()
            pos = cursor.position()
            self.txt_traduccion.setPlainText(texto_limpio)
            cursor.setPosition(pos)
            self.txt_traduccion.setTextCursor(cursor)
            self.txt_traduccion.blockSignals(False)
            texto = texto_limpio

        bytes_actuales = self.calcular_bytes_reales(texto)
        
        if bytes_actuales > limite_bytes:
            self.txt_traduccion.blockSignals(True)
            cursor = self.txt_traduccion.textCursor()
            posicion = cursor.position()
            
            while self.calcular_bytes_reales(texto) > limite_bytes and posicion > 0:
                texto = texto[:posicion-1] + texto[posicion:]
                posicion -= 1
                
            self.txt_traduccion.setPlainText(texto)
            cursor.setPosition(posicion)
            self.txt_traduccion.setTextCursor(cursor)
            self.txt_traduccion.blockSignals(False)
            bytes_actuales = self.calcular_bytes_reales(texto)

        self.lbl_bytes.setText(f"Bytes en la ISO: {bytes_actuales} / {limite_bytes}")
        
        porcentaje = int((bytes_actuales / limite_bytes) * 100) if limite_bytes > 0 else 0
        self.barra_bytes.setValue(min(porcentaje, 100))
        
        if bytes_actuales == limite_bytes:
            self.barra_bytes.setStyleSheet("QProgressBar::chunk { background-color: orange; }")
            self.lbl_bytes.setStyleSheet("font-weight: bold; font-size: 13px; color: orange;")
        else:
            self.barra_bytes.setStyleSheet("QProgressBar::chunk { background-color: #4CAF50; }")
            self.lbl_bytes.setStyleSheet("font-weight: bold; font-size: 13px; color: #dddddd;")

        # ====================================================
        # CORRECCIÓN DE LA POSICIÓN DEL SCROLL EN LA VISTA PREVIA
        # ====================================================
        scrollbar = self.txt_preview.verticalScrollBar()
        posicion_actual = scrollbar.value()
        
        self.txt_preview.setHtml(self.generar_html_preview(texto, tipo))
        
        # Le decimos al scrollbar que regrese a donde estaba antes de renderizar
        scrollbar.setValue(posicion_actual)

    def guardar_traduccion_actual(self):
        if not self.llave_actual or not self.archivo_plantilla: return

        texto = self.txt_traduccion.toPlainText()
        tipo = self.plantilla[self.llave_actual].get("tipo", 2)
        
        if self.config.get('simplificar_acentos', True):
            texto = texto.translate(str.maketrans('áéíóúÁÉÍÓÚäëïöüÄËÏÖÜ', 'aeiouAEIOUaeiouAEIOU'))
            
        if tipo == 1:
            texto = texto.upper()
            
        self.plantilla[self.llave_actual]["traduccion"] = texto

        with open(self.archivo_plantilla, 'w', encoding='utf-8') as f:
            json.dump(self.plantilla, f, ensure_ascii=False, indent=4)

        item = self.lista_textos.currentItem()
        if item:
            mostrar = self.llave_actual[:40] + "..." if len(self.llave_actual) > 40 else self.llave_actual
            if texto.strip():
                item.setText(f"[✓] {mostrar}")
            else:
                item.setText(f"[ ] {mostrar}")

    def saltar_siguiente(self):
        self.guardar_traduccion_actual()
        
        fila_actual = self.lista_textos.currentRow()
        siguiente_fila = fila_actual + 1
        
        while siguiente_fila < self.lista_textos.count():
            item_siguiente = self.lista_textos.item(siguiente_fila)
            if not item_siguiente.isHidden():
                self.lista_textos.setCurrentRow(siguiente_fila)
                self.lista_textos.scrollToItem(item_siguiente)
                break
            siguiente_fila += 1