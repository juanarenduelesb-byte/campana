"""Capa de OpenStreetMap: todas las iglesias católicas (y cristianas sin confesión indicada) de España.

- Sitúa en el mapa las iglesias de las zonas que aún no tienen fuente oficial.
- Si la iglesia tiene la etiqueta service_times, se interpreta como horario (fuente colaborativa, se indica en la ficha).
- Se descartan las que coinciden con una iglesia de una fuente oficial (a menos de 80 m).
Datos © colaboradores de OpenStreetMap, licencia ODbL (https://www.openstreetmap.org/copyright).
Uso:  python osm.py            (descarga de Overpass y genera site/data/osm-*.js)
      python osm.py fichero.json  (usa una descarga ya hecha)"""
import json, os, re, sys, math, time, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from misas_lib import UA, empty_season, season_empty
from temporadas import DEFECTO

AQUI = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(AQUI, '..', 'site', 'data')
SERVIDORES = ['https://overpass-api.de/api/interpreter', 'https://overpass.kumi.systems/api/interpreter',
              'https://overpass.private.coffee/api/interpreter', 'https://maps.mail.ru/osm/tools/overpass/api/interpreter']
ZONAS = [(35.9, -9.4, 38.6, -4.5), (35.9, -4.5, 38.6, 0.5), (38.6, -9.4, 41.2, -5.5), (38.6, -5.5, 39.25, -4.75), (38.6, -4.75, 39.25, -4.0), (39.25, -5.5, 39.9, -4.75), (39.25, -4.75, 39.9, -4.0), (38.6, -4.0, 39.9, -2.5), (39.9, -5.5, 41.2, -4.0), (39.9, -4.0, 41.2, -2.5), (38.6, -2.5, 41.2, 4.4),
         (41.2, -9.4, 44.0, -5.5), (41.2, -5.5, 44.0, -2.5), (41.2, -2.5, 44.0, 0.8), (41.2, 0.8, 43.0, 3.4), (27.5, -18.3, 29.5, -13.3), (35.2, -5.5, 35.95, -2.8)]
CONSULTA = """[out:json][timeout:300];
area["ISO3166-1"="ES"][admin_level=2]->.es;
nwr["amenity"="place_of_worship"]["religion"="christian"](area.es)(%s,%s,%s,%s);
out center tags qt;"""
UA_OSM = 'Campana/1.0 (horarios de misa; +https://github.com/juanarenduelesb-byte/campana)'
NO_CATOLICA = re.compile(r'evang|protest|bapti|adventist|jehov|testigos|pentecost|mormon|latter|orthodox|ortodox|anglican|lutheran|metodist|methodist|filadelfia|asamblea|cristiana de|iglesia de cristo|nueva vida|ministerio', re.I)

def _pide(servidor, q):
    req = urllib.request.Request(servidor, data=urllib.parse.urlencode({'data': q}).encode(),
                                 headers={'User-Agent': UA_OSM, 'Accept': 'application/json'})
    return json.loads(urllib.request.urlopen(req, timeout=420).read())

def descargar():
    """Descarga por zonas (una consulta de toda España de golpe agota el tiempo de los servidores)."""
    todos = {}
    for z in ZONAS:
        ok = False
        for intento in range(2):
            for srv in SERVIDORES:
                try:
                    d = _pide(srv, CONSULTA % z)
                    for e in d.get('elements', []): todos[(e['type'], e['id'])] = e
                    print('  zona', z, len(d.get('elements', [])), 'de', srv, flush=True); ok = True; break
                except Exception as e:
                    print('  zona', z, 'falla', srv, repr(e)[:80], flush=True); time.sleep(10)
            if ok: break
            time.sleep(60)
        if not ok: print('  zona sin datos:', z, flush=True)
        time.sleep(5)
    print('Overpass: %d elementos' % len(todos), flush=True)
    return {'elements': list(todos.values())} if len(todos) > 5000 else None

# ---------- service_times (sintaxis tipo opening_hours) ----------
DIA = {'mo': 0, 'tu': 1, 'we': 2, 'th': 3, 'fr': 4, 'sa': 5, 'su': 6}
MES = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}

def _dias(txt):
    d = set(); ph = False
    for p in re.split(r'\s*,\s*', txt.lower()):
        if p == 'ph': ph = True; continue
        m = re.fullmatch(r'(mo|tu|we|th|fr|sa|su)(?:\s*-\s*(mo|tu|we|th|fr|sa|su))?', p)
        if not m: return None, False
        a = DIA[m.group(1)]; b = DIA[m.group(2)] if m.group(2) else a
        d.update(range(a, b + 1) if a <= b else list(range(a, 7)) + list(range(0, b + 1)))
    return d, ph

def service_times(st):
    """'Mo-Fr 19:00; Sa 19:30; Su,PH 10:00,12:00' -> h (inv/ver) o None si no se entiende."""
    H = {'inv': empty_season(), 'ver': empty_season()}; entendido = 0
    for regla in [r.strip() for r in st.split(';') if r.strip()]:
        seas = ['inv', 'ver']
        m = re.match(r'^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s*-\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+', regla, re.I)
        if m:
            a, b = MES[m.group(1).lower()], MES[m.group(2).lower()]
            seas = ['ver'] if a in (5, 6, 7) and b in (8, 9) else ['inv'] if a in (9, 10, 11) else ['inv', 'ver']
            regla = regla[m.end():]
        m = re.match(r'^([A-Za-z,\s-]+?)\s+([\d:,\s-]+)$', regla)
        if not m: continue
        d, ph = _dias(m.group(1).strip())
        if d is None: continue
        horas = []
        for t in re.split(r'\s*,\s*', m.group(2).strip()):
            mm = re.match(r'^(\d{1,2}):(\d{2})', t)
            if mm and int(mm.group(1)) < 24: horas.append('%02d:%s' % (int(mm.group(1)), mm.group(2)))
        if not horas: continue
        entendido += 1
        for s in seas:
            for x in d:
                l = H[s]['lab'][x] if x < 5 else H[s]['visp'] if x == 5 else H[s]['fest']
                for t in horas:
                    if t not in l: l.append(t)
            if ph:
                for t in horas:
                    if t not in H[s]['fest']: H[s]['fest'].append(t)
    if not entendido: return None
    for s in H.values():
        for l in s['lab']: l.sort()
        s['visp'].sort(); s['fest'].sort()
    return H

# ---------- provincias (polígonos de site/geo.js) ----------
def provincias():
    t = open(os.path.join(AQUI, '..', 'site', 'geo.js'), encoding='utf8').read()
    G = json.loads(t[t.index('['):t.rindex(']') + 1])
    out = []
    for g in G:
        rings = [[tuple(map(float, p.split(','))) for p in r.split(' ')] for r in g['r']]
        out.append((rings, g['b']))
    return out

def dentro(lon, lat, ring):
    c = False; j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]; xj, yj = ring[j]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi + 1e-12) + xi: c = not c
        j = i
    return c

def provincia_de(lon, lat, P):
    for k, (rings, b) in enumerate(P):
        if b[0] <= lon <= b[2] and b[1] <= lat <= b[3] and any(dentro(lon, lat, r) for r in rings): return k
    # fuera de los polígonos simplificados (costa): la de caja más cercana
    return min(range(len(P)), key=lambda k: (max(P[k][1][0] - lon, 0, lon - P[k][1][2]) ** 2 + max(P[k][1][1] - lat, 0, lat - P[k][1][3]) ** 2))

def km(a, b, c, d):
    return 6371 * 2 * math.asin(math.sqrt(math.sin(math.radians(c - a) / 2) ** 2 + math.cos(math.radians(a)) * math.cos(math.radians(c)) * math.sin(math.radians(d - b) / 2) ** 2))

import unicodedata
def clave_nombre(s):
    s = ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if unicodedata.category(c) != 'Mn')
    s = re.sub(r'\b(parroquia|iglesia|parroquial|templo|ermita|capilla|santuario|de|del|la|el|los|las|y|nuestra|senora|ntra|sra)\b', ' ', s)
    return ' '.join(s.split())

NOMBRES = {}
def oficiales():
    pts = {}
    try: idx = json.load(open(os.path.join(DATA, 'indice.json'), encoding='utf8'))
    except Exception: return pts
    for d in idx['dioc']:
        t = open(os.path.join(DATA, d['id'] + '.js'), encoding='utf8').read()
        for x in json.loads(t[t.index(']=') + 2:t.rindex(';')]):
            NOMBRES.setdefault(clave_nombre(x['nombre']), []).append((x['lat'], x['lon']))
            if x.get('aprox'): continue
            pts.setdefault((round(x['lat'], 2), round(x['lon'], 2)), []).append((x['lat'], x['lon']))
    return pts

def cerca_oficial(lat, lon, pts, nombre=''):
    k = clave_nombre(nombre)
    if k and any(km(lat, lon, a, b) < 4 for a, b in NOMBRES.get(k, [])): return True
    for dl in (-0.01, 0, 0.01):
        for dn in (-0.01, 0, 0.01):
            for a, b in pts.get((round(lat + dl, 2), round(lon + dn, 2)), []):
                if km(lat, lon, a, b) < 0.08: return True
    return False

def main(fich=None):
    d = json.load(open(fich, encoding='utf8')) if fich else descargar()
    if not d: print('No se ha podido descargar OpenStreetMap; se conservan los datos anteriores.'); return 0
    P = provincias(); OF = oficiales()
    grupos = {}; n_h = 0; vistos = 0
    for e in d['elements']:
        tg = e.get('tags', {})
        nombre = (tg.get('name') or tg.get('name:es') or '').strip()
        if not nombre: continue
        den = (tg.get('denomination') or '').lower()
        if den and den not in ('catholic', 'roman_catholic', 'católica', 'catolica'): continue
        if NO_CATOLICA.search(nombre): continue
        if e['type'] == 'node': lat, lon = e['lat'], e['lon']
        elif 'center' in e: lat, lon = e['center']['lat'], e['center']['lon']
        else: continue
        if not (27 < lat < 44.5 and -19 < lon < 5): continue
        vistos += 1
        if cerca_oficial(lat, lon, OF, nombre): continue
        h = service_times(tg['service_times']) if tg.get('service_times') else None
        if h: n_h += 1
        calle = ' '.join(x for x in (tg.get('addr:street', ''), tg.get('addr:housenumber', '')) if x).strip()
        loc = tg.get('addr:city') or tg.get('addr:town') or tg.get('addr:village') or tg.get('is_in:municipality') or ''
        x = {'id': 'o' + e['type'][0] + str(e['id']), 'nombre': nombre, 'localidad': loc, 'calle': calle, 'num': '', 'cp': tg.get('addr:postcode', ''),
             'tel': re.sub(r'[^\d]', '', tg.get('phone') or tg.get('contact:phone') or '')[-9:], 'parroco': '', 'rol': '', 'arciprestazgo': '',
             'diocesis': '', 'url': 'https://www.openstreetmap.org/%s/%d' % (e['type'], e['id']), 'fuente': 'OpenStreetMap (datos colaborativos)',
             'actualizado': '', 'lat': round(lat, 5), 'lon': round(lon, 5), 'aprox': False, 'verano': DEFECTO, 'idiomas': ['es'], 'res': False,
             'h': h or {'inv': empty_season(), 'ver': empty_season()}, 'obs': '', 'texto': tg.get('service_times', ''), 'interpretado': bool(h),
             'osm': 1, 'web': tg.get('website') or tg.get('contact:website') or ''}
        grupos.setdefault(provincia_de(lon, lat, P), []).append(x)
    os.makedirs(DATA, exist_ok=True)
    for f in os.listdir(DATA):
        if f.startswith('osm-'): os.remove(os.path.join(DATA, f))
    capas = []
    for k, L in sorted(grupos.items()):
        L.sort(key=lambda x: (x['localidad'], x['nombre']))
        sid = 'osm-%02d' % k
        open(os.path.join(DATA, sid + '.js'), 'w', encoding='utf8').write(
            "(window.CAMPANA_DATA=window.CAMPANA_DATA||{})[%s]=%s;\n" % (json.dumps(sid), json.dumps(L, ensure_ascii=False, separators=(',', ':'))))
        la = [x['lat'] for x in L]; lo = [x['lon'] for x in L]
        capas.append({'id': sid, 'n': len(L), 'ok': sum(1 for x in L if x['interpretado']),
                      'bbox': [round(min(la), 3), round(min(lo), 3), round(max(la), 3), round(max(lo), 3)]})
    idx = json.load(open(os.path.join(DATA, 'indice.json'), encoding='utf8'))
    idx['osm'] = {'capas': capas, 'n': sum(c['n'] for c in capas), 'ok': sum(c['ok'] for c in capas),
                  'fecha': time.strftime('%Y-%m-%d')}
    open(os.path.join(DATA, 'indice.json'), 'w', encoding='utf8').write(json.dumps(idx, ensure_ascii=False))
    open(os.path.join(DATA, 'indice.js'), 'w', encoding='utf8').write('window.CAMPANA_IDX=' + json.dumps(idx, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print('OSM: %d iglesias católicas con nombre, %d nuevas (no oficiales) en %d provincias, %d con horario' % (vistos, idx['osm']['n'], len(capas), n_h))
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
