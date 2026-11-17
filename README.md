# Campana · horarios de misa

Web estática que dice **cuál es la misa más cercana** y **cuál empieza antes** según dónde estés y la hora que sea, en Sotogrande y 50 km alrededor (Cádiz y Málaga). Mismo diseño que Turno, en burdeos cardenalicio y oro.

- Pestañas: **Cerca de mí** (dos tarjetas, lista y mapa), **Esta semana**, **Favoritas** y **Fuentes**.
- Al entrar pide tu ubicación; si no la das, muestra Sotogrande. La posición no sale del dispositivo.
- Favoritas: se guardan en el navegador solo si aceptas guardar preferencias.

## Cómo funciona

```
GitHub Actions (cada día)           Cloudflare Pages
pipeline/build.py  ──►  site/misas.js  ──commit──►  publica site/ (sin build)
```

1. `pipeline/fetch_cadiz.py` y `fetch_malaga.py` leen las fichas oficiales de cada parroquia (Obispado de Cádiz y Ceuta, Diócesis de Málaga).
2. `pipeline/static/locales.json` trae los horarios curados de Sotogrande, Guadiaro, Pueblo Nuevo y Torreguadiaro (parroquia, vía holasoto.com). Mandan sobre las fichas del Obispado.
3. `pipeline/geocode.py` obtiene las coordenadas con Nominatim y las guarda en `pipeline/static/geo_cache.json` (solo consulta las iglesias nuevas).
4. `pipeline/build.py` filtra a 50 km de Sotogrande y escribe `site/misas.js`. `pipeline/check.py` valida antes de publicar.
5. El navegador calcula todo lo demás (próxima misa, tiempo de llegada, semana) a partir de las reglas semanales, así que los datos no caducan cada día.

## Puesta en marcha

1. Crear el repositorio vacío `juanarenduelesb-byte/campana` en GitHub y subir este código.
2. Cloudflare Pages → conectar el repositorio. **Comando de compilación:** vacío. **Directorio de salida:** `site`. **Rama:** `main`.
3. En GitHub → Actions, lanzar «Actualizar horarios de misa» una vez a mano para comprobar que funciona.

Probar en local: `cd site && python3 -m http.server` y abrir `http://localhost:8000`.

## Cosas que conviene saber

- Los horarios son **orientativos**. Los de Málaga son texto libre que se interpreta automáticamente; la ficha muestra siempre el texto original.
- No distingue vísperas de festivo (solo los sábados), ni Semana Santa, Navidad o festivos locales. Los festivos nacionales fijos sí cuentan como domingo.
- Ceuta no está incluida a propósito. Gibraltar, pendiente.
- El tiempo en coche es una estimación por distancia en línea recta, sin tráfico.
- `robots.txt` y las cabeceras piden no indexar (como Turno). Para que salga en Google, cambiar `robots.txt`, `X-Robots-Tag` en `site/_headers` y la etiqueta `robots` de `index.html`.
- Un proyecto de **esclusa**.


## Cobertura por diócesis (actualizado)

Campana ya no se limita a Sotogrande: cada diócesis es una fuente independiente en `pipeline/fuentes/<diocesis>.py`
y solo se usan las webs oficiales de las diócesis. `pipeline/build.py` genera un archivo por diócesis (`site/data/<id>.js`)
y un índice de cobertura (`site/data/indice.js`); la web carga solo las diócesis cercanas a tu ubicación.

- Hoy: Cádiz y Ceuta, Málaga y Sevilla. Pendientes: ver `pipeline/static/pendientes.json`.
- Para añadir una diócesis: crea `pipeline/fuentes/<id>.py` con `run() -> (lista_normalizada, fallos)`, añádela a `FUENTES` en `build.py` y prueba con `python3 pipeline/build.py <id>`.
- Si una diócesis falla o devuelve menos del 60 % de lo anterior, se conservan sus datos anteriores y el índice la marca como «antiguo».
- Sevilla guarda una caché (`pipeline/static/cache_sevilla.json`) para no volver a descargar las fichas que no han cambiado.
