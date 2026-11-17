"""Genera los datos de Campana: un archivo por diócesis (site/data/<id>.js) y un índice de cobertura (site/data/indice.js).

Cada diócesis es una fuente independiente (pipeline/fuentes/<diocesis>.py) y SOLO usa la web oficial de esa diócesis
(más pipeline/static/locales.json, que viene de la parroquia de Guadiaro).
Si una diócesis falla o devuelve mucho menos que la vez anterior, se conserva su archivo anterior y el índice lo marca como «antiguo».
Los nombres de las fuentes se pueden limitar con:  python build.py cadiz sevilla"""
import json, os, re, sys, datetime, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geocode
from misas_lib import season_empty

AQUI = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(AQUI, '..', 'site', 'data')
FUENTES = [  # (id, módulo, nombre, web oficial)
    ('cadiz', 'cadiz', 'Cádiz y Ceuta', 'https://www.obispadocadizyceuta.es/parroquias/'),
    ('malaga', 'malaga', 'Málaga', 'https://diocesismalaga.es/parroquias'),
    ('sevilla', 'sevilla', 'Sevilla', 'https://www.archisevilla.org/iglesia/'),
    ('madrid', 'madrid', 'Madrid', 'https://www.archimadrid.org/index.php/component/archimadrid/?view=parroquias&Itemid=1236'),
]
PENDIENTES = json.load(open(os.path.join(AQUI, 'static', 'pendientes.json'), encoding='utf8'))
MIN_RATIO = 0.6   # si una diócesis devuelve menos de este % de lo anterior, se descarta lo nuevo
CAMPOS = ('id', 'nombre', 'localidad', 'calle', 'num', 'cp', 'tel', 'parroco', 'rol', 'arciprestazgo', 'diocesis', 'url', 'fuente',
          'actualizado', 'lat', 'lon', 'aprox', 'verano', 'idiomas')

def locales_cadiz():
    loc = json.load(open(os.path.join(AQUI, 'static', 'locales.json'), encoding='utf8'))
    out = []
    for l in loc['iglesias']:
        h = l['h']; h.setdefault('ver', h['inv'])
        out.append({**{k: l.get(k, '') for k in ('id', 'nombre', 'localidad', 'calle', 'num', 'cp', 'tel', 'arciprestazgo', 'diocesis', 'obs')},
                    'prov': 'Cádiz', 'parroco': l.get('parroco', ''), 'rol': '', 'url': loc['fuente_url'], 'h': h, 'texto': '', 'verano': [6, 1, 9, 30],
                    'fuente': 'Parroquia de Guadiaro (holasoto.com)', 'actualizado': loc['verificado'], 'idiomas': l.get('idiomas', ['es']),
                    'res': bool(l.get('residencia')), 'reemplaza': l.get('reemplaza')})
    return out

def preparar(lista, id_):
    """Coordenadas, duplicados y formato final de una diócesis."""
    if id_ == 'cadiz':
        loc = locales_cadiz()
        reemplazos = {x['reemplaza'] for x in loc}
        lista = [x for x in lista if x['id'] not in reemplazos] + loc
    sin = []; res = []
    for x in lista:
        if 'lat' not in x:
            g = geocode.localiza(x['id'], x['calle'], x['num'], x['localidad'], x['prov'], x['nombre'], x['cp'])
            if not g: sin.append(x['id']); continue
            x['lat'], x['lon'], x['aprox'] = g[0], g[1], bool(g[2])
        res.append(x)
    vistos = set(); fin = []
    for x in res:
        k = (x['nombre'].lower(), x['localidad'].lower(), x['calle'].lower(), x['url'])
        if k in vistos: continue
        vistos.add(k); fin.append(x)
    fin.sort(key=lambda x: (x['localidad'], x['nombre']))
    out = []
    for x in fin:
        o = {k: x[k] for k in CAMPOS}
        o['res'] = bool(x.get('res'))
        x.pop('_raros', None)
        o['h'] = {'inv': x['h']['inv'], 'ver': x['h']['ver']}
        o['obs'] = x.get('obs_raw') or x.get('obs', ''); o['texto'] = x.get('texto', '')
        o['interpretado'] = not (season_empty(x['h']['inv']) and season_empty(x['h']['ver']))
        out.append(o)
    return out, sin

def main(solo=None):
    ahora = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=1))).strftime('%Y-%m-%dT%H:%M')
    try: prev_idx = json.loads(open(os.path.join(DATA, 'indice.json'), encoding='utf8').read())
    except Exception: prev_idx = {}
    idx = []; problemas = []
    for id_, mod, nombre, web in FUENTES:
        if solo and id_ not in solo:
            e = next((d for d in prev_idx.get('dioc', []) if d['id'] == id_), None)
            if e: idx.append(e)
            continue
        print('==', nombre, flush=True)
        previo = leer_shard(id_)
        try:
            m = importlib.import_module('fuentes.' + mod)
            lista, fallos = m.run()
            nuevo, sin = preparar(lista, id_)
        except Exception as e:
            print('  ERROR', repr(e)[:200]); nuevo, fallos, sin = [], [str(e)[:100]], []
        estado = 'ok'
        if previo is not None and len(nuevo) < MIN_RATIO * len(previo) or not nuevo:
            problemas.append(f'{nombre}: {len(nuevo)} iglesias (antes {len(previo or [])})')
            estado = 'antiguo'
            if previo is None: continue
            nuevo = previo
        elif len(nuevo) < 20:
            problemas.append(f'{nombre}: demasiado pocas ({len(nuevo)})'); continue
        if estado == 'ok':
            escribir_shard(id_, nuevo)
        ant = next((d for d in prev_idx.get('dioc', []) if d['id'] == id_), {})
        la = [x['lat'] for x in nuevo]; lo = [x['lon'] for x in nuevo]
        idx.append({'id': id_, 'nombre': nombre, 'web': web, 'n': len(nuevo), 'ok': sum(1 for x in nuevo if x['interpretado']),
                    'bbox': [round(min(la), 3), round(min(lo), 3), round(max(la), 3), round(max(lo), 3)], 'estado': estado,
                    'actualizado': ahora if estado == 'ok' else ant.get('actualizado', ''), 'sinCoord': len(sin), 'fallos': len(fallos)})
        print('  %d iglesias, %d con horario, %d sin coordenadas, %d fallos' % (len(nuevo), idx[-1]['ok'], len(sin), len(fallos)), flush=True)
    try: ult = json.loads(open(os.path.join(DATA, 'indice.json'), encoding='utf8').read()).get('dioc', [])
    except Exception: ult = []
    hechos = {e['id'] for e in idx}
    idx += [e for e in ult if e['id'] not in hechos]          # lo que otro proceso haya escrito mientras tanto
    orden = [f[0] for f in FUENTES]; idx.sort(key=lambda e: orden.index(e['id']) if e['id'] in orden else 99)
    datos = {'built': ahora, 'dioc': idx, 'pendientes': PENDIENTES}
    os.makedirs(DATA, exist_ok=True)
    open(os.path.join(DATA, 'indice.json'), 'w', encoding='utf8').write(json.dumps(datos, ensure_ascii=False))
    open(os.path.join(DATA, 'indice.js'), 'w', encoding='utf8').write('window.CAMPANA_IDX=' + json.dumps(datos, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print('Índice: %d diócesis; problemas: %s' % (len(idx), problemas))
    return 1 if (problemas and not idx) else 0

def escribir_shard(id_, lista):
    os.makedirs(DATA, exist_ok=True)
    open(os.path.join(DATA, id_ + '.js'), 'w', encoding='utf8').write(
        "(window.CAMPANA_DATA=window.CAMPANA_DATA||{})[%s]=%s;\n" % (json.dumps(id_), json.dumps(lista, ensure_ascii=False, separators=(',', ':'))))

def leer_shard(id_):
    try:
        t = open(os.path.join(DATA, id_ + '.js'), encoding='utf8').read()
        return json.loads(t[t.index(']=') + 2:t.rindex(';')])
    except Exception:
        return None

if __name__ == '__main__':
    sys.exit(main(set(sys.argv[1:]) or None))
