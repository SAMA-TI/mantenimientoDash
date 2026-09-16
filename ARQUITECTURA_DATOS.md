# Arquitectura de Datos — Tablero de Mantenimiento SAMA

Explicación de cómo los archivos CSV de `Analisis6/` y los datos extraídos de los endpoints de la API producen los valores del tablero.

---

## 1. Fuentes de Datos

El tablero tiene **dos fuentes** principales:

| Fuente | Descripción |
|---|---|
| 📁 `Analisis6/*.csv` | Archivos generados previamente con registros históricos de actividad nocturna |
| 🌐 API `sigran.antioquia.gov.co` | Consultas en tiempo real al momento de iniciar el servidor |

---

## 2. Estructura de los archivos CSV

Cada día analizado produce **dos archivos** con el mismo sufijo de fecha (e.g. `august06`):

### `resumen_estaciones_activas__august06.csv`
Registra las estaciones que **estuvieron activas durante la noche anterior** (normalmente entre las 00:00 y las 07:00 del día anterior).

```
estacion_code, dias_desde_ultima_fecha, ultima_fecha_reportada, fecha,       hora
sp_101,        -1.0,                   2026-08-06 05:41:00,    2026-08-06,  05:41:00
sp_102,        -1.0,                   2026-08-06 05:41:00,    2026-08-06,  05:41:00
```

### `resumen_estaciones_august06.csv`
Registra el **estado general de cada estación** al momento del análisis (última actividad conocida).

```
estacion_code, Estado_ultima_semana, calidad_ultima_reportada, dias_desde_ultima_actividad, fecha_ultima_actividad, hora_ultima_actividad
sn_1059,       ACTIVA,              cal2,                     0.0,                         2026-08-06,            10:30:00
sp_101,        ACTIVA,              cal1,                     0.0,                         2026-08-06,            10:28:00
```

---

## 3. Endpoints de la API

| Endpoint | Propósito |
|---|---|
| `/api/v1/estaciones/` | Obtener la lista de todos los códigos de estaciones (sp, sn, sm, sa) |
| `/api/v1/estaciones/{tipo}_{code}/` | Metadata: latitud, longitud, municipio, subregión |
| `/estaciones/sp_{code}/precipitacion?calidad=1\|2&page=1` | Última fecha de dato de precipitación (calidad 1 y 2) |
| `/estaciones/sn_{code}/nivel?calidad=1\|2&page=1` | Última fecha de dato de nivel hídrico |
| `/estaciones/sm_{code}/meteorologia?page=1` | Última fecha de dato meteorológico |
| `/estaciones/sa_{code}/alarma?page=1` | Última actividad de estación de alarma |
| `/estaciones/sn_{code}/camara?page=1` | Última actividad de cámara |

Los tipos de estación son:
- `sp` — Pluviométrica (precipitación)
- `sn` — Hidrométrica (nivel de agua)
- `sm` — Meteorológica
- `sa` — Alarma

---

## 4. Flujo de Procesamiento

### 4.1 Análisis de Intermitencia Nocturna (CSV → tablero)

El objetivo es detectar estaciones que reportaron actividad nocturna pero que luego dejaron de transmitir.

```
resumen_estaciones_activas__august06.csv      resumen_estaciones_august06.csv
         (registros del día ANTERIOR)                (registros del día OBJETIVO)
         fecha filtrada: 2026-08-05                  fecha filtrada: 2026-08-06
                  │                                            │
                  └──────────── MERGE por estacion_code ───────┘
                                         │
                              diferencia_tiempo =
                         fecha_hora_ultima − fecha_hora_activa
                                         │
                              df_resultado_total
                         (acumulado de todos los días)
```

**Ejemplo concreto:**

| Campo | Valor |
|---|---|
| `estacion_code` | `sp_101` |
| Activa a las (noche anterior) | `2026-08-05 05:41` |
| Última actividad registrada | `2026-08-06 10:30` |
| `diferencia_horas` | `~28.8 horas` |

Esto indica que `sp_101` tuvo una **interrupción nocturna**: reportó actividad a las 5:41 am del 5 de agosto y el siguiente dato no apareció hasta el 6 de agosto.

Todos los pares de archivos con la misma fecha se procesan y se acumulan en `df_resultado_total`.

---

### 4.2 Carga de Metadata de Estaciones (API → tablero)

```
GET /api/v1/estaciones/
        │
        ▼
Lista de códigos: sp_codes, sn_codes, sm_codes, sa_codes
        │
        ▼  (consultas en paralelo con ThreadPoolExecutor)
GET /estaciones/sp_101/  →  { latitud: 6.25, longitud: -75.56, municipio: 5, region: 1 }
GET /estaciones/sp_102/  →  { latitud: 6.18, longitud: -75.60, municipio: 5, region: 1 }
...
        │
        ▼
df_metadata
[ estacion | latitud | longitud | municipio_num | subregion_num ]
        │
        ▼  (cruce con estacionesSAMADB.xlsx)
[ estacion | latitud | longitud | Municipio (texto) | Subregion (texto) ]

Ejemplos de mapeo:
  municipio_num = 5  →  "Medellín"
  subregion_num = 1  →  "Valle de Aburra"
  subregion_num = 6  →  "Oriente"
```

---

### 4.3 Estado Actual de Estaciones SP/SN/SM (API → tablero)

Para cada estación se consultan **dos calidades** de datos para determinar si sigue activa:

```
GET /sp_101/precipitacion?calidad=1  →  { values[0].fecha: "2026-08-26T10:00:00" }
GET /sp_101/precipitacion?calidad=2  →  { values[0].fecha: "2026-08-25T08:00:00" }
        │
        ▼
cal1_ultima_fecha = 2026-08-26
cal2_ultima_fecha = 2026-08-25

ultima_fecha_reportada = max(cal1, cal2) = 2026-08-26

dias_desde_ultima_actividad = hoy (2026-08-27) − 2026-08-26 = 1 día

Estado_ultima_semana:
  ≤ 7 días  →  "ACTIVA"
  > 7 días  →  "INACTIVA"

calidad_ultima_reportada:
  Si cal2 > cal1 y año válido (2025/2026)  →  "cal2"
  Si no                                   →  "cal1"
```

**Tabla de ejemplo resultante (`df_ordenado`):**

| estacion_code | Estado_ultima_semana | calidad_ultima_reportada | dias_desde_ultima_actividad | fecha_ultima_actividad |
|---|---|---|---|---|
| `sn_1059` | ACTIVA | cal2 | 1 | 2026-08-26 |
| `sp_101` | ACTIVA | cal1 | 1 | 2026-08-26 |
| `sn_1001` | INACTIVA | cal1 | 48 | 2026-07-10 |

Las estaciones se **ordenan por prioridad**:
- `ACTIVA + cal2` primero (más completas)
- `ACTIVA + cal1` segundo
- `INACTIVA` al final

---

### 4.4 Estado de Alarmas y Cámaras (API → tablero)

```
GET /sa_3030/alarma?page=1    →  { values[0].fecha: "2026-08-26T10:00:00Z" }
GET /sn_1001/camara?page=1   →  { values[0].fecha: "2026-07-01T08:00:00Z" }
        │
        ▼
dias_diferencia = hoy_UTC − fecha_ultima
  sa_3030: 1 día   →  ACTIVA
  sn_1001: 57 días →  INACTIVA
        │
        ▼
df_estado_estaciones
```

---

## 5. De los datos procesados al tablero

Cada sección del tablero visible en el navegador se construye así:

```
                    ┌─────────────────────────────────────────────────────┐
                    │                  TABLERO                            │
                    │                                                     │
  df_resultado      │  🗺️  Mapa de estaciones con intermitencia nocturna  │
  (intermitencias   │  📋 Resumen Intermitencias (conteo por estación)    │
   + geo)           │  📋 Historial de Intermitencias (fechas/horas)      │
                    │  📋 Intermitencias por Municipio                    │
                    │                                                     │
  df_ordenado_geo   │  🗺️  Mapa estaciones con calidad = 2                │
  (estado actual    │  📋 Inactivas SP / SN / SM                         │
   + geo)           │                                                     │
                    │                                                     │
  df_estado_        │  📋 Inactivas Alarma y Cámara                      │
  estaciones        │                                                     │
                    │                                                     │
  fechas_analizadas │  📅 Calendario de fechas analizadas                │
  (de nombres CSV)  │  📌 Última fecha de análisis                        │
                    │                                                     │
  pct_metadata      │  📊 Métricas de respuesta de la API                │
  pct_datos         │                                                     │
                    └─────────────────────────────────────────────────────┘
```

### Detalle por sección

| Sección del tablero | DataFrame fuente | Origen de los datos |
|---|---|---|
| 🗺️ Mapa calidad=2 | `df_cal2` (filtro de `df_ordenado_geo`) | API precipitación/nivel/meteorología + API metadata |
| 📋 Inactivas SP/SN/SM | `df_inactivas` (filtro `INACTIVA` de `df_ordenado`) | API precipitación/nivel/meteorología |
| 📋 Inactivas Alarma/Cámara | `df_inactivas_alcam` (filtro `INACTIVA` de `df_estado_estaciones`) | API alarma + API cámara |
| 🗺️ Mapa intermitencias | `df_resultado` | CSV Analisis6 + API metadata |
| 📋 Resumen Intermitencias | `resumen_intermitencias` (value_counts de `df_resultado_total`) | CSV Analisis6 |
| 📋 Historial Intermitencias | `df_interrupciones` | CSV Analisis6 |
| 📋 Por Municipio | `df_resultado` ordenado por Municipio | CSV Analisis6 + API metadata |
| 📅 Calendario | `fechas_analizadas` | Nombres de archivos CSV |
| 📌 Última fecha | `fecha_mas_reciente` | Nombres de archivos CSV |
| 📊 Métricas API | `pct_metadata`, `pct_datos` | Conteo de respuestas exitosas de la API |

---

## 6. Diagrama completo de dependencias

```
Analisis6/
  resumen_estaciones_activas__*.csv ──┐
  resumen_estaciones_*.csv ───────────┴──► df_resultado_total
                                               │
                                               ├──► resumen_intermitencias ──► Tabla: Resumen
                                               ├──► df_interrupciones ────────► Tabla: Historial
                                               └──► fechas_analizadas ─────────► Calendario / Última fecha

API /estaciones/ ────────────────────────────► sp_codes / sn_codes / sm_codes / sa_codes
                                               │
                      ┌────────────────────────┤
                      ▼                        ▼
API /estaciones/{id}/ ────────────────────► df_metadata
  (metadata)                                   │
                                               ├──► MERGE con resumen_intermitencias ──► df_resultado ──► Mapa intermitencias / Tabla municipio
                                               └──► MERGE con df_ordenado ──────────► df_ordenado_geo ──► Mapa calidad=2

API /sp/precipitacion + /sn/nivel + /sm/meteorologia ──► df_final ──► df_ordenado ──► Tabla inactivas SP/SN/SM

API /sa/alarma + /sn/camara ─────────────────────────────────────► df_estado_estaciones ──► Tabla inactivas Alarma/Cámara
```

---

## 7. Actualización automática

El módulo `data_manager.py` gestiona un `BackgroundScheduler` que recarga todos los datos cada **30 minutos** sin reiniciar el servidor. El flujo completo (CSV + API) se ejecuta de nuevo y el tablero se actualiza automáticamente.

```
Inicio del servidor
      │
      ▼
data_manager.load_data()  ←──────────────────────────┐
      │                                               │
      ▼                                               │ cada 30 minutos
Ejecuta TableroMantenimiento.py completo              │
      │                                               │
      ▼                                               │
Datos almacenados con lock de hilo ──────────────────►┘
      │
      ▼
Dashboard disponible en :8000
```
