from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

class TabTraductor(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        mensaje = QLabel("Aquí cargaremos la Plantilla Maestra depurada\npara comenzar a inyectar el español.")
        layout.addWidget(mensaje)
        self.setLayout(layout)