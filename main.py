import sys
from PyQt5.QtWidgets import QApplication
from frontend.app_window import MainWindow

def main():
    # Inicializa la aplicación de PyQt5
    app = QApplication(sys.argv)
    
    # Aplica un estilo moderno (Fusion es nativo multiplataforma)
    app.setStyle("Fusion")
    
    # Crea y muestra la ventana principal
    ventana = MainWindow()
    ventana.show()
    
    # Ejecuta el bucle principal de la aplicación
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()