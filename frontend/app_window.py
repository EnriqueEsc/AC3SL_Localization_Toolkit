from PyQt5.QtWidgets import QMainWindow, QTabWidget
from frontend.tab_extractor import TabExtractor
from frontend.tab_depurador import TabDepurador
from frontend.tab_traductor import TabTraductor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AC3: Silent Line - Localization Toolkit")
        self.resize(1000, 700)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Inicializamos las pestañas
        self.tab_extractor = TabExtractor() # <-- INICIALIZAMOS
        self.tab_depurador = TabDepurador()
        self.tab_traductor = TabTraductor()

        # Añadimos las pestañas al contenedor
        self.tabs.addTab(self.tab_extractor, "0. Extractor (Archivos en bruto)") # <-- NUEVA PESTAÑA
        self.tabs.addTab(self.tab_depurador, "1. Depuración (Filtro Maestro)")
        self.tabs.addTab(self.tab_traductor, "2. Traducción")