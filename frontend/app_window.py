from PyQt5.QtWidgets import QMainWindow, QTabWidget
from frontend.tab_depurador import TabDepurador
from frontend.tab_traductor import TabTraductor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AC3: Silent Line - Localization Toolkit")
        self.resize(1000, 700) # Tamaño inicial de la ventana

        # El widget central será el contenedor de pestañas
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Inicializamos las pestañas
        self.tab_depurador = TabDepurador()
        self.tab_traductor = TabTraductor()

        # Añadimos las pestañas al contenedor
        self.tabs.addTab(self.tab_depurador, "1. Depuración (Filtro Mestro)")
        self.tabs.addTab(self.tab_traductor, "2. Traducción e Inyección")