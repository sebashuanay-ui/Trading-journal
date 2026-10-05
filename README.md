# Trading-journal · Bitácora MNQ

Diario de trading para Micro E-mini Nasdaq-100 (MNQ). Registras tus trades cerrados, ves el gráfico de velas de MNQ de ese momento, y la página calcula tus métricas: win rate, PnL, drawdown, calendario, análisis por hora y día, más un diario personal y el precio de MNQ casi en vivo.

## Cómo funciona

- `index.html`: la página completa (sin servidor, sin dependencias que instalar).
- **Tus datos** (trades, diario, ajustes) se guardan **solo en tu navegador** (localStorage). No se suben a GitHub. Usa *Ajustes y datos → Exportar copia* de vez en cuando.
- **Precios**: la carpeta `data/` guarda velas de MNQ (contrato continuo `MNQ=F` de Yahoo Finance): 1 minuto, 5 minutos y 1 hora.
- **Workflows** (`.github/workflows/`):
  - `deploy.yml`: cada 5 minutos en horario de mercado descarga el precio actual y vuelve a publicar el sitio. No hace commits. GitHub puede retrasar las tareas programadas unos minutos, así que el precio llega con 5 a 15 minutos de retraso.
  - `live.yml`: cada 5 minutos arranca un trabajo que, durante ~5 minutos, descarga el precio cada minuto y lo publica en la rama `live` (un único commit reescrito). La página lo lee desde `raw.githubusercontent.com`. Si el mercado está cerrado no hace nada.
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
