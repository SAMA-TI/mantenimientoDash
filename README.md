# Tablero de Mantenimiento SAMA

Descripción
-----------
Este proyecto procesa resúmenes diarios de estaciones (CSV) y construye un tablero interactivo (Dash) para visualizar intermitencias, inactividades y metadata de las estaciones. Calcula diferencias entre la última actividad registrada y los registros de estaciones activas para detectar interrupciones (por ejemplo, intermitencia nocturna). Consulta una API pública de SAMA para obtener metadata (nombre, coordenadas, municipio, subregión) y puede enriquecerla con un archivo Excel local `estacionesSAMADB.xlsx` si está disponible.

Propósito
--------
- Identificar y reportar eventos de interrupción/intermitencia entre días consecutivos.
- Visualizar en un dashboard (Dash) la cantidad de intermitencias por estación, su localización y detalles por municipio/subregión.
- Facilitar la revisión operativa y la priorización de mantenimiento.

Estructura de datos esperada
----------------------------
- Carpeta `Analisis6/` (ya incluida en el repositorio) con archivos CSV con nombres del tipo:
  - `resumen_estaciones_activas__<mes><dia>.csv`
  - `resumen_estaciones_<mes><dia>.csv`

- Opcional: `estacionesSAMADB.xlsx` en la raíz del proyecto para enriquecer metadata de estaciones.

Requisitos
----------
- Python 3.8+ (recomendado)
- Conexión a Internet para consultar la API pública de metadata (opcional, pero recomendada).

Instalación
-----------
1. Crear y activar un entorno virtual (opcional, recomendado):

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

Nota: si `pip install -r requirements.txt` falló antes, se corrigió el archivo `requirements.txt` en este repositorio (eliminé accidentalmente un bloque de código que lo rodeaba). Si ves errores, por favor comparte la salida y lo reviso.

Ejecutar el dashboard
---------------------
1. Asegúrate de que la carpeta `Analisis6/` contiene los CSV de entrada (ya está incluida en el repo de ejemplo).
2. (Opcional) Si tienes `estacionesSAMADB.xlsx`, colócalo en la raíz del proyecto para obtener municipio y subregión más precisos.
3. Ejecuta la aplicación Dash:

```bash
python TableroMantenimiento.py
```

4. Abre tu navegador en:

```
http://127.0.0.1:8050
```



Comportamiento y notas técnicas
-------------------------------
- El script busca archivos CSV en `Analisis6/` con nombres que emparejen las convenciones esperadas. Si las columnas clave faltan en un CSV, ese día se saltará con una advertencia.
- Se realizan llamadas HTTP a `https://sigran.antioquia.gov.co/api/v1/estaciones/<tipo>_<code>/` para obtener metadata. Si estás en una red sin acceso a esa API, la metadata será parcial.
- El proceso es tolerante a separadores (coma/;), y a errores de parseo de fecha — los registros que no se puedan parsear se omiten con advertencias impresas en consola.




