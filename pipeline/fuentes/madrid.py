"""Archidiócesis de Madrid (guía diocesana, https://www.archimadrid.org/index.php/component/archimadrid/?view=parroquias).
El listado trae las parroquias; cada una tiene un servicio JSON (datos y horarios) que usa la propia web. Hace falta una sesión con su token."""
import re, json, time, html, http.cookiejar, urllib.request, urllib.parse, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from misas_lib import UA, empty_season
from norm import titulo
from temporadas import DEFECTO

BASE = 'https://www.archimadrid.org'
LISTA = BASE + '/index.php/component/archimadrid/?view=parroquias&Itemid=1236'
FUENTE = 'Archidiócesis de Madrid'
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static', 'cache_madrid.json')

class Sesion:
    def __init__(self):
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.op.addheaders = [('User-Agent', UA), ('Accept-Language', 'es')]
        self.t = self.op.open(LISTA, timeout=40).read().decode('utf8', 'ignore')
        self.token = re.search(r'id="token" name="token" value="([a-f0-9]{32})"', self.t).group(1)
    def post(self, task, id_, tries=3):
        url = f'{BASE}/index.php?option=com_archimadrid&task={task}&format=ajax&{self.token}=1'
        for i in range(tries):
            try:
                return json.loads(self.op.open(urllib.request.Request(url, data=urllib.parse.urlencode({'id': id_}).encode()), timeout=40).read().decode('utf8'))
            except Exception:
                if i == tries - 1: raise
                time.sleep(2 + 3 * i)

def listar(ses):
    return sorted(set(re.findall(r'onclick="datos\((\d+)\)"', ses.t)), key=int)

DIAS_LAB = {'lunes': 0, 'martes': 1, 'miercoles': 2, 'miércoles': 2, 'jueves': 3, 'viernes': 4}
DIA = {'diario': 'lab', 'sabado': 'visp', 'sábado': 'visp', 'domingo': 'fest', 'festivo': 'fest', 'festivos': 'fest'}
def horarios(filas):
    h = {'inv': empty_season(), 'ver': empty_season()}; raros = set()
    for f in filas:
        if f.get('tipo') != 'misas': continue
        sea = {'invierno': 'inv', 'verano': 'ver'}.get(f.get('tiempo'))
        dia = (f.get('dia') or '').lower()
        k = DIA.get(dia) or ('d' if dia in DIAS_LAB else None)
        if not sea or not k: raros.add((f.get('tiempo'), f.get('dia'))); continue
        try: hh = '%02d:%02d' % (int(f['inicio_hora']), int(f['inicio_min'] or 0))
        except Exception: continue
        if k == 'lab':
            for d in range(5):
                if hh not in h[sea]['lab'][d]: h[sea]['lab'][d].append(hh)
        elif k == 'd':
            if hh not in h[sea]['lab'][DIAS_LAB[dia]]: h[sea]['lab'][DIAS_LAB[dia]].append(hh)
        elif hh not in h[sea][k]: h[sea][k].append(hh)
    for s in h.values():
        for l in s['lab']: l.sort()
        s['visp'].sort(); s['fest'].sort()
    return h, raros

def normaliza(id_, d, filas):
    h, raros = horarios(filas)
    if not any(h['ver'][k] for k in ('visp', 'fest')) and not any(h['ver']['lab']): h['ver'] = h['inv']
    if not any(h['inv'][k] for k in ('visp', 'fest')) and not any(h['inv']['lab']): h['inv'] = h['ver']
    try: lat, lon = float(d['lat']), float(d['lng'])
    except Exception: return None
    if not (39.8 < lat < 41.2 and -4.6 < lon < -3.0): return None
    obs = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', d.get('obsevaciones') or ''))).strip()
    return {'id': 'md-' + str(id_), 'nombre': titulo(d['nombre']), 'localidad': titulo(d.get('poblacion') or 'Madrid'), 'calle': (d.get('direccion') or '').strip(),
            'num': '', 'cp': d.get('cp') or '', 'prov': 'Madrid', 'tel': re.sub(r'\D', '', d.get('telefono_fijo') or '')[:9], 'parroco': '', 'rol': '',
            'arciprestazgo': 'Vicaría ' + str(d.get('vicaria') or ''), 'diocesis': 'Madrid', 'url': LISTA, 'h': h, 'obs': obs, 'texto': '', 'verano': DEFECTO,
            'fuente': FUENTE, 'actualizado': '', 'idiomas': ['es'], 'lat': round(lat, 5), 'lon': round(lon, 5), 'aprox': False, '_raros': sorted(map(str, raros))}

def run(limite=None, pausa=0.15):
    ses = Sesion(); ids = listar(ses)[:limite]
    out, fallos = [], []
    for n, i in enumerate(ids):
        try:
            d = ses.post('datos_parroquia', i); d = d[0] if d else None
            if not d: fallos.append(i); continue
            x = normaliza(i, d, ses.post('horarios', i) or [])
            if x: out.append(x)
            else: fallos.append(i)
        except Exception as e:
            fallos.append(f'{i} {str(e)[:50]}')
        time.sleep(pausa)
        if n % 50 == 0: print('  madrid', n, '/', len(ids), flush=True)
    return out, fallos

if __name__ == '__main__':
    o, f = run(int(sys.argv[1]) if len(sys.argv) > 1 else 12)
    print(len(o), 'ok;', len(f), 'fallos', f[:5])
    for x in o[:6]: print(x['nombre'], '|', x['localidad'], '|', x['calle'], '|', x['h']['inv']['fest'], x['h']['inv']['lab'][0], x['h']['inv']['visp'], x['_raros'], x['obs'][:50])
    print(set(r for x in o for r in x['_raros']))
