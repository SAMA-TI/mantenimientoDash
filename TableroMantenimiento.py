import os
import warnings
import requests
import pandas as pd
from glob import glob
from datetime import datetime, timedelta, timezone
from dateutil import parser
from urllib3.exceptions import InsecureRequestWarning
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Import configuration
from config import DATA_FOLDER, APP_HOST, APP_PORT, DEBUG_MODE, get_config_info

#Análisis de Intermitencia Nocturna
carpeta = DATA_FOLDER
archivos = glob(os.path.join(carpeta, "*.csv"))

def leer_csv_robusto(path):
    try:
        df = pd.read_csv(path, dtype=str)
        if df.shape[1] == 1:
            primera_linea = df.columns[0]
            if ',' in primera_linea:
                df = pd.read_csv(path, dtype=str, sep=',')
            elif ';' in primera_linea:
                df = pd.read_csv(path, dtype=str, sep=';')
        return df
    except Exception as e:
        print(f"❌ Error leyendo archivo {path}: {e}")
        return pd.DataFrame()

archivos_activas = {}
archivos_estados = {}

for archivo in archivos:
    nombre = os.path.basename(archivo)
    if "resumen_estaciones_activas__" in nombre:
        key = nombre.split("resumen_estaciones_activas__")[1].replace(".csv", "")
        archivos_activas[key] = archivo
    elif "resumen_estaciones_" in nombre:
        key = nombre.split("resumen_estaciones_")[1].replace(".csv", "")
        archivos_estados[key] = archivo

# DataFrame final acumulado
df_resultado_total = pd.DataFrame()

for key in archivos_activas.keys() & archivos_estados.keys():
    print(f"\n🔍 Procesando dia: {key}")
    
    try:
        df_activas = leer_csv_robusto(archivos_activas[key])
        df_estados = leer_csv_robusto(archivos_estados[key])

        df_activas.columns = df_activas.columns.str.strip()
        df_estados.columns = df_estados.columns.str.strip()

        columnas_activas = {'estacion_code', 'fecha', 'hora'}
        columnas_estados = {'estacion_code', 'fecha_ultima_actividad', 'hora_ultima_actividad'}

        if not columnas_activas.issubset(df_activas.columns) or not columnas_estados.issubset(df_estados.columns):
            continue

        # Convertir key en fecha
        try:
            fecha_key = datetime.strptime(key, "%B%d")  # e.g., "september18"
            fecha_key = fecha_key.replace(year=datetime.now().year)
        except Exception as e:
            print(f"⚠️ No se pudo parsear {key} como fecha válida: {e}")
            continue

        dia_anterior = fecha_key - timedelta(days=1)
        str_fecha_key = fecha_key.strftime("%Y-%m-%d")
        str_dia_anterior = dia_anterior.strftime("%Y-%m-%d")

        # Combinar fecha y hora para crear datetime
        df_activas['fecha_hora'] = pd.to_datetime(df_activas['fecha'] + ' ' + df_activas['hora'], errors='coerce')
        df_estados['fecha_hora_ultima'] = pd.to_datetime(
            df_estados['fecha_ultima_actividad'] + ' ' + df_estados['hora_ultima_actividad'], errors='coerce'
        )

        # Filtrar fechas específicas
        df_activas_filtrado = df_activas[df_activas['fecha_hora'].dt.strftime('%Y-%m-%d') == str_dia_anterior]
        df_estados_filtrado = df_estados[df_estados['fecha_hora_ultima'].dt.strftime('%Y-%m-%d') == str_fecha_key]

        # Merge solo de estaciones que están en ambos
        df_merged = pd.merge(df_activas_filtrado, df_estados_filtrado, on='estacion_code', how='inner')

        # Calcular diferencia en tiempo
        df_merged['diferencia_tiempo'] = df_merged['fecha_hora_ultima'] - df_merged['fecha_hora']
        df_merged['diferencia_horas'] = df_merged['diferencia_tiempo'].dt.total_seconds() / 3600

        def formatear_diferencia(td):
            if pd.isnull(td):
                return "NaT"
            total_min = int(td.total_seconds() // 60)
            dias = total_min // (24 * 60)
            horas = (total_min % (24 * 60)) // 60
            minutos = total_min % 60
            return f"{dias} días, {horas} horas, {minutos} minutos"

        df_merged['diferencia_legible'] = df_merged['diferencia_tiempo'].apply(formatear_diferencia)

        if not df_merged.empty:
            df_resultado_total = pd.concat([df_resultado_total, df_merged], ignore_index=True)
            print(f"✅ {len(df_merged)} filas agregadas para {key}.")
        else:
            print(f"⚠️ No se encontraron coincidencias válidas para {key}.")

    except Exception as e:
        print(f"❌ Error procesando {key}: {e}")


def normalizar_mes(fecha_str):
    meses = {
        'january': 'jan', 'february': 'feb', 'march': 'mar',
        'april': 'apr', 'may': 'may', 'june': 'jun',
        'july': 'jul', 'august': 'aug', 'september': 'sep',
        'october': 'oct', 'november': 'nov', 'december': 'dec'
    }
    fecha_lower = fecha_str.lower()
    for mes_completo, mes_abrev in meses.items():
        if fecha_lower.startswith(mes_completo):
            return mes_abrev + fecha_str[len(mes_completo):]
    return fecha_str

archivos_activas = {}
archivos_estados = {}

for archivo in archivos:
    nombre = os.path.basename(archivo)
    if "resumen_estaciones_activas__" in nombre:
        key = nombre.split("resumen_estaciones_activas__")[1].replace(".csv", "")
        archivos_activas[key] = archivo
    elif "resumen_estaciones_" in nombre:
        key = nombre.split("resumen_estaciones_")[1].replace(".csv", "")
        archivos_estados[key] = archivo

df_resultado_total = pd.DataFrame()

fechas_analizadas = []

for key in archivos_activas.keys() & archivos_estados.keys():
    print(f"\n🔍 Procesando dia: {key}")
    
    try:
        df_activas = leer_csv_robusto(archivos_activas[key])
        df_estados = leer_csv_robusto(archivos_estados[key])

        df_activas.columns = df_activas.columns.str.strip()
        df_estados.columns = df_estados.columns.str.strip()

        columnas_activas = {'estacion_code', 'fecha', 'hora'}
        columnas_estados = {'estacion_code', 'fecha_ultima_actividad', 'hora_ultima_actividad'}

        if not columnas_activas.issubset(df_activas.columns) or not columnas_estados.issubset(df_estados.columns):
            print(f"⚠️ Columnas faltantes en archivos para {key}. Saltando...")
            continue

        key_normalizado = normalizar_mes(key)
        fecha_key = datetime.strptime(key_normalizado, "%b%d")
        fecha_key = fecha_key.replace(year=datetime.now().year)

        fechas_analizadas.append(fecha_key)

        dia_anterior = fecha_key - timedelta(days=1)
        str_fecha_key = fecha_key.strftime("%Y-%m-%d")
        str_dia_anterior = dia_anterior.strftime("%Y-%m-%d")

        df_activas['fecha_hora'] = pd.to_datetime(df_activas['fecha'] + ' ' + df_activas['hora'], errors='coerce')
        df_estados['fecha_hora_ultima'] = pd.to_datetime(
            df_estados['fecha_ultima_actividad'] + ' ' + df_estados['hora_ultima_actividad'], errors='coerce'
        )

        df_activas_filtrado = df_activas[df_activas['fecha_hora'].dt.strftime('%Y-%m-%d') == str_dia_anterior]
        df_estados_filtrado = df_estados[df_estados['fecha_hora_ultima'].dt.strftime('%Y-%m-%d') == str_fecha_key]

        df_merged = pd.merge(df_activas_filtrado, df_estados_filtrado, on='estacion_code', how='inner')

        df_merged['diferencia_tiempo'] = df_merged['fecha_hora_ultima'] - df_merged['fecha_hora']
        df_merged['diferencia_horas'] = df_merged['diferencia_tiempo'].dt.total_seconds() / 3600

        def formatear_diferencia(td):
            if pd.isnull(td):
                return "NaT"
            total_min = int(td.total_seconds() // 60)
            dias = total_min // (24 * 60)
            horas = (total_min % (24 * 60)) // 60
            minutos = total_min % 60
            return f"{dias} días, {horas} horas, {minutos} minutos"

        df_merged['diferencia_legible'] = df_merged['diferencia_tiempo'].apply(formatear_diferencia)

        if not df_merged.empty:
            df_resultado_total = pd.concat([df_resultado_total, df_merged], ignore_index=True)
            print(f"✅ {len(df_merged)} filas agregadas para {key}.")
        else:
            print(f"⚠️ No se encontraron coincidencias válidas para {key}.")
            print(f"🎯 Activas {key}: {len(df_activas_filtrado)} registros en {str_dia_anterior}")
            print(f"🎯 Estados {key}: {len(df_estados_filtrado)} registros en {str_fecha_key}")

    except Exception as e:
        print(f"❌ Error procesando {key}: {e}")

print(f"\n📊 Total de filas resultantes: {len(df_resultado_total)}")

resumen_intermitencias = df_resultado_total['estacion_code'].value_counts().reset_index()
resumen_intermitencias.columns = ['estacion_code', 'cantidad']

def parse_fecha(fecha_str):
    try:
        return parser.parse(str(fecha_str), dayfirst=False)  # Prueba flexible
    except:
        return pd.NaT

# Renombrar y copiar
df_interrupciones = df_resultado_total[['estacion_code', 'fecha', 'hora']].copy()
df_interrupciones.columns = ['codigo_estacion', 'fecha_interrupcion', 'hora_interrupcion']

# Aplicar parseo robusto
df_interrupciones['fecha_interrupcion'] = df_interrupciones['fecha_interrupcion'].apply(parse_fecha)

# Reordenar por código, fecha y hora
df_interrupciones = df_interrupciones.sort_values(
    by=['codigo_estacion', 'fecha_interrupcion', 'hora_interrupcion']
)
# Formatear fecha como string legible (opcional)
df_interrupciones['fecha_interrupcion'] = df_interrupciones['fecha_interrupcion'].dt.strftime('%d/%m/%Y')
df_interrupciones

# Renombrar columnas con formato capitalizado
df_interrupciones.columns = [
    col.replace('_', ' ').title() for col in df_interrupciones.columns
]

# Desactivar advertencias SSL
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

# Estaciones por tipo
sp_codes = ["101", "102", "103", "104", "106", "108", "109", "131", "132", "133", "134", "135", 
            "136", "137", "138", "139", "140", "141", "142", "143", "144", "145", "146", "147", 
            "149", "150", "151", "152", "154", "155", "156","157","158","159","160", "161", "162", "163", "164", "165", "166", "167","168"]

sn_codes = ['1001', '1002', '1003', '1004', '1005', '1007', '1008', '1009', '1010', '1011', '1012', '1013',
            '1014', '1015', '1016', '1018', '1019', '1021', '1022', '1023', '1030', '1031', '1032', '1033',
            '1034', '1035', '1036', '1037', '1038', '1039', '1040', '1041', '1042', '1043', '1044', '1045', 
            '1046', '1047', '1048', '1049', '1050', '1051']

sm_codes =  ['501', '502', '503', '504', '505', '506', '507', '508', '509', '510', '511', '512', '513', '514', '515', '516', '517']

# Función para obtener metadata de estación
def obtener_metadata_estacion(tipo, code):
    url = f"https://sigran.antioquia.gov.co/api/v1/estaciones/{tipo}_{code}/"
    try:
        resp = requests.get(url, verify=False, timeout=10)
        if resp.status_code == 200:
            d = resp.json()
            return {
                "estacion": f"{tipo}_{code}",
                "tipo": tipo,
                "codigo": d.get("codigo"),
                "descripcion": d.get("descripcion"),
                "nombre_web": d.get("nombre_web"),
                "latitud": float(d.get("latitud", 0)),
                "longitud": float(d.get("longitud", 0)),
                "municipio": d.get("municipio"),
                "region": d.get("region")
            }
    except Exception as e:
        print(f"Error al consultar {url}: {e}")
    return None

# Recolectar metadata de todas las estaciones en paralelo
resumen = []

def fetch_metadata_batch(tipo, codes):
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(obtener_metadata_estacion, tipo, code): code for code in codes}
        for future in as_completed(futures):
            data = future.result()
            if data:
                results.append(data)
    return results

print("🔄 Cargando metadata de estaciones en paralelo...")
for tipo, codes in [("sp", sp_codes), ("sn", sn_codes), ("sm", sm_codes)]:
    batch_results = fetch_metadata_batch(tipo, codes)
    resumen.extend(batch_results)
print(f"✅ Metadata cargada: {len(resumen)} estaciones")

# Crear DataFrame final
df_metadata = pd.DataFrame(resumen)

## Cruce de Info API con datos de Municipio y Subregión¶
# Cargar el archivo Excel (Base de datos estaciones SAMA)
try:
    df_excel = pd.read_excel('estacionesSAMADB.xlsx', usecols=[
        'GRUPO', 'MUNICIPIO', 'NOM_EST', 'COD_EST', 'TIPO', 'COMUN_PRIORIZ', 'CORRIENTE', 'LAT', 'LONG'])
    
    # Reorganizar las columnas
    df_excel = df_excel[['COD_EST', 'TIPO', 'GRUPO', 'MUNICIPIO', 'NOM_EST', 'COMUN_PRIORIZ', 'CORRIENTE', 'LAT', 'LONG']]
    
    # LIMPIAR columna COD_EST
    df_excel['COD_EST'] = df_excel['COD_EST'].astype(str).str.strip().str.lower()
    excel_loaded = True
except FileNotFoundError:
    print("⚠️ Archivo 'estacionesSAMADB.xlsx' no encontrado. Continuando sin datos de Excel...")
    df_excel = pd.DataFrame()
    excel_loaded = False

#Correción de regiones erroneas
# Diccionario con los valores correctos
#correcciones = {
#    'sp_163': 8,
#    'sp_149': 3,
#    'sp_151': 6,
#    'sp_158': 6
#}

# Aplicar las correcciones
#for codigo, region_correcta in correcciones.items():
#    df_metadata.loc[df_metadata['codigo'] == codigo, 'region'] = region_correcta

#Organizar columna Municipio
# 1. Renombrar la columna 'municipio' en df_metadata data data data 
df_metadata  = df_metadata.rename(columns={'municipio': 'municipio_num'})

if excel_loaded and not df_excel.empty:
    # 2. Crear un DataFrame auxiliar con solo las columnas necesarias de df_excel
    df_municipio = df_excel[['COD_EST', 'MUNICIPIO']].rename(columns={
        'COD_EST': 'codigo',  # para que coincida con df_metadata
        'MUNICIPIO': 'Municipio'
    })
    
    # 3. Hacer el merge con df_metadata usando la columna común 'codigo'
    df_metadata = df_metadata.merge(df_municipio, on='codigo', how='left')
    
    df_metadata['Municipio'] = df_metadata['Municipio'].str.title()
else:
    # Si no hay Excel, usar municipio_num como Municipio
    df_metadata['Municipio'] = df_metadata.get('municipio_num', 'Desconocido')

#Para subregiones
#Renombrar la columna 'region' a 'subregion_num'
df_metadata = df_metadata.rename(columns={'region': 'subregion_num'})

# Diccionario de equivalencias de subregiones
mapa_subregiones = {
    1: 'Valle de Aburra',
    2: 'Bajo Cauca',
    3: 'Magdalena Medio',
    4: 'Nordeste',
    5: 'Norte',
    6: 'Oriente',
    7: 'Occidente',
    8: 'Suroeste',
    9: 'Urabá'
}

# Creación de la columna 'subregion' usando el diccionario
df_metadata['Subregion'] = df_metadata['subregion_num'].map(mapa_subregiones)

# Unir los DataFrames usando 'estacion_code' y 'estacion' como clave
df_resultado = resumen_intermitencias.merge(
    df_metadata[['estacion', 'latitud', 'longitud', 'Municipio', 'Subregion']],
    how='left',
    left_on='estacion_code',
    right_on='estacion'
)

# Opcional: eliminar la columna 'estacion' si no la necesitas
df_resultado = df_resultado.drop(columns=['estacion'])

# Función para traducir fecha a formato español
def traducir_fecha_espanol(fecha):
    meses = {
        "January": "enero", "February": "febrero", "March": "marzo", "April": "abril",
        "May": "mayo", "June": "junio", "July": "julio", "August": "agosto",
        "September": "septiembre", "October": "octubre", "November": "noviembre", "December": "diciembre"
    }
    return fecha.strftime("%d de ") + meses[fecha.strftime("%B")]
    
# Construir DataFrame con fechas analizadas
df_fechas = pd.DataFrame({"fecha": fechas_analizadas})
df_fechas["fecha_es"] = df_fechas["fecha"].apply(traducir_fecha_espanol)
df_fechas["mes"] = df_fechas["fecha"].dt.month
df_fechas["día"] = df_fechas["fecha"].dt.day
df_fechas["fecha_str"] = df_fechas["fecha"].dt.strftime("%Y-%m-%d")


# Obtener la fecha actual
fecha_actual = datetime.now()

# Formatear la fecha en el formato "abril30"
fecha_formateada = fecha_actual.strftime("%B%d").lower()
fecha_formateada

# Desactivar advertencias SSL
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

# Estaciones de precipitación (sp)
sp_codes = ["101", "102", "103", "104", "106", "108", "109", "131", "132", "133", "134", "135", 
            "136", "137", "138", "139", "140", "141", "142", "143", "144", "145", "146", "147", 
            "149", "150", "151", "152", "154", "155", "156", "157","158","159","160", "161", "162",
            "163"]

# Estaciones de nivel (sn)
sn_codes = ['1001', '1002', '1003', '1004', '1005', '1007', '1008', '1009', '1010', '1011', '1012', '1013',
            '1014', '1015', '1016', '1018', '1019', '1021', '1022', '1023', '1030', '1031', '1032', '1033',
            '1034', '1035', '1036', '1037', '1038', '1039', '1040', '1041', '1042', '1043', '1044', '1045', 
            '1046', '1047', '1048']

#Estaciones de meteorología (sm)
sm_codes =  ['501', '502', '503', '504', '505', '506', '507', '508', '509', '510', '511', '512', '513', '514', '515', '516', '517']
        



# Función para obtener datos por estación y calidad
def obtener_datos(tipo, code, calidad):
    if tipo == "sp":
        url = f"https://sigran.antioquia.gov.co/api/v1/estaciones/sp_{code}/precipitacion?calidad={calidad}&page=1"
    elif tipo == 'sn':
        url = f"https://sigran.antioquia.gov.co/api/v1/estaciones/sn_{code}/nivel?calidad={calidad}&page=1"
    else: 
        url = f"https://sigran.antioquia.gov.co/api/v1/estaciones/sm_{code}/meteorologia?&page=1"
    
    try:
        response = requests.get(url, verify=False, timeout=30)
    except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
        print(f"⚠️ Timeout/Error para {tipo}_{code} calidad {calidad}")
        return None, None
    
    if response.status_code == 200:
        data = response.json()
        if data and 'values' in data and len(data['values']) > 0:
            fecha = data['values'][0]['fecha']
            es_2025 = 1 if str(fecha).startswith("2025") else 0
            return es_2025, fecha
    return None, None

# Función para procesar una estación completa (ambas calidades)
def procesar_estacion(tipo, code):
    estacion = f"{tipo}_{code}"
    fila = {"estacion_code": estacion}
    
    for calidad in [1, 2]:
        es_2025, fecha = obtener_datos(tipo, code, calidad)
        fila[f"cal{calidad}_es_2025"] = es_2025
        fila[f"cal{calidad}_ultima_fecha"] = fecha
    
    return fila

# Lista para los resultados
resumen = []

# Procesar todas las estaciones en paralelo
print("🔄 Cargando datos de estaciones en paralelo...")
with ThreadPoolExecutor(max_workers=20) as executor:
    futures = []
    for tipo, codes in [("sp", sp_codes), ("sn", sn_codes), ("sm", sm_codes)]:
        for code in codes:
            futures.append(executor.submit(procesar_estacion, tipo, code))
    
    for i, future in enumerate(as_completed(futures), 1):
        result = future.result()
        resumen.append(result)
        if i % 10 == 0:
            print(f"  Procesadas {i}/{len(futures)} estaciones...")

print(f"✅ Datos cargados: {len(resumen)} estaciones")

# Crear DataFrame final
df_final = pd.DataFrame(resumen)

# Crear DataFrame final
df_final = pd.DataFrame(resumen)

# Convertir columnas es_2025 a enteros (con soporte para NaN)
df_final["cal1_es_2025"] = df_final["cal1_es_2025"].astype("Int64")
df_final["cal2_es_2025"] = df_final["cal2_es_2025"].astype("Int64")

# Forzar fechas sin zona horaria
df_final["cal1_ultima_fecha"] = pd.to_datetime(df_final["cal1_ultima_fecha"], errors='coerce').dt.tz_localize(None)
df_final["cal2_ultima_fecha"] = pd.to_datetime(df_final["cal2_ultima_fecha"], errors='coerce').dt.tz_localize(None)

# Obtener fecha actual sin zona horaria (tz-naive)
hoy = pd.Timestamp.now(tz=None)

# 1. Última fecha reportada entre cal1 y cal2
df_final["ultima_fecha_reportada"] = df_final[["cal1_ultima_fecha", "cal2_ultima_fecha"]].max(axis=1)

# 2. Días desde la última fecha
df_final["dias_desde_ultima_actividad"] = (hoy - df_final["ultima_fecha_reportada"]).dt.days
df_final.loc[df_final["ultima_fecha_reportada"].isna(), "dias_desde_ultima_actividad"] = pd.NA

# 3. Verificar si la última fecha es de 2025
es_2025_cal1 = df_final["cal1_ultima_fecha"].dt.year == 2025
es_2025_cal2 = df_final["cal2_ultima_fecha"].dt.year == 2025

df_final["ultima_fecha_2025"] = pd.NaT
df_final["calidad_ultima_reportada"] = pd.NA

for i, row in df_final.iterrows():
    f1, f2 = row["cal1_ultima_fecha"], row["cal2_ultima_fecha"]
    if pd.notnull(f1) and f1.year == 2025 and (pd.isnull(f2) or f1 >= f2 or f2.year != 2025):
        df_final.at[i, "ultima_fecha_2025"] = f1
        df_final.at[i, "calidad_ultima_reportada"] = "cal1"
    elif pd.notnull(f2) and f2.year == 2025:
        df_final.at[i, "ultima_fecha_2025"] = f2
        df_final.at[i, "calidad_ultima_reportada"] = "cal2"
        
# 4. Verificar si la última fecha es reciente (últimos 30 días)
df_final["es_reciente"] = (
    df_final["ultima_fecha_reportada"]
    .apply(lambda x: 1 if pd.notnull(x) and (hoy - x).days <= 30 else (0 if pd.notnull(x) else pd.NA))
)

# Creación la columna 'Estado_ultima_semana'
df_final['Estado_ultima_semana'] = df_final['dias_desde_ultima_actividad'].apply(lambda x: 'ACTIVA' if pd.notnull(x) and x <= 7 else 'INACTIVA')

# Garantizar de que las columnas de fecha estén en formato datetime
df_final['cal1_ultima_fecha'] = pd.to_datetime(df_final['cal1_ultima_fecha'])
df_final['cal2_ultima_fecha'] = pd.to_datetime(df_final['cal2_ultima_fecha'])

# Crear columna 'dias_desde_ultima_cal1' solo si cal2 > cal1
df_final['dias_desde_ultima_cal1'] = (
    df_final['cal2_ultima_fecha'] - df_final['cal1_ultima_fecha']
).dt.days

df_final['dias_desde_ultima_cal1'] = df_final.apply(
    lambda row: row['dias_desde_ultima_cal1'] if pd.notnull(row['cal2_ultima_fecha']) and row['cal2_ultima_fecha'] > row['cal1_ultima_fecha'] else None,
    axis=1
)

# Crear una columna auxiliar para ordenar según prioridad deseada
def prioridad(row):
    if row['Estado_ultima_semana'] == 'ACTIVA' and row['calidad_ultima_reportada'] == 'cal2':
        return 0
    elif row['Estado_ultima_semana'] == 'ACTIVA' and row['calidad_ultima_reportada'] == 'cal1':
        return 1
    else:
        return 2

df_final['orden_prioridad'] = df_final.apply(prioridad, axis=1)

# Ordenar por prioridad, luego por días y luego por estación
df_final = df_final.sort_values(
    by=['orden_prioridad', 'dias_desde_ultima_actividad', 'estacion_code'],
    ascending=[True, True, False]
).drop(columns='orden_prioridad')

# Reubicar 'Estado_ultima_semana' justo después de 'estacion_code'
cols = df_final.columns.tolist()
cols.insert(1, cols.pop(cols.index('Estado_ultima_semana')))
df_final = df_final[cols]

# COnvetrtir  la columna a tipo datetime
df_final['timestamp'] = pd.to_datetime(df_final['ultima_fecha_reportada'])

#Crear nuevas columnas de fecha y hora
df_final['fecha_ultima_actividad']= df_final['timestamp'].dt.date
df_final['hora_ultima_actividad']= df_final['timestamp'].dt.time

df_ordenado = df_final[['estacion_code', 'Estado_ultima_semana',  'calidad_ultima_reportada', 'dias_desde_ultima_cal1', 'dias_desde_ultima_actividad','fecha_ultima_actividad', 'hora_ultima_actividad']]

#Análisis estaciones de Alarma y Cámara
# Desactivar advertencias SSL
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

# Estaciones de alarma (sa)
sa_codes = ['1036', '3030', '3031', '3032', '3033', '3034', '3035', '3037', '3038', '3039',
            '3040', '3041', '3042', '3043', '3044', '3045', '3046', '3047', '3048', '3049',
            '3050', '3051', '3052', '3053', '3054', '3055', '3056', '3057', '3058', '3059']

# Estaciones de cámara (sn)
sn_codes = ['1008', '1009', '1010', '1011', '1012', '1013', '1014', '1015']

# Fecha actual en UTC
hoy = datetime.now(timezone.utc)

# Lista para guardar los datos
datos_estaciones = []

# --- Función para procesar la respuesta y extraer los datos requeridos ---
def procesar_fecha(fecha_str):
    # Convertir string a objeto datetime
    fecha_dt = datetime.strptime(fecha_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    dias_diferencia = (hoy - fecha_dt).days
    estado = "ACTIVA" if dias_diferencia < 7 else "INACTIVA"
    fecha_formateada = fecha_dt.strftime("%d/%m/%Y")
    hora_formateada = fecha_dt.strftime("%H:%M")
    return estado, fecha_formateada, hora_formateada, dias_diferencia

# Función para procesar una estación de alarma
def procesar_estacion_alarma(code):
    url = f"https://sigran.antioquia.gov.co/api/v1/estaciones/sa_{code}/alarma?page=1"
    try:
        response = requests.get(url, verify=False, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("values"):
                ultima = data["values"][0]
                estado, fecha_act, hora_act, dias = procesar_fecha(ultima["fecha"])
                return {
                    "estacion_code": f"sa_{code}",
                    "Estado_ultima_semana": estado,
                    "fecha_ultima_actividad": fecha_act,
                    "hora_ultima_actividad": hora_act,
                    "dias_desde_ultima_actividad": dias
                }
    except Exception as e:
        print(f"Error con sa_{code}: {e}")
    return None

# Función para procesar una estación de cámara
def procesar_estacion_camara(code):
    url = f"https://sigran.antioquia.gov.co/api/v1/estaciones/sn_{code}/camara?page=1"
    try:
        response = requests.get(url, verify=False, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("values"):
                ultima = data["values"][0]
                estado, fecha_act, hora_act, dias = procesar_fecha(ultima["fecha"])
                return {
                    "estacion_code": f"sn_{code}",
                    "Estado_ultima_semana": estado,
                    "fecha_ultima_actividad": fecha_act,
                    "hora_ultima_actividad": hora_act,
                    "dias_desde_ultima_actividad": dias
                }
    except Exception as e:
        print(f"Error con sn_{code}: {e}")
    return None

# --- Consulta estaciones en paralelo ---
print("🔄 Cargando datos de alarmas y cámaras en paralelo...")
datos_estaciones = []

with ThreadPoolExecutor(max_workers=15) as executor:
    # Procesar alarmas
    futures_alarma = {executor.submit(procesar_estacion_alarma, code): code for code in sa_codes}
    # Procesar cámaras
    futures_camara = {executor.submit(procesar_estacion_camara, code): code for code in sn_codes}
    
    all_futures = {**futures_alarma, **futures_camara}
    for future in as_completed(all_futures):
        result = future.result()
        if result:
            datos_estaciones.append(result)

print(f"✅ Datos de alarmas/cámaras cargados: {len(datos_estaciones)} estaciones")

# --- Crear el DataFrame ---
df_estado_estaciones = pd.DataFrame(datos_estaciones)

# --- Añadir columna auxiliar para tipo de estación (para ordenar) ---
df_estado_estaciones["tipo"] = df_estado_estaciones["estacion_code"].str[:2]

# --- Definir orden personalizado para estado y tipo ---
estado_orden = {"ACTIVA": 0, "INACTIVA": 1}
tipo_orden = {"sa": 0, "sn": 1}

# --- Aplicar columnas auxiliares para ordenamiento ---
df_estado_estaciones["estado_orden"] = df_estado_estaciones["Estado_ultima_semana"].map(estado_orden)
df_estado_estaciones["tipo_orden"] = df_estado_estaciones["tipo"].map(tipo_orden)

# --- Ordenar ---
df_estado_estaciones = df_estado_estaciones.sort_values(
    by=["estado_orden", "tipo_orden", "dias_desde_ultima_actividad"]
).drop(columns=["estado_orden", "tipo_orden", "tipo"])

# --- Resetear índices si lo deseas ---
df_estado_estaciones.reset_index(drop=True, inplace=True)


### TABLERO
# Garantizar que las fechas estén en datetime
fechas_analizadas = sorted(list(set(fechas_analizadas)))
fechas_analizadas = [f.replace(hour=0, minute=0, second=0, microsecond=0) for f in fechas_analizadas]

# Rango de días mínimo y máximo
fecha_min = min(fechas_analizadas)
fecha_max = max(fechas_analizadas)

# Expandimos a semanas completas (lunes a domingo)
inicio_semana = fecha_min - timedelta(days=fecha_min.weekday())
fin_semana = fecha_max + timedelta(days=(6 - fecha_max.weekday()))

# Crear lista completa de fechas entre esos días
fechas_completas = pd.date_range(inicio_semana, fin_semana, freq='D')

# Construir estructura de calendario: cada fila = semana, columnas = lun-dom
semanas = []
semana_actual = []

for i, fecha in enumerate(fechas_completas):
    if fecha.weekday() == 0 and semana_actual:  # lunes
        semanas.append(semana_actual)
        semana_actual = []
    semana_actual.append(fecha)

if semana_actual:
    semanas.append(semana_actual)

# Normalizar cada semana a 7 días
for s in semanas:
    while len(s) < 7:
        s.append(None)

# Función para traducir día
def formato_fecha(fecha):
    if fecha is None:
        return ""
    dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    return f"{dias[fecha.weekday()]} {fecha.day}"

# Colores: azul si está en fechas_analizadas
def color_celda(fecha):
    if fecha is None:
        return "#ffffff"
    elif fecha in fechas_analizadas:
        return "#007BFF"
    else:
        return "#f2f2f2"

# Crear datos para la tabla
celdas_texto = []
celdas_color = []

for semana in semanas:
    fila_texto = [formato_fecha(d) for d in semana]
    fila_color = [color_celda(d) for d in semana]
    celdas_texto.append(fila_texto)
    celdas_color.append(fila_color)

# Transponer para plotly (columnas = días)
celdas_texto_t = list(map(list, zip(*celdas_texto)))
celdas_color_t = list(map(list, zip(*celdas_color)))

# Encabezados de columnas
encabezados = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go


# Unir df_ordenado con df_metadata para obtener georreferencia
df_ordenado_geo = df_ordenado.merge(
    df_metadata[['estacion', 'latitud', 'longitud', 'Municipio', 'Subregion']],
    how='left',
    left_on='estacion_code',
    right_on='estacion'
)

#  Mapa de estaciones con calidad = cal2
df_cal2 = df_ordenado_geo[df_ordenado_geo['calidad_ultima_reportada'] == 'cal2']

if not df_cal2.empty:
    fig_map_cal2 = px.scatter_mapbox(
        df_cal2,
        lat="latitud",
        lon="longitud",
        hover_name="estacion_code",
        hover_data=["Estado_ultima_semana", "dias_desde_ultima_actividad", "Municipio", "Subregion"],
        color="Estado_ultima_semana",
        zoom=7,
        height=500
    )
    fig_map_cal2.update_traces(marker=dict(size=15))
    fig_map_cal2.update_layout(mapbox_style="open-street-map") #, title="Estaciones con calidad cal2"
else:
    fig_map_cal2 = None

#  Mapa general con todas las estaciones de df_resultado (usar estacion_code)
fig_all = px.scatter_mapbox(
    df_resultado,
    lat="latitud",
    lon="longitud",
    hover_name="estacion_code",
    hover_data=["Municipio", "Subregion"],
    zoom=7,
    height=500
)
fig_all.update_traces(marker=dict(size=15)) 
fig_all.update_layout(mapbox_style="open-street-map") #, title="Ubicación de las intermitencias"

###Prueba
# Calendario con fechas analizadaas

fig_calendario = go.Figure(data=[go.Table(
    header=dict(
        values=encabezados,
        fill_color='#1a1a1a',
        font=dict(color='white', size=14),
        align='center'
    ),
    cells=dict(
        values=celdas_texto_t,
        fill_color=celdas_color_t,
        align='center',
        font=dict(size=12, color='black'),
        height=30
    )
)])
fig_calendario.update_layout(
    #title="📅 Fechas Analizadas (Últimos Días)",
    height=300 + len(semanas) * 30,
    margin=dict(l=20, r=20, t=40, b=20)
)

# Última fecha de análisis
fecha_mas_reciente = max(fechas_analizadas)
fecha_mas_reciente_str = traducir_fecha_espanol(fecha_mas_reciente)

### Hasta acá prueba

# ========================
# 🔍 TABLAS 
# ========================

# ============
# 🎨 Estilos
# ============
# Tabla 1: Estilo ajustado al contenido
tabla_style_table_estrecha = {
    'overflowX': 'auto',
    'width': 'fit-content',
    'margin': 'auto',
    'border': '1px solid lightgray',
    'borderRadius': '5px', #
    'boxShadow': '0 2px 6px rgba(0,0,0,0.1)',#
    'padding': '10px'#
}

# Tabla 2: Estilo intermedio (región y municipio)
tabla_style_table_media = {
    'overflowX': 'auto',
    'maxWidth': '80%',
    'margin': 'auto',
    'border': '1px solid lightgray'
}

# Tabla 3: Scroll horizontal para muchas columnas
tabla_style_table_scroll = {
    'overflowX': 'scroll',
    'minWidth': '1000px',
    'margin': 'auto',
    'border': '1px solid lightgray'
}

# Estilos comunes para celdas y encabezado
tabla_style_cell_comun = {
    'textAlign': 'center',
    'padding': '5px',
    'whiteSpace': 'normal',
    'height': 'auto',
    'minWidth': '100px',
    'maxWidth': '250px',
    'overflow': 'hidden',
    'textOverflow': 'ellipsis'
}

tabla_style_header = {
    'backgroundColor': '#f1f1f1',
    'fontWeight': 'bold',
    'textAlign': 'center',  #'textAlign': 'left'
    'borderBottom': '2px solid #ccc'
}

# =======================
# 1.Tabla Resumen cantidad
# =======================
tabla_cantidad = dash_table.DataTable(
    columns=[
    {"name": "Código Estación", "id": "estacion_code"},
    {"name": "Cantidad", "id": "cantidad"}
    ],
    data=df_resultado[['estacion_code', 'cantidad']].to_dict('records'),
    style_table=tabla_style_table_estrecha,
    style_cell=tabla_style_cell_comun,
    style_header=tabla_style_header
)

# =======================
# 2. Tabla Región y municipio
# =======================
tabla_region_municipio = dash_table.DataTable(
    columns=[{"name": i, "id": i} for i in [ 'Municipio', 'estacion_code']],  #'Subregion',
    data=df_resultado.sort_values([ 'Municipio'])[['Subregion', 'Municipio', 'estacion_code']].to_dict('records'),  #'Subregion','Municipio'
    style_table=tabla_style_table_media,
    style_cell=tabla_style_cell_comun,
    style_header=tabla_style_header,
    page_size=20
)

# =======================
# 3. Tabla Historial de intermitencias
# =======================
tabla_interrupciones = dash_table.DataTable(
    columns=[{"name": i, "id": i} for i in df_interrupciones.columns],
    data=df_interrupciones.to_dict('records'),
    style_table=tabla_style_table_media,
    style_cell=tabla_style_cell_comun,
    style_header=tabla_style_header,
    page_size=15
)

# =======================
# 4. Tabla Estaciones inactivas
# =======================
#df_inactivas = df_ordenado[df_ordenado["Estado_ultima_semana"] == "INACTIVA"]
df_inactivas = df_ordenado[df_ordenado["Estado_ultima_semana"] == "INACTIVA"].drop(columns=["dias_desde_ultima_cal1"])


tabla_inactivas = dash_table.DataTable(
    columns=[
        {"name": col.replace("_", " ").title(), "id": col}
        for col in df_inactivas.columns
    ],
    data=df_inactivas.to_dict('records'),
    style_table=tabla_style_table_scroll,
    style_cell=tabla_style_cell_comun,
    style_header=tabla_style_header,
    page_size=15
)

# =======================
# 5. Tabla Estaciones inactivas alarma y cámara
# =======================
#df_inactivas = df_ordenado[df_ordenado["Estado_ultima_semana"] == "INACTIVA"]
df_inactivas_alcam = df_estado_estaciones[df_estado_estaciones["Estado_ultima_semana"] == "INACTIVA"]


tabla_inactivas_alcam = dash_table.DataTable(
    columns=[
    {"name": "Código Estación", "id": "estacion_code"},
    {"name": "Estado última semana", "id": "Estado_ultima_semana"},
    {"name": "Fecha Última Actividad", "id": "fecha_ultima_actividad"},
    {"name": "Hora Última Actividad", "id": "hora_ultima_actividad"},
    {"name": "Dias desde Última Actividad", "id": "dias_desde_ultima_actividad"}
    ],
    data=df_inactivas_alcam.to_dict('records'),
    style_table=tabla_style_table_scroll,
    style_cell=tabla_style_cell_comun,
    style_header=tabla_style_header,
    page_size=15
)



# =============================
# 🔧 Creación del dashboard en Dash
# =============================
app = dash.Dash(__name__)
server = app.server  # Exponer el servidor Flask para Gunicorn
# Título que aparece en la pestaña del navegador
app.title = "Mantenimiento SAMA"

app.layout = html.Div([
    html.H1(
        "🔧Tablero de Monitoreo de Estaciones para Mantenimiento- SAMA",
        style={
            'textAlign': 'center',
            'color': '#007BFF'  # Azul Bootstrap
        }),

    html.H2("Mapa de estaciones en calidad =2"),

    # Mostrar gráfico si existe, si no, mostrar mensaje estilizado
    html.Div(
        dcc.Graph(figure=fig_map_cal2) if fig_map_cal2 else html.Div(
            "⚠️ En el momento no hay estaciones en Calidad=2.",
            style={
                'color': '#b30000',
                'backgroundColor': '#ffe6e6',
                'border': '2px solid #b30000',
                'borderRadius': '5px',
                'padding': '15px',
                'margin': '10px 0',
                'fontWeight': 'bold',
                'fontSize': '16px',
                'textAlign': 'center'
            }
        )
    ),

    html.Div([
        html.H2("Resumen estaciones Precipitación, Nivel y Meteorológicas Inactivas"),
        html.Button("📥 Descargar CSV", id="btn-descargar-inactivas", n_clicks=0),
        dcc.Download(id="descarga-inactivas"),
        tabla_inactivas
    ], style={'padding': '20px'}),


    html.Div([
        html.H2("Resumen estaciones Alarma y Cámara Inactivas"),
        html.Button("📥 Descargar CSV", id="btn-descargar-inactivas-Alarma-Camara", n_clicks=0),
        dcc.Download(id="descarga-inactivas-Alarma-Camara"),
        tabla_inactivas_alcam
    ], style={'padding': '20px'}),

    html.H2("Mapa de estaciones con intermitencia nocturna"),
    dcc.Graph(figure=fig_all),

    html.Div([
        html.H2("Resumen Intermitencias"),
        tabla_cantidad
    ], style={'padding': '20px'}),

    html.Div([
    html.H2("Historial de Intermitencias"),
    html.Button("📥 Descargar CSV", id="btn-descargar-interrupciones", n_clicks=0),
    dcc.Download(id="descarga-interrupciones"),
    tabla_interrupciones
    ], style={'padding': '20px'}),

    html.Div([
        html.H2("Intermitencias por Municipio"),
        html.Button("📥 Descargar CSV", id="btn-descargar-region", n_clicks=0),
        dcc.Download(id="descarga-region"),
        tabla_region_municipio
    ], style={'padding': '20px'}),

    # =======================Prueba
    # 📅 Visual Calendario y Última Fecha
    # =======================

    html.Div([
        html.H2("📅 Fechas Analizadas"),
        dcc.Graph(figure=fig_calendario)
    ], style={'padding': '20px'}),
    
    html.Div([
        html.H2("📌 Última Fecha Análisis de Intermitencias"),
        html.Div(fecha_mas_reciente_str, style={
            'color': 'white',
            'backgroundColor': '#007BFF',
            'padding': '20px',
            'fontSize': '24px',
            'textAlign': 'center',
            'borderRadius': '10px',
            'fontWeight': 'bold'
        })
    ], style={'padding': '20px'})

    ### Hasta acá prueba
    ])


# ====================
# CALLBACKS DE DESCARGA
# ====================
# Callbacks
@app.callback(
    Output("descarga-region", "data"),
    Input("btn-descargar-region", "n_clicks"),
    prevent_initial_call=True
)
def descargar_region(n_clicks):
    fecha = datetime.now().strftime("%Y%m%d")
    nombre = f"intermitencias_por_region_{fecha}.csv"
    df = df_resultado.sort_values(['Subregion', 'Municipio'])[['Subregion', 'Municipio', 'estacion_code']]
    return dcc.send_data_frame(df.to_csv, nombre, index=False)

@app.callback(
    Output("descarga-inactivas", "data"),
    Input("btn-descargar-inactivas", "n_clicks"),
    prevent_initial_call=True
)
def descargar_inactivas(n_clicks):
    fecha = datetime.now().strftime("%Y%m%d")
    nombre = f"estaciones_inactivas_{fecha}.csv"
    df = df_ordenado[df_ordenado["Estado_ultima_semana"] == "INACTIVA"]
    return dcc.send_data_frame(df.to_csv, nombre, index=False)

@app.callback(
    Output("descarga-inactivas-Alarma-Camara", "data"),
    Input("btn-descargar-inactivas-Alarma-Camara", "n_clicks"),
    prevent_initial_call=True
)
def descargar_inactivas_alarma_camara(n_clicks):
    fecha = datetime.now().strftime("%Y%m%d")
    nombre = f"estaciones_inactivas_alarma_camara_{fecha}.csv"
    df2 = df_estado_estaciones[df_estado_estaciones["Estado_ultima_semana"] == "INACTIVA"]
    return dcc.send_data_frame(df2.to_csv, nombre, index=False)

@app.callback(
    Output("descarga-interrupciones", "data"),
    Input("btn-descargar-interrupciones", "n_clicks"),
    prevent_initial_call=True
)
def descargar_interrupciones(n_clicks):
    fecha = datetime.now().strftime("%Y%m%d")
    nombre = f"interrupciones_estaciones_{fecha}.csv"
    return dcc.send_data_frame(df_interrupciones.to_csv, nombre, index=False)

# ====================
# INICIAR SERVIDOR
# ====================
if __name__ == "__main__":
    print(get_config_info())
    app.run(debug=DEBUG_MODE, host=APP_HOST, port=APP_PORT)