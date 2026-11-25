"""Diócesis de Alcalá de Henares: fichas de parroquias (https://diocesisdealcala.es/parroquias/) con horario de invierno y verano
(laborables / vísperas / festivos) y la ubicación del mapa de la propia ficha."""
import re, sys, os, time, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from misas_lib import get
from texto import interpreta
from fuentes._comun import registro, txt, lineas
from norm import titulo

BASE = 'https://diocesisdealcala.es/parroquias/'

def listar():
    t = get(BASE)
    return sorted(set(u for u in re.findall(r'href="(https://diocesisdealcala.es/parroquias/[^"]+/)"', t) if u != BASE))

def parse(url, t):
    tit = re.search(r'<meta property="og:title" content="([^"]+)"', t)
    nombre = txt(tit.group(1)).split(' - Diócesis')[0].split(' – Diócesis')[0] if tit else ''
    s = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', t, flags=re.S)
    i = min([p for p in (s.find('Invierno ('), s.find('Verano ('), s.find('Todo el año')) if p >= 0] or [-1])
    L = []
    if i >= 0:
        L = lineas(s[i:i + 8000])
        corte = next((k for k, l in enumerate(L) if re.match(r'(confesiones|despacho|horario de despacho|contactar)', l, re.I)), len(L))
        L = [l for l in L[:corte] if not l.startswith('<')]
    h, ver, ok, resto = interpreta(L)
    d = re.search(r'Direcci[oó]n\s*</[^>]+>(.*?)</', s, re.S)
    dire = txt(d.group(1)) if d else ''
    m = re.search(r'"lat":(-?\d+\.\d+),"lng":(-?\d+\.\d+)', t)
    loc = ''
    mm = re.search(r'\d{5}\.?\s*(.+)$', dire)
    if mm: loc = mm.group(1).strip(' .')
    cp = re.search(r'\b(28\d{3})\b', dire)
    calle = re.split(r'\.\s*\d{5}', dire)[0].strip(' .')
    lc = titulo(loc) if loc else 'Alcalá de Henares'
    if nombre.lower().startswith(lc.lower() + ' '): nombre = nombre[len(lc) + 1:]
    nombre = nombre[:1].upper() + nombre[1:]
    r = registro('al', url.rstrip('/').split('/')[-1], nombre, titulo(loc) if loc else 'Alcalá de Henares', 'Madrid', 'Alcalá de Henares',
                 'Diócesis de Alcalá de Henares', url, h, verano=ver, calle=calle, cp=cp.group(1) if cp else '', texto=' / '.join(L), obs=' '.join(resto))
    if m:
        lat, lon = float(m.group(1)), float(m.group(2))
        if 39.8 < lat < 41.2 and -4 < lon < -2.8: r.update(lat=round(lat, 5), lon=round(lon, 5), aprox=False)
    return r

def run(pausa=0.3):
    out, fallos = [], []
    for u in listar():
        try: out.append(parse(u, get(u)))
        except Exception as e: fallos.append(u + ' ' + str(e)[:50])
        time.sleep(pausa)
    return out, fallos

if __name__ == '__main__':
    U = listar(); print(len(U))
    for u in U[:6]:
        x = parse(u, get(u)); print(x['nombre'], '|', x['localidad'], '|', x['calle'], x.get('lat'), '|', x['h']['inv']['lab'][0], x['h']['inv']['visp'], x['h']['inv']['fest'], x['verano'])
