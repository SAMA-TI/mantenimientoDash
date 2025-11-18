# Tablero de Mantenimiento SAMA

## Índice

- [Descripción](#descripción)
- [Propósito](#propósito)
- [Autora](#autora)
- [Soporte](#soporte)
- [Estructura de datos esperada](#estructura-de-datos-esperada)
- [Requisitos del Sistema](#requisitos-del-sistema)
- [Instalación](#instalación)
- [Ejecutar el dashboard](#ejecutar-el-dashboard)
  - [Verificar que la aplicación está corriendo](#verificar-que-la-aplicación-está-corriendo)
  - [Detener la aplicación](#detener-la-aplicación)
  - [Ejecutar en segundo plano](#ejecutar-en-segundo-plano)
- [Despliegue](#despliegue)
  - [Estándar de Configuración de Túneles](#estándar-de-configuración-de-túneles)
  - [Instalar cloudflared](#instalar-cloudflared)
  - [Autenticación en cloudflared](#autenticación-en-cloudflared)
  - [Crear un tunel y nombrarlo](#crear-un-tunel-y-nombrarlo)
  - [Configurar tunel para que apunte al servicio local](#configurar-tunel-para-que-apunte-al-servicio-local)
  - [Enrutar el tráfico sin un dominio](#enrutar-el-tráfico-sin-un-dominio)
  - [Enrutar el tráfico con dominio](#enrutar-el-tráfico-con-dominio)
  - [Run the tunnel](#run-the-tunnel)
  - [Configurar Túneles como Servicios Systemd](#configurar-túneles-como-servicios-systemd)
    - [Método 1: Instalación automática](#método-1-instalación-automática-recomendado-para-configuraciones-simples)
    - [Método 2: Configuración manual](#método-2-configuración-manual-recomendado-para-control-completo)
- [Actualización de Datos](#actualización-de-datos)
- [Variables de Entorno y Configuración](#variables-de-entorno-y-configuración)
- [Comportamiento y Notas Técnicas](#comportamiento-y-notas-técnicas)
- [Troubleshooting (Solución de Problemas)](#troubleshooting-solución-de-problemas)
  - [Problema: No hay archivos CSV en Analisis6/](#problema-no-hay-archivos-csv-en-analisis6)
  - [Problema: La aplicación no inicia o muestra errores de módulos](#problema-la-aplicación-no-inicia-o-muestra-errores-de-módulos)
  - [Problema: Error al acceder al dashboard desde el navegador](#problema-error-al-acceder-al-dashboard-desde-el-navegador)
  - [Problema: El túnel de Cloudflare no funciona](#problema-el-túnel-de-cloudflare-no-funciona)
  - [Problema: Metadata de estaciones incompleta](#problema-metadata-de-estaciones-incompleta)
  - [Problema: Dashboard muestra datos desactualizados](#problema-dashboard-muestra-datos-desactualizados)
  - [Problema: Warnings de SSL/InsecureRequestWarning](#problema-warnings-de-sslinsecurerequestwarning)
  - [Obtener ayuda adicional](#obtener-ayuda-adicional)

---

Descripción
-----------
Este proyecto procesa resúmenes diarios de estaciones (CSV) y construye un tablero interactivo (Dash) para visualizar intermitencias, inactividades y metadata de las estaciones. Calcula diferencias entre la última actividad registrada y los registros de estaciones activas para detectar interrupciones (por ejemplo, intermitencia nocturna). Consulta una API pública de SAMA para obtener metadata (nombre, coordenadas, municipio, subregión) y puede enriquecerla con un archivo Excel local `estacionesSAMADB.xlsx` si está disponible.

Propósito
--------
- Identificar y reportar eventos de interrupción/intermitencia entre días consecutivos.
- Visualizar en un dashboard (Dash) la cantidad de intermitencias por estación, su localización y detalles por municipio/subregión.
- Facilitar la revisión operativa y la priorización de mantenimiento.

## Autora

- **Maria Cristina Montoya** - Calidad de Datos - **Github:** [@mcml1225](https://github.com/mcml1225)


## Soporte

- **Maria Cristina Montoya** - Calidad de Datos - **Email:** [mmonto37@eafit.edu.co](mailto:mmonto37@eafit.edu.co)
- **Sergio Camilo Garzón** - Desarrollo de Software - **Email:** [scgarzonp@eafit.edu.co](mailto:scgarzonp@eafit.edu.co)

Este proyecto es financiado por la  **Gobernación de Antioquia** (AMVA) y administrado por la **Universidad Eafit**.



Estructura de datos esperada
----------------------------
- Carpeta `Analisis6/` (ya incluida en el repositorio) con archivos CSV con nombres del tipo:
  - `resumen_estaciones_activas__<mes><dia>.csv`
  - `resumen_estaciones_<mes><dia>.csv`

- Opcional: `estacionesSAMADB.xlsx` en la raíz del proyecto para enriquecer metadata de estaciones.

Requisitos del Sistema
----------------------
- **Python 3.8 o superior** (recomendado Python 3.9+)
- Sistema operativo: Linux, macOS o Windows
- Acceso a internet para consultar la API de SAMA (opcional pero recomendado)
- Mínimo 2GB de RAM
- 500MB de espacio en disco

### Verificar versión de Python:
```bash
python --version
# o
python3 --version
```

**Nota:** Si tienes archivos CSV en `Analisis6/` el sistema funcionará sin el archivo `estacionesSAMADB.xlsx`. Este archivo Excel opcional enriquece la información con:
- Nombres completos de estaciones
- Coordenadas geográficas precisas
- Información de municipio y subregión

Sin este archivo, la aplicación consultará únicamente la API pública de SAMA para obtener metadata.

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



Ejecutar el dashboard
---------------------
1. Asegúrate de que la carpeta `Analisis6/` contiene los CSV de entrada (ya está incluida en el repo de ejemplo).
2. (Opcional) Si tienes `estacionesSAMADB.xlsx`, colócalo en la raíz del proyecto para obtener municipio y subregión más precisos.
3. Ejecuta la aplicación Dash:

```bash
python TableroMantenimiento.py
```

// TODO PENDIENTE INCLUIR EL O LOS PUERTOS

4. Abre tu navegador en:

```
http://127.0.0.1:8095
```

### Verificar que la aplicación está corriendo

Una vez ejecutado el comando anterior, deberías ver en la terminal:
- Mensajes de procesamiento de archivos CSV
- Mensaje final: `Dash is running on http://127.0.0.1:8095/`
- Warnings sobre certificados SSL (son normales al consultar la API de SAMA)

### Detener la aplicación

Para detener el servidor Dash:
- Presiona `Ctrl + C` en la terminal donde se está ejecutando

### Ejecutar en segundo plano

Para ejecutar la aplicación en segundo plano:

```bash
nohup python TableroMantenimiento.py > tablero.log 2>&1 &
```

Para detenerla:
```bash
# Encontrar el proceso
ps aux | grep TableroMantenimiento.py

# Detener el proceso (reemplaza PID con el número del proceso)
kill PID
```

Despliegue
----------
Para el despliegue utilizaremos un tunel (cloudflared tunnel) para evitar abrir los puertos, además de otras ventajas que brinda este servicio como protección a ataques DDOS.

## Estándar de Configuración de Túneles

Para mantener una estructura organizada y escalable, se utiliza **un túnel por ambiente** que gestiona todas las aplicaciones de ese ambiente.

### Tabla de Configuración de Túneles y Puertos

| Ambiente | Aplicaciones | Puertos | Archivo de Configuración | Nombre del Túnel | Nombre del Servicio |
|----------|--------------|---------|--------------------------|------------------|---------------------|
| **Producción** | Pronóstico<br>Mantenimiento | `8090`<br>`8095` | `/etc/cloudflared/prod-dash-config.yml` | `prod-tunnel` | `cloudflared-prod-tunnel` |
| **Staging** | Pronóstico<br>Mantenimiento | `8091`<br>`8096` | `/etc/cloudflared/staging-dash-config.yml` | `staging-tunnel` | `cloudflared-staging-tunnel` |

### Asignación de Puertos por Aplicación

| Aplicación | Puerto Producción | Puerto Staging | Dominio Producción | Dominio Staging |
|------------|-------------------|----------------|-------------------|-----------------|
| **Pronóstico** | `8090` | `8091` | `pronosticosdash.online` | `staging-pronostico.pronosticosdash.online` |
| **Mantenimiento** | `8095` | `8096` | `mantenimiento.pronosticosdash.online` | `staging-mantenimiento.pronosticosdash.online` |

### Convenciones de Nomenclatura

**Archivos de Configuración:**
```
/etc/cloudflared/<ambiente>-dash-config.yml
```

**Nombres de Túneles:**
```
<ambiente>-tunnel
```

**Nombres de Servicios systemd:**
```
cloudflared-<ambiente>-tunnel
```

**Dominios:**
- Producción: dominio principal o subdominio sin prefijo
- Staging: prefijo `staging-` antes del subdominio

### Ventajas de este Estándar

- ✅ **Simplicidad:** Solo dos túneles para gestionar (producción y staging)
- ✅ **Centralización:** Todas las aplicaciones de un ambiente en un solo túnel
- ✅ **Economía:** Reduce el número de túneles activos
- ✅ **Fácil gestión:** Un solo servicio systemd por ambiente
- ✅ **Escalabilidad:** Fácil agregar nuevas aplicaciones al mismo túnel

Instalar cloudflared
-------------------
No es una dependencia de Python; cloudflared es un binario independiente que debes instalar en el sistema antes de usar el túnel. Opciones comunes:

### Add Cloudflared's package signing key:

- Debian/Ubuntu:
```bash

sudo mkdir -p --mode=0755 /usr/share/keyrings
curl -fsSL https://pkg.cloudflare.com/cloudflare-public-v2.gpg | sudo tee /usr/share/keyrings/cloudflare-public-v2.gpg >/dev/null
```

### Add Cloudflare's apt repo to your apt repositories

```bash
echo "deb [signed-by=/usr/share/keyrings/cloudflare-public-v2.gpg] https://pkg.cloudflare.com/cloudflared any main" | sudo tee /etc/apt/sources.list.d/cloudflared.list
```

### Update repositories and install clouflared:
```bash
sudo apt-get update && sudo apt-get install cloudflared
```

Para otros sistemas operativos o distribuciones de linux consultar en el sitio de cloudflared
[Create a cloudflared tunnel](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/local-management/create-local-tunnel/)


### Verifica la instalación:
```bash
cloudflared --version
```

### Autenticación en cloudflared
```bash
cloudflared tunnel login
```
Esto genera un link de acceso donde se hace el login desde el navegador

### Crear un tunel y nombrarlo

Siguiendo el estándar establecido, crea los dos túneles necesarios (uno por ambiente):

```bash
# Túnel de Producción
cloudflared tunnel create prod-tunnel

# Túnel de Staging
cloudflared tunnel create staging-tunnel
```

Esto generará un UUID y un archivo de credenciales en `~/.cloudflared/` para cada túnel. Guarda estos UUIDs, los necesitarás para la configuración.

### Configurar tunel para que apunte al servicio local

Una vez instalado cloudflared se crea una carpeta para su configuración, en el caso de **Debian** y **Ubuntu** se encuentra en **/etc/cloudflared**. 

Allí creamos los archivos de configuración según el estándar establecido.

#### Configuración de Producción

Crear el archivo `/etc/cloudflared/prod-dash-config.yml`:

```yml
tunnel: <PROD_TUNNEL_ID>
credentials-file: /home/scgarzonp/.cloudflared/<PROD_TUNNEL_ID>.json

ingress:
  - hostname: pronosticosdash.online
    service: http://127.0.0.1:8090
  - hostname: mantenimiento.pronosticosdash.online
    service: http://127.0.0.1:8095
  - service: http_status:404
```

#### Configuración de Staging

Crear el archivo `/etc/cloudflared/staging-dash-config.yml`:

```yml
tunnel: <STAGING_TUNNEL_ID>
credentials-file: /home/scgarzonp/.cloudflared/<STAGING_TUNNEL_ID>.json

ingress:
  - hostname: staging-pronostico.pronosticosdash.online
    service: http://127.0.0.1:8091
  - hostname: staging-mantenimiento.pronosticosdash.online
    service: http://127.0.0.1:8096
  - service: http_status:404
```

**Nota importante:** Reemplaza:
- `<PROD_TUNNEL_ID>` con el UUID del túnel de producción (generado al crear `prod-tunnel`)
- `<STAGING_TUNNEL_ID>` con el UUID del túnel de staging (generado al crear `staging-tunnel`)
- `/home/scgarzonp/` con la ruta de tu usuario si es diferente
- Los dominios `pronosticosdash.online` con tu dominio real

**Estructura de la configuración:**
- Cada entrada en `ingress` asocia un hostname (dominio/subdominio) con un servicio local (puerto)
- El orden importa: cloudflared evaluará las reglas de arriba hacia abajo
- La última regla (`http_status:404`) es obligatoria como fallback

### Enrutar el tráfico sin un dominio
Una forma de probar el funcionamiento del tunel de cloudflare o establecerlo si no tienes un dominio es con el siguiente comando

```bash
cloudflared tunnel --url http://localhost:<PORT>
```

De esta manera se establece un tunel a una url aleatoria generada por cloudflared y luego probar que esta conexión quedo lista.

En la consola se presentará la URL aleatoria similar a la siguiente:

```bash
https://beach-templates-nights-general.trycloudflare.com
```


### Enrutar el tráfico con dominio

Ahora asigna registros __CNAME__ que dirigen el trafico a los túneles correspondientes:

```bash
# Dominios de Producción
cloudflared tunnel route dns prod-tunnel pronosticosdash.online
cloudflared tunnel route dns prod-tunnel mantenimiento.pronosticosdash.online

# Dominios de Staging
cloudflared tunnel route dns staging-tunnel staging-pronostico.pronosticosdash.online
cloudflared tunnel route dns staging-tunnel staging-mantenimiento.pronosticosdash.online
```

Estos comandos crearán automáticamente registros CNAME en tu DNS de Cloudflare apuntando a los túneles correspondientes.

## Run the tunnel

Para ejecutar un túnel manualmente y verificar su funcionamiento:

```bash
# Túnel de Producción
cloudflared tunnel --config /etc/cloudflared/prod-dash-config.yml run prod-tunnel

# Túnel de Staging
cloudflared tunnel --config /etc/cloudflared/staging-dash-config.yml run staging-tunnel
```

Esto es útil para probar la configuración antes de configurar los servicios systemd permanentes.

### Configurar Túneles como Servicios Systemd

Es importante que el servicio del tunel de cloudflared se instale como un servicio. Hay dos métodos:

### Método 1: Instalación automática (Recomendado para configuraciones simples)

Este es el método estándar según la documentación oficial:

```bash
cloudflared service install

systemctl start cloudflared

systemctl status cloudflared
```

**Comandos útiles para este método:**
```bash
# Reiniciar el servicio
sudo systemctl restart cloudflared

# Detener el servicio
sudo systemctl stop cloudflared

# Ver logs
sudo journalctl -u cloudflared -f
```

### Método 2: Configuración manual (Recomendado para control completo)

Esta alternativa permite tener control total sobre los túneles y mejor gestión de permisos. **Este es el método recomendado para seguir el estándar establecido.**

#### Servicio de Producción

Crear el archivo `/etc/systemd/system/cloudflared-prod-tunnel.service`:

```ini
[Unit]
Description=Cloudflare Tunnel - Producción (Pronóstico y Mantenimiento)
After=network.target

[Service]
Type=simple
User=scgarzonp
ExecStart=/usr/bin/cloudflared tunnel --config /etc/cloudflared/prod-dash-config.yml run prod-tunnel
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

#### Servicio de Staging

Crear el archivo `/etc/systemd/system/cloudflared-staging-tunnel.service`:

```ini
[Unit]
Description=Cloudflare Tunnel - Staging (Pronóstico y Mantenimiento)
After=network.target

[Service]
Type=simple
User=scgarzonp
ExecStart=/usr/bin/cloudflared tunnel --config /etc/cloudflared/staging-dash-config.yml run staging-tunnel
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Nota:** 
- Reemplaza `scgarzonp` con tu usuario del sistema si es diferente
- Se recomienda usar un usuario diferente al root por seguridad
- Asegúrate de que el usuario tenga permisos de lectura sobre los archivos de configuración y credenciales

#### Habilitar y Gestionar los Servicios

Para cada túnel creado, habilita e inicia el servicio:

```bash
# Recargar la configuración de systemd
sudo systemctl daemon-reload

# Túnel de Producción
sudo systemctl enable --now cloudflared-prod-tunnel

# Túnel de Staging
sudo systemctl enable --now cloudflared-staging-tunnel
```

#### Comandos de Gestión de Servicios

**Gestión del Túnel de Producción:**

```bash
# Ver el estado
sudo systemctl status cloudflared-prod-tunnel

# Reiniciar el servicio
sudo systemctl restart cloudflared-prod-tunnel

# Detener el servicio
sudo systemctl stop cloudflared-prod-tunnel

# Iniciar el servicio
sudo systemctl start cloudflared-prod-tunnel

# Ver logs en tiempo real
sudo journalctl -u cloudflared-prod-tunnel -f

# Ver últimas 50 líneas de logs
sudo journalctl -u cloudflared-prod-tunnel -n 50
```

**Gestión del Túnel de Staging:**

```bash
# Ver el estado
sudo systemctl status cloudflared-staging-tunnel

# Reiniciar el servicio
sudo systemctl restart cloudflared-staging-tunnel

# Detener el servicio
sudo systemctl stop cloudflared-staging-tunnel

# Iniciar el servicio
sudo systemctl start cloudflared-staging-tunnel

# Ver logs en tiempo real
sudo journalctl -u cloudflared-staging-tunnel -f

# Ver últimas 50 líneas de logs
sudo journalctl -u cloudflared-staging-tunnel -n 50
```

#### Comandos para Gestionar Ambos Túneles

```bash
# Ver estado de ambos túneles
sudo systemctl status cloudflared-*-tunnel

# Reiniciar ambos túneles
sudo systemctl restart cloudflared-prod-tunnel cloudflared-staging-tunnel

# Detener ambos túneles
sudo systemctl stop cloudflared-prod-tunnel cloudflared-staging-tunnel

# Ver logs de ambos en tiempo real (en terminales separadas)
sudo journalctl -u cloudflared-prod-tunnel -u cloudflared-staging-tunnel -f
```

#### Modificar Configuración de un Túnel

Si necesitas modificar la configuración de un túnel:

```bash
# 1. Editar el archivo de configuración
sudo nano /etc/cloudflared/prod-dash-config.yml
# o
sudo nano /etc/cloudflared/staging-dash-config.yml

# 2. Recargar y reiniciar el servicio
sudo systemctl daemon-reload
sudo systemctl restart cloudflared-prod-tunnel
# o
sudo systemctl restart cloudflared-staging-tunnel

# 3. Verificar que funciona correctamente
sudo systemctl status cloudflared-prod-tunnel
# o
sudo systemctl status cloudflared-staging-tunnel
```

### Ventajas del método manual:

- Se pueden tener múltiples túneles de manera sencilla (producción, staging, desarrollo)
- Mayor control sobre permisos de usuario (evita usar root)
- Configuración personalizable por túnel

Se puede establecer un usuario que controle los permisos y evitar de que se den permisos sudo en caso de que por una vulnerabilidad se ingrese por dicho tunel

https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/local-management/as-a-service/linux/

https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/local-management/create-local-tunnel/

https://developers.cloudflare.com/containers/get-started/


Notas:
- Asegúrate de que el binario esté en tu PATH.
- No se requiere instalar nada adicional en Python para usar el túnel, solo el propio cloudflared.
- Opcional: configura un servicio systemd o el equivalente en tu SO para ejecutar el túnel en segundo plano.




Actualización de Datos
---------------------

Para agregar nuevos datos al dashboard:

1. **Formato de archivos CSV requerido:**
   - Coloca los nuevos archivos CSV en la carpeta `Analisis6/`
   - Nomenclatura requerida:
     - `resumen_estaciones_activas__<mes><dia>.csv` (ejemplo: `resumen_estaciones_activas__november18.csv`)
     - `resumen_estaciones_<mes><dia>.csv` (ejemplo: `resumen_estaciones_november18.csv`)
   - El mes debe estar en inglés y en minúsculas
   - El día debe ser de 2 dígitos (01, 02, ..., 31)

2. **Columnas requeridas en los CSV:**
   - `resumen_estaciones_activas__*.csv`: debe contener columnas de código de estación y timestamp de última actividad
   - `resumen_estaciones_*.csv`: debe contener estado de las estaciones

3. **Actualizar el dashboard:**
   - Simplemente reinicia la aplicación después de agregar los nuevos archivos
   - Los cambios se reflejarán automáticamente al cargar

```bash
# Si está corriendo en terminal, detén con Ctrl+C y vuelve a ejecutar
python TableroMantenimiento.py

# Si está corriendo en segundo plano, encuentra y detén el proceso
ps aux | grep TableroMantenimiento.py
kill <PID>
python TableroMantenimiento.py
```

Variables de Entorno y Configuración
-----------------------------------

La aplicación usa configuraciones directas en el código. Las principales configuraciones son:

- **Puerto del servidor:** 8095 (definido en `TableroMantenimiento.py`)
- **Carpeta de datos:** `./Analisis6` (modificable en el código)
- **API de SAMA:** `https://sigran.antioquia.gov.co/api/v1/estaciones/`
- **Archivo Excel opcional:** `estacionesSAMADB.xlsx` (debe estar en la raíz del proyecto)

### Para cambiar el puerto:

Edita el archivo `TableroMantenimiento.py` y busca la línea al final:
```python
app.run_server(debug=False, host='0.0.0.0', port=8095)
```

Cambia `8095` por el puerto deseado y reinicia la aplicación.

Comportamiento y Notas Técnicas
-------------------------------
- El script busca archivos CSV en `Analisis6/` con nombres que emparejen las convenciones esperadas. Si las columnas clave faltan en un CSV, ese día se saltará con una advertencia.
- Se realizan llamadas HTTP a `https://sigran.antioquia.gov.co/api/v1/estaciones/<tipo>_<code>/` para obtener metadata. Si estás en una red sin acceso a esa API, la metadata será parcial.
- El proceso es tolerante a separadores (coma/;), y a errores de parseo de fecha — los registros que no se puedan parsear se omiten con advertencias impresas en consola.
- Los warnings de SSL (`InsecureRequestWarning`) son normales y se pueden ignorar. La aplicación los suprime automáticamente.

Troubleshooting (Solución de Problemas)
---------------------------------------

### Problema: No hay archivos CSV en Analisis6/

**Síntoma:** Error al iniciar o dashboard vacío

**Solución:**
1. Verifica que la carpeta `Analisis6/` existe en la raíz del proyecto
2. Asegúrate de que hay archivos CSV con la nomenclatura correcta
3. Los archivos deben venir en pares (activas y estados) con el mismo sufijo de fecha

```bash
# Listar archivos en la carpeta
ls -la Analisis6/

# Deberías ver pares como:
# resumen_estaciones_activas__november11.csv
# resumen_estaciones_november11.csv
```

### Problema: La aplicación no inicia o muestra errores de módulos

**Síntoma:** `ModuleNotFoundError: No module named 'dash'` o similar

**Solución:**
```bash
# Verifica que el entorno virtual está activado
source .venv/bin/activate  # Linux/Mac
# o
.venv\Scripts\activate  # Windows

# Reinstala las dependencias
pip install -r requirements.txt

# Verifica las instalaciones
pip list
```

### Problema: Error al acceder al dashboard desde el navegador

**Síntoma:** "No se puede acceder a este sitio" o "Connection refused"

**Solución:**
1. Verifica que la aplicación está corriendo:
   ```bash
   ps aux | grep TableroMantenimiento.py
   ```

2. Verifica que el puerto 8095 está escuchando:
   ```bash
   netstat -tuln | grep 8095
   # o
   lsof -i :8095
   ```

3. Intenta acceder desde:
   - `http://127.0.0.1:8095`
   - `http://localhost:8095`
   - `http://<tu-ip-local>:8095`

### Problema: El túnel de Cloudflare no funciona

**Síntoma:** No se puede acceder desde internet o el servicio no inicia

**Solución:**
```bash
# Verifica el estado del servicio (método automático)
sudo systemctl status cloudflared

# O para método manual
sudo systemctl status cloudflared-tunnel

# Ver logs detallados
sudo journalctl -u cloudflared -n 50
# o
sudo journalctl -u cloudflared-tunnel -n 50

# Verifica la configuración
cat /etc/cloudflared/config.yml

# Prueba el túnel manualmente
cloudflared tunnel --config /etc/cloudflared/config.yml run
```

### Problema: Metadata de estaciones incompleta

**Síntoma:** Dashboard muestra estaciones sin nombre o ubicación

**Solución:**
1. Verifica conexión a internet (la app consulta la API de SAMA)
2. Opcionalmente, agrega el archivo `estacionesSAMADB.xlsx` en la raíz del proyecto para metadata local
3. El archivo Excel debe contener columnas: código de estación, nombre, coordenadas, municipio, subregión

### Problema: Dashboard muestra datos desactualizados

**Síntoma:** No aparecen los últimos días procesados

**Solución:**
1. Verifica que los archivos CSV nuevos están en `Analisis6/`
2. Verifica la nomenclatura de los archivos
3. Reinicia la aplicación para recargar los datos

### Problema: Warnings de SSL/InsecureRequestWarning

**Síntoma:** Muchos warnings en consola sobre certificados SSL

**Solución:** Estos warnings son normales y esperados. La aplicación ya los suprime automáticamente. No afectan el funcionamiento.

### Obtener ayuda adicional

Si los problemas persisten:

1. Revisa los logs de la aplicación
2. Ejecuta con modo debug activado (edita `debug=True` en `TableroMantenimiento.py`)
3. Contacta al equipo de soporte (ver sección Soporte arriba)
4. Incluye en tu reporte:
   - Versión de Python (`python --version`)
   - Sistema operativo
   - Mensaje de error completo
   - Contenido del directorio `Analisis6/`




