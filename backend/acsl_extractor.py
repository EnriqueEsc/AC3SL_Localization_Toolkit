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
    
    # LA MAGIA DEL BÚFER: Expresión regular para datos binarios
    # Grupo 1: ([^\x00]+) -> Todo lo que NO sea 00 (El texto o datos)
    # Grupo 2: (\x00+)    -> Uno o más 00 consecutivos (El padding original)
    patron_bloque = re.compile(b'([^\x00]+)(\x00+)')
    
    print("Iniciando extracción con Lector de Búfer Continuo y Shift-JIS...")

    for nombre_archivo in os.listdir(directorio_dat):
        if not nombre_archivo.endswith('.dat'):
            continue
            
        ruta_completa = os.path.join(directorio_dat, nombre_archivo)
        with open(ruta_completa, 'rb') as f:
            datos = f.read()

        entradas_archivo = []

        # Usamos finditer para "barrer" el archivo bloque por bloque
        for match in patron_bloque.finditer(datos):
            bloque_texto = match.group(1) # Solo el texto
            bloque_ceros = match.group(2) # Solo los 00 que le sobran
            
            # Filtramos si el texto es muy corto
            if len(bloque_texto) < min_chars:
                continue
                
            # Evaluamos legibilidad SOLO en la porción de texto
            bytes_legibles = sum(1 for b in bloque_texto if 32 <= b <= 126 or b in (10, 13) or (0x81 <= b <= 0x9F) or (0xE0 <= b <= 0xEF))
            
            if (bytes_legibles / len(bloque_texto)) >= umbral_legibilidad:
                texto_limpio = decodificar_bloque(bloque_texto)
                
                # Ignorar bloques que sean pura "basura" hexadecimal sin texto real
                if texto_limpio.replace('[', '').replace(']', '').strip():
                    
                    # EL CÁLCULO REAL: Sumamos el peso del texto original + su padding
                    capacidad_total = len(bloque_texto) + len(bloque_ceros)
                    
                    entradas_archivo.append({
                        "original": texto_limpio,
                        "traduccion": "",
                        "max_bytes": capacidad_total # <-- Ahora sí, el espacio 100% real
                    })
        
        if entradas_archivo:
            diccionario_juego[nombre_archivo] = entradas_archivo
            archivos_procesados += 1

    # Exportar el JSON maestro
    nombre_json = "SilentLine_Master.json"
    with open(nombre_json, 'w', encoding='utf-8') as f:
        json.dump(diccionario_juego, f, ensure_ascii=False, indent=4)

    print(f"\n¡Backend finalizado! {archivos_procesados} archivos indexados.")
    print(f"Base de datos guardada en: {nombre_json}")

if __name__ == "__main__":
    # Apunta esto a la carpeta donde tienes los miles de archivos .dat extraídos
    generar_diccionario_json('.')