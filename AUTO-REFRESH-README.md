# Dashboard Auto-Refresh - Mantenimiento SAMA

## ¿Por qué el dashboard no se actualiza automáticamente?

El dashboard se ejecuta en un contenedor Docker con **Gunicorn usando 4 workers**. Cada worker tiene su **propia memoria** y no comparte datos con los demás.

### Problema

Cuando el API devuelve datos nuevos (por ejemplo, sp_138 vuelve a estar activa), el dashboard **NO** refleja estos cambios automáticamente porque:

1. Los datos se cargan **una sola vez** cuando el contenedor inicia
2. Cada worker de Gunicorn mantiene su propia copia de los datos
3. No hay sincronización automática entre workers

## Soluciones

### ✅ Opción 1: Reiniciar el contenedor (Recomendado)

La forma más confiable de actualizar todos los datos:

```bash
# Usar el script proporcionado
./refresh-dashboard.sh

# O manualmente
docker compose restart mantenimiento
```

**Tiempo de reinicio:** ~10-15 segundos

### ✅ Opción 2: Configurar reinicio automático con Cron

Crea un cronjob para reiniciar el contenedor diariamente:

```bash
# Editar crontab
crontab -e

# Agregar esta línea para reiniciar a las 6 AM todos los días
0 6 * * * /home/evalenci/Projects/dashboards/refresh-dashboard.sh >> /var/log/dashboard-refresh.log 2>&1
```

### Opción 3: Usar solo 1 worker (No recomendado para producción)

Modificar `Dockerfile`:

```dockerfile
# Cambiar esta línea:
ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "TableroMantenimiento:server"]
```

**Desventaja:** Menor capacidad para múltiples usuarios simultáneos.

## APScheduler Incluido

El código ahora incluye APScheduler que **intenta** refrescar datos cada 30 minutos, pero solo funciona dentro de un worker individual. 

**Limitación:** Los otros 3 workers seguirán mostrando datos antiguos.

## Recomendación Final

**Para asegurar datos actualizados:**
1. Reinicia el contenedor manualmente cuando lo necesites
2. O configura un cronjob para reinicio automático diario/cada 6 horas

