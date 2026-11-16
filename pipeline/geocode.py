"""Coordenadas de las parroquias: Nominatim (OpenStreetMap), con caché en pipeline/static/geo_cache.json.
Solo se consulta lo que no está en la caché (1 petición por segundo, como pide la política de uso)."""
import json, os, re, time, urllib.parse
from misas_lib import get

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'geo_cache.json')
ABREV = [(r'^Cl\b\.?', 'Calle'), (r'^Pz\b\.?', 'Plaza'), (r'^Av\b\.?', 'Avenida'), (r'^Avda\b\.?', 'Avenida'), (r'^Ba\b\.?', 'Barriada'),
         (r'^Cm\b\.?', 'Camino'), (r'^Ctra\b\.?', 'Carretera'), (r'^Pje\b\.?', 'Pasaje'), (r'^Bda\b\.?', 'Barriada'), (r'^Pg\b\.?', 'Polígono')]

def limpia_calle(s):
    s = re.sub(r',?\s*N[ºo°]\.?\s*(S/?N|\d+)\b.*$', '', s, flags=re.I)
    s = re.sub(r'\s*[-–]\s*[A-Z]\b.*$', '', s)
    s = re.sub(r'\bPiso\b.*$', '', s, flags=re.I)
    for a, b in ABREV: s = re.sub(a, b, s)
    num = re.search(r',?\s*N[ºo°]\.?\s*(\d+)', s)
    return s.strip(' ,.')

def cargar():
    try: return json.load(open(CACHE, encoding='utf8'))
    except Exception: return {}

def guardar(c):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    json.dump(c, open(CACHE, 'w', encoding='utf8'), ensure_ascii=False, indent=0, sort_keys=True)

def nominatim(q):
    u = 'https://nominatim.openstreetmap.org/search?format=json&limit=1&countrycodes=es,gi&q=' + urllib.parse.quote(q)
    r = json.loads(get(u))
    time.sleep(1.1)
    return (float(r[0]['lat']), float(r[0]['lon'])) if r else None

def localiza(clave, calle, num, localidad, provincia, nombre, cp=''):
    """Devuelve (lat, lon, aprox). aprox=True si solo se ha podido situar la localidad."""
    c = cargar()
    if clave in c: return tuple(c[clave])
    res = None
    intentos = []
    if calle:
        intentos.append((f'{calle} {num}, {cp} {localidad}, {provincia}'.replace('  ', ' '), False))
        intentos.append((f'{calle}, {localidad}, {provincia}', False))
    intentos.append((f'{nombre}, {localidad}, {provincia}', False))
    intentos.append((f'{localidad}, {provincia}', True))
    for q, aprox in intentos:
        try: p = nominatim(q)
        except Exception: p = None
        if p: res = (round(p[0], 5), round(p[1], 5), aprox); break
    if res:
        c[clave] = list(res); guardar(c)
    return res
