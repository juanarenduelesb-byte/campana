"""Genera site/misas.js con las iglesias a menos de 50 km de Sotogrande y sus horarios.

Fuentes:
  - Obispado de Cádiz y Ceuta (fichas oficiales de cada parroquia)
  - Diócesis de Málaga (fichas oficiales)
  - Iglesias de Sotogrande y Guadiaro: parroquia, vía holasoto.com (pipeline/static/locales.json)
Si una fuente falla, se conservan los datos de la última ejecución (site/misas.js)."""
import json, math, os, re, sys, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_cadiz, fetch_malaga, geocode
from temporadas import temporada_verano
from misas_lib import season_empty

AQUI = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(AQUI, '..', 'site')
CENTRO = (36.2825, -5.2945)   # Sotogrande
RADIO_KM = 50
ARCIP_CADIZ = ('san roque', 'linea', 'línea', 'algeciras')

def km(a, b, c, d):
    r = math.pi / 180
    h = math.sin((c - a) * r / 2) ** 2 + math.cos(a * r) * math.cos(c * r) * math.sin((d - b) * r / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))

PEQ = {'de', 'del', 'la', 'las', 'los', 'el', 'y', 'e', 'en', 'a'}
ACENTOS = {'Linea': 'Línea', 'Concepcion': 'Concepción', 'Martin': 'Martín', 'Estacion': 'Estación', 'Espiritu': 'Espíritu', 'Pio': 'Pío',
           'Andalucia': 'Andalucía', 'Maria': 'María', 'Jose': 'José', 'Agustin': 'Agustín', 'Garcia': 'García', 'Santisima': 'Santísima',
           'Angel': 'Ángel', 'Roque': 'Roque', 'Fra.': 'Frontera', 'Ildefonso': 'Ildefonso', 'Alcantara': 'Alcántara', 'Rocio': 'Rocío',
           'Ojen': 'Ojén', 'Benahavis': 'Benahavís', 'Istan': 'Istán', 'Gaucin': 'Gaucín', 'Mayorga': 'Mayorga', 'Santisimo': 'Santísimo'}
def titulo(s):
    s = re.sub(r'\s+', ' ', s or '').strip().rstrip('.')
    s = re.sub(r'\s+-\s*', ' – ', s)
    out = []
    for i, w in enumerate(s.split(' ')):
        lw = w.lower()
        if i > 0 and lw in PEQ: out.append(lw); continue
        w2 = w[:1].upper() + w[1:].lower() if w.isupper() or w.islower() or w == w.title() else w
        out.append(ACENTOS.get(w2, w2))
    return ' '.join(out)

def calle_num(dirs):
    """['Cl Romero De Figueroa, Nº 2', ...] -> ('Calle Romero de Figueroa', '2')"""
    s = dirs[0] if dirs else ''
    num = ''
    m = re.search(r',?\s*N[ºo°]\.?\s*(\d+)', s)
    if m: num = m.group(1)
    return geocode.limpia_calle(s), num

def norm_cadiz(d):
    if not any(k in d['arciprestazgo'].lower() for k in ARCIP_CADIZ): return None
    dirs = d['dir']
    if len(dirs) < 4: return None
    calle, num = calle_num(dirs)
    loc = titulo(dirs[-3]).replace('Castellar de la Frontera', 'Castellar de la Frontera')
    cp = dirs[-1]
    slug = d['url'].rstrip('/').split('/')[-1]
    obs = d['obs']
    return {'id': slug, 'nombre': titulo(d['nombre']), 'localidad': loc, 'calle': calle, 'num': num, 'cp': cp, 'prov': 'Cádiz',
            'tel': d.get('tel', ''), 'parroco': d.get('parroco', ''), 'rol': d.get('rol', ''), 'arciprestazgo': titulo(d['arciprestazgo']),
            'diocesis': 'Cádiz y Ceuta', 'url': d['url'], 'h': d['h'], 'obs': obs, 'texto': '', 'verano': temporada_verano(obs),
            'fuente': 'Obispado de Cádiz y Ceuta', 'actualizado': d.get('modificado', ''), 'idiomas': ['es']}

def norm_malaga(d):
    dirs = d['dir']
    if not dirs: return None
    calle = geocode.limpia_calle(re.sub(r'^(c/\.?|c\.|pza\.?|pl\.?|avda\.?)\s*', lambda m: {'c/': 'Calle ', 'c/.': 'Calle ', 'c.': 'Calle ', 'pza': 'Plaza ', 'pza.': 'Plaza ', 'pl': 'Plaza ', 'pl.': 'Plaza ', 'avda': 'Avenida ', 'avda.': 'Avenida '}.get(m.group(1).lower(), '') , dirs[0], flags=re.I))
    num = ''
    m = re.search(r'\b(?:n[ºo°]\s*)?(\d{1,3})\b\s*$', dirs[0])
    if m: num = m.group(1); calle = re.sub(r',?\s*(?:n[ºo°]\s*)?\d{1,3}\s*$', '', calle).strip()
    cpm = re.search(r'\b(\d{5})\b', dirs[-1]); cp = cpm.group(1) if cpm else ''
    loc = re.sub(r'^\d{5}\s*', '', dirs[-1]).strip() or d['localidad']
    loc = re.sub(r'\s*\(Estepona\)', '', loc)
    return {'id': 'm' + d['url'].rstrip('/').split('/')[-2], 'nombre': titulo(d['nombre']), 'localidad': loc, 'calle': calle, 'num': num, 'cp': cp,
            'prov': 'Málaga', 'tel': d.get('tel', ''), 'parroco': d.get('parroco', ''), 'rol': d.get('rol', ''),
            'arciprestazgo': d.get('arciprestazgo', ''), 'diocesis': 'Málaga', 'url': d['url'], 'h': d['h'], 'obs': '', 'texto': d.get('texto', ''),
            'verano': temporada_verano(d.get('obs', '') + ' ' + d.get('texto', '')), 'fuente': 'Diócesis de Málaga', 'actualizado': '', 'idiomas': ['es'], 'obs_raw': d.get('obs', '')}

def cargar_previo():
    try:
        t = open(os.path.join(SITE, 'misas.js'), encoding='utf8').read()
        return json.loads(t[t.index('=') + 1:].rstrip(';\n'))
    except Exception:
        return None

def main():
    fallos = []
    cad, f1 = fetch_cadiz.run()
    mal, f2 = fetch_malaga.run()
    fallos += [u for u in f1 + f2]
    previo = cargar_previo()
    if len(cad) < 40 or len(mal) < 20:
        print('Fuentes insuficientes (Cádiz %d, Málaga %d).' % (len(cad), len(mal)))
        print('Se conservan los datos anteriores (si los hay); el trabajo falla para que GitHub avise.'); return 1
    iglesias = [x for x in (norm_cadiz(d) for d in cad) if x] + [x for x in (norm_malaga(d) for d in mal) if x]
    # iglesias de Sotogrande (parroquia)
    loc = json.load(open(os.path.join(AQUI, 'static', 'locales.json'), encoding='utf8'))
    reemplazos = {i.get('reemplaza') for i in loc['iglesias']}
    iglesias = [x for x in iglesias if x['id'] not in reemplazos]
    for l in loc['iglesias']:
        h = l['h']; h.setdefault('ver', h['inv'])
        iglesias.append({**{k: l.get(k, '') for k in ('id', 'nombre', 'localidad', 'calle', 'num', 'cp', 'tel', 'arciprestazgo', 'diocesis', 'obs')},
                         'prov': 'Cádiz', 'parroco': l.get('parroco', ''), 'rol': '', 'url': loc['fuente_url'], 'h': h, 'texto': '', 'verano': [6, 1, 9, 30],
                         'fuente': 'Parroquia de Guadiaro (holasoto.com)', 'actualizado': loc['verificado'], 'idiomas': l.get('idiomas', ['es']), 'res': bool(l.get('residencia'))})
    # coordenadas
    fuera = []; res = []
    for x in iglesias:
        g = geocode.localiza(x['id'], x['calle'], x['num'], x['localidad'], x['prov'], x['nombre'], x['cp'])
        if not g: fuera.append(x['id'] + ' (sin coordenadas)'); continue
        lat, lon, aprox = g
        d = km(CENTRO[0], CENTRO[1], lat, lon)
        if d > RADIO_KM: continue
        x['lat'], x['lon'], x['aprox'] = lat, lon, bool(aprox)
        res.append(x)
    # sin duplicados
    vistos = set(); fin = []
    for x in res:
        k = (x['nombre'].lower(), x['localidad'].lower(), x['calle'].lower())
        if k in vistos: continue
        vistos.add(k); fin.append(x)
    fin.sort(key=lambda x: (x['localidad'], x['nombre']))
    out = []
    for x in fin:
        o = {k: x[k] for k in ('id', 'nombre', 'localidad', 'calle', 'num', 'cp', 'tel', 'parroco', 'rol', 'arciprestazgo', 'diocesis', 'url', 'fuente',
                              'actualizado', 'lat', 'lon', 'aprox', 'verano', 'idiomas')}
        o['res'] = bool(x.get('res'))
        o['h'] = {'inv': x['h']['inv'], 'ver': x['h']['ver']}
        o['obs'] = x.get('obs', ''); o['texto'] = x.get('texto', '')
        if x.get('obs_raw'): o['obs'] = x['obs_raw']
        o['interpretado'] = not (season_empty(x['h']['inv']) and season_empty(x['h']['ver']))
        out.append(o)
    ahora = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=1))).strftime('%Y-%m-%dT%H:%M')
    datos = {'meta': {'built': ahora, 'centro': CENTRO, 'radio': RADIO_KM, 'fallos': fallos[:10], 'sinCoord': fuera[:20],
                      'fuentes': {'cadiz': len(cad), 'malaga': len(mal), 'local': len(loc['iglesias'])}}, 'i': out}
    open(os.path.join(SITE, 'misas.js'), 'w', encoding='utf8').write('window.MISAS=' + json.dumps(datos, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print('%d iglesias en %d km; sin coordenadas: %s; fallos de fuente: %s' % (len(out), RADIO_KM, fuera, fallos))
    return 0

if __name__ == '__main__':
    sys.exit(main())
