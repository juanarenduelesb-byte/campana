# Hoy hay misa · horarios de misa

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

- Hoy: Cádiz y Ceuta, Málaga, Sevilla, Madrid, Alcalá de Henares, Barcelona, Granada, Valladolid, Orihuela-Alicante, Salamanca, Pamplona y Tudela, y Tenerife. Pendientes: ver `pipeline/static/pendientes.json`.
- Para añadir una diócesis: crea `pipeline/fuentes/<id>.py` con `run() -> (lista_normalizada, fallos)`, añádela a `FUENTES` en `build.py` y prueba con `python3 pipeline/build.py <id>`.
- Si una diócesis falla o devuelve menos del 60 % de lo anterior, se conservan sus datos anteriores y el índice la marca como «antiguo».
- Sevilla guarda una caché (`pipeline/static/cache_sevilla.json`) para no volver a descargar las fichas que no han cambiado.

### Formatos que entiende el generador

- Tablas por día (Sevilla, Valladolid, Salamanca, Tenerife), servicios de datos de la propia diócesis (Madrid, Granada) y hojas de cálculo (Pamplona, necesita `openpyxl`).
- Texto libre en español y catalán (`pipeline/texto.py`): «Lunes a sábado: 19h», bloques LABORABLES / VÍSPERAS / FESTIVOS, «Feiners: dimecres i divendres 20:00h».
- Las coordenadas salen de la propia web cuando las publica; si no, de OpenStreetMap (Nominatim, 1 consulta por segundo, con caché en `pipeline/static/geo_cache.json`). Si el resultado cae fuera de la zona de la diócesis, se usa la localidad y la ficha lo marca como ubicación aproximada.
- Diócesis revisadas sin horarios legibles todavía: Burgos (no publica la localidad de cada misa), Getafe y Jaén (solo directorio, sin horarios), Cartagena (buscador en mantenimiento), Huelva (PDF), Ibiza (solo la ciudad).

### Resto de España: OpenStreetMap

`pipeline/osm.py` descarga de Overpass todas las iglesias católicas de España (unas decenas de miles) y genera `site/data/osm-NN.js` por provincia,
descartando las que ya vienen de una fuente oficial. Si la iglesia tiene la etiqueta `service_times`, se interpreta como horario colaborativo y la ficha lo marca como no oficial.
Las demás muestran un enlace de búsqueda a misas.org. **Misas.org no se descarga**: su aviso legal prohíbe extraer su información sistemáticamente.
La capa se rehace en la acción diaria y se puede lanzar sola con el flujo «Iglesias de OpenStreetMap».
