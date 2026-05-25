import os
import json
import re

def decodificar_bloque(bloque_bytes):
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
            except UnicodeDecodeError:
                texto += f"[{b:02X}{bloque_bytes[i+1]:02X}]"
            i += 2
        else:
            texto += f"[{b:02X}]"
            i += 1
    return texto

def es_texto_valido(texto_limpio):
    """
    Juez Heurístico basado en los patrones reales de Armored Core 3.
    """
    texto = texto_limpio.strip()
    if not texto: return False

    # 1. PASO DIRECTO (Golden Rules): Si tiene esto, es 100% texto del juego
    tags_seguros = ['<BR>', '\\n', '&p(', '&c(', '&g(', ' : ', '&x(']
    if any(tag in texto for tag in tags_seguros):
        return True

    # 2. PATRÓN DE PIEZAS: Ej. "CHD-SKYEYE", "MCL-SS/RAY"
    # (Al menos 2 letras, un guión, y más letras/números)
    if re.match(r'^[A-Z0-9]{2,4}-[A-Z0-9/]{2,}$', texto):
        return True

    # 3. FILTRO DE BASURA: Si no tiene espacios, suele ser código ensamblador fantasma
    if " " not in texto:
        return False

    # 4. FILTRO DE CORRUPCIÓN: Si tiene demasiados tags [HEX] (más del 20% del texto), es basura
    cantidad_hex = len(re.findall(r'\[[A-F0-9]{2}\]', texto_limpio)) * 4
    if len(texto_limpio) > 0 and (cantidad_hex / len(texto_limpio)) > 0.20:
        return False

    # Si pasó los filtros, probablemente sea una frase o descripción válida
    return True

def generar_diccionario_json(directorio_dat):
    diccionario_juego = {}
    archivos_procesados = 0
    textos_totales = 0
    
    # Atrapa texto válido (ASCII + Japonés) y su padding
    patron_texto = re.compile(b'((?:[\x20-\x7E\x0A\x0D]|[\x81-\x9F\xE0-\xEF][\x40-\x7E\x80-\xFC]){4,})(\x00*)')
    
    archivos_dat = [f for f in os.listdir(directorio_dat) if f.endswith('.dat')]
    total_archivos = len(archivos_dat)
    
    print(f"Iniciando extracción con Filtro Heurístico en {total_archivos} archivos...")

    for i, nombre_archivo in enumerate(archivos_dat):
        if i % 500 == 0 and i > 0:
            print(f"Procesando: {i} / {total_archivos} archivos...")
            
        ruta_completa = os.path.join(directorio_dat, nombre_archivo)
        entradas_archivo = []

        with open(ruta_completa, 'rb') as f:
            datos = f.read()

        for match in patron_texto.finditer(datos):
            bloque_texto = match.group(1)
            bloque_ceros = match.group(2)
            
            texto_decodificado = decodificar_bloque(bloque_texto)
            
            # ---> APLICAMOS TU LÓGICA AQUÍ <---
            if es_texto_valido(texto_decodificado):
                capacidad_total = len(bloque_texto) + len(bloque_ceros)
                entradas_archivo.append({
                    "original": texto_decodificado,
                    "traduccion": "",
                    "max_bytes": capacidad_total
                })
                textos_totales += 1
        
        if entradas_archivo:
            diccionario_juego[nombre_archivo] = entradas_archivo
            archivos_procesados += 1

    ruta_salida = os.path.join("data", "raw_output")
    os.makedirs(ruta_salida, exist_ok=True)
        
    nombre_json = os.path.join(ruta_salida, "SilentLine_Master.json")
    with open(nombre_json, 'w', encoding='utf-8') as f:
        json.dump(diccionario_juego, f, ensure_ascii=False, indent=4)

    print(f"\n¡Extracción finalizada!")
    print(f"Archivos útiles encontrados: {archivos_procesados}")
    print(f"Total de textos filtrados listos para traducir: {textos_totales}")

if __name__ == "__main__":
    generar_diccionario_json('data/dats')