# AC3SL_Localization_Toolkit

Proyecto personal enfocado en el área de ingeniería inversa y modding. Este es un conjunto de herramientas diseñado para descompilar, depurar, traducir y recompilar los binarios de texto de una copia digital de *Armored Core 3: Silent Line*.

## > Descripción del Sistema <

Apoyándose en *QuickBMS* para el desempaquetado de archivos, este *toolkit* proporciona un flujo de trabajo visual a través de una interfaz gráfica (PyQt6). Permite extraer texto de diálogos, descripciones, interfaces de usuario y *briefings*, modificarlos bajo los límites de memoria originales y volver a inyectarlos en el juego.

### > Módulos de la Interfaz <
- **Extractor:** Solicita los archivos originales `ac3data.bin` y `SLUS_206.44` (obtenidos al extraer la ISO con programas como DkZStudio). Desempaqueta la estructura para buscar cadenas de caracteres editables.
- **Depurador:** Dado que la extracción cruda genera ruido, este módulo permite buscar y categorizar texto legible (Interfaz, Diálogo, Email, Briefing, Misceláneo) mediante búsquedas y selección en lote (Shift o Ctrl + Click derecho).
- **Traductor:** El área de edición. El sistema aplica validaciones estrictas de límite de caracteres para evitar romper los punteros de memoria del juego original. Soporta previsualización del marcado interno del juego (etiquetas para colores rojos, negritas e iconos de UI).
- **Compilador:** Realiza el proceso inverso. Reempaqueta los textos traducidos reconstruyendo los archivos binarios, dejándolos listos para ser reinyectados en la imagen del juego mediante DkZStudio.
- **Preferencias:** Permite el mapeo y sustitución de caracteres (ej. reemplazar símbolos inútiles por 'Ñ', '¿', '¡'). **Nota:** Esto requiere el uso de la función de reemplazo de texturas de emuladores como PCSX2. Se incluyen texturas base para español en la carpeta `assets/`, las cuales deben renombrarse según el volcado (dump) del emulador de cada usuario.

*Archivos adicionales:* En el directorio `scripts_quickbms/` se incluyen los scripts funcionales para la extracción en *Silent Line*. La arquitectura podría ser compatible con *Armored Core 3* base, pero juegos de generaciones posteriores (*Nexus*, *Last Raven*) poseen sistemas de marcado diferentes y requerirían refactorización del código Python.

## > Tecnologías Utilizadas <

- **Python** - Procesamiento de cadenas, punteros y lógica central.
- **PyQt6** - Construcción de la Interfaz Gráfica de usuario multiventana.
- **QuickBMS** - Lenguaje de scripting para la extracción y reinserción de archivos binarios/archivos estructurados.
- **DkZStudio** (Herramienta externa de soporte).

## > Instalación y Ejecución <

1. **Clona el repositorio:**
   ```bash
   git clone [https://github.com/EnriqueEsc/AC3SL_Localization_Toolkit.git](https://github.com/EnriqueEsc/AC3SL_Localization_Toolkit.git)
   cd AC3SL_Localization_Toolkit
Crea y activa un entorno virtual:

   ```bash
  python -m venv venv

  # En Windows:
  venv\Scripts\activate
  # En Linux/Mac:
  source venv/bin/activate
```

Instala las dependencias:

   ```bash
  pip install -r requirements.txt
```
Inicia la interfaz gráfica:

   ```bash
  python main.py
```
