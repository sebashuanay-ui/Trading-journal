# Trading-journal · Bitácora MNQ

Diario de trading para Micro E-mini Nasdaq-100 (MNQ). Registras tus trades cerrados, ves el gráfico de velas de MNQ de ese momento, y la página calcula tus métricas: win rate, PnL, drawdown, calendario, análisis por hora y día, más un diario personal y el precio de MNQ casi en vivo.

## Cómo funciona

- `index.html`: la página completa (sin servidor, sin dependencias que instalar).
- **Tus datos** (trades, diario, ajustes y fotos de los trades) se guardan **solo en tu navegador** (localStorage e IndexedDB). Las fotos se comprimen a 1600 px y se pueden pegar con Ctrl+V. No se suben a GitHub. Usa *Ajustes y datos → Exportar copia* de vez en cuando.
- **Precios**: la carpeta `data/` guarda velas de MNQ (contrato continuo `MNQ=F` de Yahoo Finance): 1 minuto, 5 minutos y 1 hora.
- **Workflows** (`.github/workflows/`):
  - `deploy.yml`: cada 5 minutos en horario de mercado descarga el precio actual y vuelve a publicar el sitio. No hace commits. GitHub puede retrasar las tareas programadas unos minutos, así que el precio llega con 5 a 15 minutos de retraso.
  - `live.yml`: un trabajo de 6 minutos que descarga el precio cada minuto y lo publica en la rama `live` (un único commit reescrito). La página lo lee por la API de GitHub. Si el mercado está cerrado no hace nada. Lo dispara un **cron externo** (cron-job.org) cada 5 minutos llamando a la API de GitHub, con el programador de GitHub como respaldo cada 15 minutos. Ver *Cron externo* abajo.
  - `archive.yml`: cada día hábil después del cierre guarda las últimas sesiones en `data/` (un commit al día).

## Activar GitHub Pages (una sola vez)

1. En el repositorio: **Settings → Pages**.
2. En **Build and deployment → Source** elige **GitHub Actions**.
3. Ve a **Actions → Publicar sitio → Run workflow** para la primera publicación.
4. La dirección queda en `https://<tu-usuario>.github.io/Trading-journal/`.

## Ejecutar a mano

```bash
pip install -r requirements.txt
python scripts/build_site.py   # arma _site/ con el precio actual
python scripts/update_data.py  # archiva las últimas sesiones en data/
```

## Límites

- **El precio de MNQ llega con ~10 minutos de retraso**: Yahoo publica los futuros del CME así. Refrescar más seguido no lo acerca al real. Para tiempo real, la pestaña *En vivo* incluye el gráfico de TradingView del CFD Nasdaq 100 (solo para mirar).
- Las **sesiones** se definen en hora de Nueva York: Asia 18:00–02:59, Londres 03:00–08:29, Nueva York 08:30–16:59, pausa 17:00–17:59.
- El contrato continuo cambia de vencimiento cada trimestre; puede haber diferencias de unos ticks con tu plataforma.
- Las horas de mercado del cron están pensadas para horario de verano de Nueva York; en invierno cubre 07:00–17:59 ET.
- No hay sincronización entre dispositivos: cada navegador guarda sus propios datos.

## Cron externo (disparo puntual del precio en vivo)

El programador (`schedule`) de GitHub Actions es de mejor esfuerzo y a veces se retrasa. Para que el precio se publique puntualmente, un servicio gratuito como [cron-job.org](https://cron-job.org) llama cada 5 minutos a la API de GitHub.

1. **Crea un token** en GitHub: *Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token*.
   - Repository access: **Only select repositories → Trading-journal**.
   - Repository permissions: **Actions → Read and write** (Metadata queda en solo lectura).
   - Elige la expiración más larga y copia el token (empieza con `github_pat_`). Guárdalo solo en el servicio de cron; nunca en el repo ni en un chat.
2. **Crea la tarea en cron-job.org** (*Create cronjob*):
   - URL: `https://api.github.com/repos/sebashuanay-ui/Trading-journal/actions/workflows/live.yml/dispatches`
   - Zona horaria: UTC. Horario: cada 5 minutos, de domingo a viernes.
   - *Advanced* → Request method: **POST**. Request body: `{"ref":"main"}`
   - Headers: `Authorization: Bearer TU_TOKEN`, `Accept: application/vnd.github+json`, `X-GitHub-Api-Version: 2022-11-28`, `Content-Type: application/json`
   - Activa las notificaciones de fallo. La respuesta correcta es **204**.
3. En *Actions → Precio en vivo* deberían aparecer ejecuciones con el evento `workflow_dispatch` cada 5 minutos.

Si el token vence o se revoca, la tarea empieza a recibir 401: renuévalo. Mientras tanto el respaldo de GitHub sigue publicando cada 15 minutos.
