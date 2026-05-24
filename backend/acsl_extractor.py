import os
import json
import re

def decodificar_bloque(bloque_bytes):
    """
    Recorre los bytes intentando decodificar ASCII y Shift-JIS.
    Lo que no entiende, lo deja como etiqueta [HEX].
    """
    texto_formateado = ""
    i = 0
    
    while i < len(bloque_bytes):
        b = bloque_bytes[i]
        
        # 1. Rango ASCII estándar y saltos de línea
        if 32 <= b <= 126:
            texto_formateado += chr(b)
            i += 1
        elif b in (10, 13):
            texto_formateado += '\\n' if b == 10 else ''
            i += 1
            
        # 2. Rango de primer byte para Shift-JIS (Caracteres Japoneses)
        elif (0x81 <= b <= 0x9F or 0xE0 <= b <= 0xEF) and i + 1 < len(bloque_bytes):
            try:
                # Intentamos decodificar el par de bytes
                caracter_sjis = bloque_bytes[i:i+2].decode('shift_jis')
                texto_formateado += caracter_sjis
                i += 2
            except UnicodeDecodeError:
                texto_formateado += f"[{b:02X}]"
                i += 1
                
        # 3. Códigos de control del juego (Colores, iconos, memoria)
        else:
            texto_formateado += f"[{b:02X}]"
            i += 1
            
    return texto_formateado

def generar_diccionario_json(directorio_dat, min_chars=4, umbral_legibilidad=0.60):
    diccionario_juego = {}
    archivos_procesados = 0
    
    # Expresión regular para datos binarios
    # Grupo 1: ([^\x00]+) -> Todo lo que NO sea 00 (El texto o datos)
    # Grupo 2: (\x00+)    -> Uno o más 00 consecutivos (El padding original)
    patron_bloque = re.compile(b'([^\x00]+)(\x00+)')
    
    
    archivos_dat = [f for f in os.listdir(directorio_dat) if f.endswith('.dat')]
    total_archivos = len(archivos_dat)
    
    print(f"Iniciando extracción de {total_archivos} archivos con Lector de Búfer...")

    for i, nombre_archivo in enumerate(archivos_dat):
        # Imprime el progreso cada 500 archivos para no saturar la GUI
        if i % 500 == 0 and i > 0:
            print(f"Procesando: {i} / {total_archivos} archivos...")
            
        ruta_completa = os.path.join(directorio_dat, nombre_archivo)

    # Exportar el JSON maestro a la carpeta raw_output
    ruta_salida = os.path.join("data", "raw_output")
    if not os.path.exists(ruta_salida):
        os.makedirs(ruta_salida)
        
    nombre_json = os.path.join(ruta_salida, "SilentLine_Master.json")
    with open(nombre_json, 'w', encoding='utf-8') as f:
        json.dump(diccionario_juego, f, ensure_ascii=False, indent=4)

    print(f"\n¡Backend finalizado! {archivos_procesados} archivos indexados con éxito.")
    print(f"Base de datos guardada en: {nombre_json}")

if __name__ == "__main__":
    # Apunta esto a la carpeta donde tienes los miles de archivos .dat extraídos
    generar_diccionario_json('.')