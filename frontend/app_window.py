from PyQt5.QtWidgets import QMainWindow, QTabWidget
from PyQt5.QtGui import QFont
from frontend.tab_extractor import TabExtractor
from frontend.tab_depurador import TabDepurador
from frontend.tab_traductor import TabTraductor
from frontend.tab_compilador import TabCompilador 
from frontend.tab_preferencias import TabPreferencias

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AC3: Silent Line - Localization Toolkit")
        self.resize(1100, 750) 

        self.aplicar_estilo_global()

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.tab_extractor = TabExtractor()
        self.tab_depurador = TabDepurador()
        self.tab_traductor = TabTraductor()
        self.tab_compilador = TabCompilador() 
        self.tab_preferencias = TabPreferencias() 

        self.tabs.addTab(self.tab_extractor, "0. Extractor")
        self.tabs.addTab(self.tab_depurador, "1. Depuración")
        self.tabs.addTab(self.tab_traductor, "2. Traducción")
        self.tabs.addTab(self.tab_compilador, "3. Compilador") 
        self.tabs.addTab(self.tab_preferencias, "⚙️ Preferencias")

    def aplicar_estilo_global(self):
        """
        Define un Dark Theme profesional y formal.
        Al aplicarlo a MainWindow, todas las pestañas hijas heredarán este diseño.
        """
        estilo_oscuro = """
        /* Fondo principal de la ventana */
        QMainWindow {
            background-color: #2b2b2b;
        }
        
        /* Contenedor de las pestañas */
        QTabWidget::pane {
            border: 1px solid #444444;
            background: #323232;
            border-radius: 4px;
        }
        
        /* Diseño de los botones de las pestañas superiores */
        QTabBar::tab {
            background: #2b2b2b;
            color: #aaaaaa;
            padding: 10px 25px;
            border: 1px solid #444444;
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            margin-right: 2px;
        }
        
        /* Pestaña activa */
        QTabBar::tab:selected {
            background: #323232;
            color: #ffffff;
            border-top: 3px solid #2196F3;
            font-weight: bold;
        }
        
        /* Efecto Hover en pestañas inactivas */
        QTabBar::tab:hover:!selected {
            background: #3a3a3a;
            color: #ffffff;
        }
        
        /* Estilo base para cajas de grupo */
        QGroupBox {
            color: #ffffff;
            border: 1px solid #555555;
            border-radius: 4px;
            margin-top: 15px;
            font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 5px;
            left: 10px;
        }
        
        /* Estilos base para campos de texto */
        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #1e1e1e;
            color: #d4d4d4;
            border: 1px solid #555555;
            border-radius: 3px;
            padding: 5px;
        }
        QLineEdit:focus {
            border: 1px solid #2196F3;
        }
        
        /* Estilos base para Listas */
        QListWidget {
            background-color: #1e1e1e;
            color: #d4d4d4;
            border: 1px solid #555555;
            border-radius: 3px;
        }
        QListWidget::item:selected {
            background-color: #2196F3;
            color: #ffffff;
        }
        
        /* Textos estáticos */
        QLabel {
            color: #dddddd;
        }

        /* ================================================= */
        /* SOLUCIÓN: ESTILOS PARA CAJAS DE MENSAJES          */
        /* ================================================= */
        QMessageBox {
            background-color: #2b2b2b;
        }
        QMessageBox QLabel {
            color: #ffffff;
            font-size: 13px;
        }
        QMessageBox QPushButton {
            background-color: #1976D2;
            color: white;
            font-weight: bold;
            border-radius: 4px;
            padding: 6px 15px;
            min-width: 80px;
        }
        QMessageBox QPushButton:hover {
            background-color: #1E88E5;
        }
        """
        self.setStyleSheet(estilo_oscuro)
        
        # Tipografía formal, limpia y legible
        fuente_global = QFont("Segoe UI", 10)
        self.setFont(fuente_global)