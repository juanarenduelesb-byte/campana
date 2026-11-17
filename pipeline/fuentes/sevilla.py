"""Archidiócesis de Sevilla (https://www.archisevilla.org/iglesia/...): fichas con tablas de horario L–D por temporada
y mapa de Google incrustado (de ahí salen las coordenadas, sin geocodificar)."""
import re, html, time, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from misas_lib import get, empty_season

BASE = 'https://www.archisevilla.org'
DIOCESIS = 'Sevilla'
FUENTE = 'Archidiócesis de Sevilla'

def listar():
    """[(url, lastmod)] de todas las fichas de iglesia."""
    t = get(BASE + '/iglesia-sitemap.xml')
    out = []
    for blk in re.findall(r'<url>(.*?)</url>', t, re.S):
        u = re.search(r'<loc>(?:<!\[CDATA\[)?([^<\]]+)', blk)
        m = re.search(r'<lastmod>(?:<!\[CDATA\[)?([^<\]]+)', blk)
        if u and '/iglesia/' in u.group(1): out.append((u.group(1), (m.group(1)[:10] if m else '')))
    return out

def _txt(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()

def parse(url, t, lastmod=''):
    h1 = re.search(r'<h2 class="font-replace">(.*?)</h2>', t, re.S)
    titulo = _txt(h1.group(1)) if h1 else ''
    if not titulo: return None
    # coordenadas del mapa
    lat = lon = None; aprox = False
    ifr = re.search(r'maps/embed\?pb=([^"]+)"', t)
    if ifr:
        pb = ifr.group(1)
        m = re.search(r'!2s[^!]+!3m2!1d(-?\d{1,2}\.\d+)!2d(-?\d{1,3}\.\d+)', pb)   # destino del mapa = la iglesia
        if m: lat, lon = float(m.group(1)), float(m.group(2))
        else:
            m = re.search(r'!2d(-?\d{1,3}\.\d+)!3d(-?\d{1,2}\.\d+)', pb)           # centro de la vista
            if m: lat, lon = float(m.group(2)), float(m.group(1)); aprox = True
        if lat is not None and not (27 < lat < 44 and -19 < lon < 5): lat = lon = None
    # tablas de horario
    h = {'inv': empty_season(), 'ver': empty_season()}
    visto = set()
    for cab, cuerpo in re.findall(r'<table[^>]*>\s*<thead>(.*?)</thead>\s*<tbody>(.*?)</tbody>', t, re.S):
        nom = _txt(cab).lower()
        sea = 'ver' if 'verano' in nom else 'inv' if 'invierno' in nom else None
        filas = re.findall(r'<tr>(.*?)</tr>', cuerpo, re.S)
        if sea is None or len(filas) < 2: continue
        letras = [_txt(c) for c in re.findall(r'<td[^>]*>(.*?)</td>', filas[0], re.S)]
        celdas = re.findall(r'<td[^>]*>(.*?)</td>', filas[1], re.S)
        if letras != ['L', 'M', 'X', 'J', 'V', 'S', 'D'] or len(celdas) != 7: continue
        horas = [sorted(set(f'{int(a):02d}:{b}' for a, b in re.findall(r'(\d{1,2})[:.](\d{2})', c))) for c in celdas]
        h[sea] = {'lab': horas[:5], 'visp': horas[5], 'fest': horas[6]}
        visto.add(sea)
    if len(visto) == 1:   # solo una tabla: vale para todo el año
        o = 'ver' if 'inv' in visto else 'inv'
        h[o] = h['inv' if 'inv' in visto else 'ver']
    # contacto
    i = t.find('<h4>CONTACTO</h4>')
    dire = ''
    if i >= 0:
        m = re.search(r'<p[^>]*>(?:<span[^>]*>)?\s*([^<]{8,160})', t[i:i + 3000])
        dire = _txt(m.group(1)) if m else ''
    tel = re.search(r'Tel[eé]fono[^<]*</[^>]+>\s*:?\s*(?:<[^>]+>\s*)*([\d \.]{9,})', t)
    mod = re.search(r'article:modified_time" content="([^"]+)"', t)
    nota = []
    for m in re.finditer(r'Nota:\s*([^<]{3,300})', t): nota.append(_txt(m.group(1)))
    return {'url': url, 'titulo': titulo, 'dir': dire, 'tel': re.sub(r'\D', '', tel.group(1))[:9] if tel else '', 'lat': lat, 'lon': lon, 'aprox': aprox,
            'h': h, 'obs': ' '.join(nota), 'modificado': (mod.group(1)[:10] if mod else lastmod)}

if __name__ == '__main__':
    import random, json
    urls = listar(); print(len(urls), 'fichas')
    random.seed(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
    for u, lm in random.sample(urls, int(sys.argv[2]) if len(sys.argv) > 2 else 12):
        d = parse(u, get(u), lm)
        if not d: print('SIN PARSEAR', u); continue
        n = sum(len(x) for x in d['h']['inv']['lab']) + len(d['h']['inv']['visp']) + len(d['h']['inv']['fest'])
        print(d['titulo'][:70], '|', d['dir'][:50], '|', d['lat'], d['lon'], '| misas inv:', n)

# ---------------------------------------------------------------- normalización
from norm import titulo
import geocode
from temporadas import DEFECTO

SUST = [(r'\bNTRA\.?', 'Nuestra'), (r'\bSRA\.?', 'Señora'), (r'\bSTA\.?', 'Santa'), (r'\bSTO\.?', 'Santo')]
RESTO = {'Asuncion': 'Asunción', 'Concepcion': 'Concepción', 'Alcala': 'Alcalá', 'Rio': 'Río', 'Moron': 'Morón', 'Ecija': 'Écija', 'Maria': 'María',
         'Jose': 'José', 'Purisima': 'Purísima', 'Basilica': 'Basílica', 'Jesus': 'Jesús', 'Marcos': 'Marcos', 'Guia': 'Guía', 'Corazon': 'Corazón',
         'Utrera': 'Utrera', 'Lebrija': 'Lebrija', 'Gelves': 'Gelves', 'Aznalcazar': 'Aznalcázar', 'Aznalcollar': 'Aznalcóllar', 'Cazalla': 'Cazalla',
         'Camaron': 'Camarón', 'Sanlucar': 'Sanlúcar', 'Bormujos': 'Bormujos', 'Mairena': 'Mairena', 'Arahal': 'Arahal', 'Lora': 'Lora', 'Gines': 'Gines',
         'Pedrera': 'Pedrera', 'Mármol': 'Mármol', 'Martin': 'Martín', 'Joaquin': 'Joaquín', 'Agustin': 'Agustín', 'Sebastian': 'Sebastián', 'Cristobal': 'Cristóbal',
         'Gonzalo': 'Gonzalo', 'Bartolome': 'Bartolomé', 'Andres': 'Andrés', 'Mateo': 'Mateo', 'Ildefonso': 'Ildefonso', 'Isabel': 'Isabel', 'Fatima': 'Fátima',
         'Angeles': 'Ángeles', 'Angel': 'Ángel', 'Cordoba': 'Córdoba', 'Dolores': 'Dolores', 'Rocio': 'Rocío', 'Pio': 'Pío', 'Valme': 'Valme', 'Esperanza': 'Esperanza'}
GENERICO = re.compile(r'^(TEMPLO PARROQUIAL|IGLESIA PARROQUIAL|PARROQUIA|TEMPLO)$', re.I)
CLASE = re.compile(r'^(capilla|ermita|bas[ií]lica|iglesia|convento|santuario|hospital|colegio|monasterio|real|catedral|sagrario|oratorio)\b', re.I)

def _nombre(s):
    for a, b in SUST: s = re.sub(a, b, s, flags=re.I)
    s = titulo(s)
    s = ' '.join(RESTO.get(w, w) for w in s.split(' '))
    s = re.sub(r'(?<=\w)cion\b', 'ción', s); s = re.sub(r'(?<=\w)sion\b', 'sión', s)
    return s

def normaliza(d):
    t = re.sub(r'^(templo parroquial|iglesia parroquial)\s*[-–]\s*', '', d['titulo'], flags=re.I)
    partes = [p.strip(' :') for p in re.split(r'\s[–-]\s', t) if p.strip(' :')]
    partes = [p for p in partes if not GENERICO.match(p)]
    loc = ''; nombre = ''
    dos = next((p for p in partes if ':' in p), None)
    if dos:
        a, b = [x.strip() for x in dos.split(':', 1)]
        loc, nombre = a, b
        resto = [p for p in partes if p != dos]
        if resto: nombre = (nombre or a) + ' – ' + ' – '.join(resto) if CLASE.match(resto[0]) else nombre
    elif len(partes) == 2 and not CLASE.match(partes[0]):
        loc, nombre = partes[0], partes[1]
    else:
        nombre = ' – '.join(partes)
    m = re.search(r'\(([^)]{3,30})\)\s*$', nombre)
    if m and not re.match(r'(c/|cl|av|pl|calle|esperanza|triana)', m.group(1), re.I) and not loc:
        loc, nombre = m.group(1), nombre[:m.start()].strip()
    dire = d['dir']; cp = ''; calle = ''
    m = re.search(r'^(.*?),?\s*(\d{5})\s+([^,]+)', dire)
    if m:
        calle, cp = m.group(1).strip(' ,'), m.group(2)
        calle = re.sub(r',?\s*n[ºo°]?\.?\s*\d+\w?$', '', calle, flags=re.I)
        loc = m.group(3).strip() or loc
    loc = _nombre(loc) if loc else 'Sevilla'
    nombre = _nombre(nombre.strip(' –:')) or 'Iglesia'
    slug = d['url'].rstrip('/').split('/')[-1]
    x = {'id': 'sv-' + slug, 'nombre': nombre, 'localidad': loc, 'calle': calle, 'num': '', 'cp': cp, 'prov': 'Sevilla', 'tel': d['tel'],
         'parroco': '', 'rol': '', 'arciprestazgo': '', 'diocesis': 'Sevilla', 'url': d['url'], 'h': d['h'], 'obs': d['obs'], 'texto': '',
         'verano': DEFECTO, 'fuente': FUENTE, 'actualizado': d['modificado'], 'idiomas': ['es']}
    lat, lon = d['lat'], d['lon']
    # (37.389, -5.995) es el centro de Sevilla que el mapa pone por defecto: no sirve como ubicación de una iglesia de otro pueblo
    defecto = lat is not None and abs(lat - 37.3886) < 0.002 and abs(lon + 5.9953) < 0.002
    if lat is not None and not defecto and 36.0 < lat < 38.4 and -6.7 < lon < -4.7:
        x['lat'], x['lon'], x['aprox'] = round(lat, 5), round(lon, 5), bool(d['aprox'])
    return x

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static', 'cache_sevilla.json')

def run(pausa=0.2):
    import json
    try: cache = json.load(open(CACHE, encoding='utf8'))
    except Exception: cache = {}
    out, fallos, nueva = [], [], {}
    for u, lm in listar():
        try:
            c = cache.get(u)
            if c and c['lm'] == lm and lm: d = c['d']
            else:
                d = parse(u, get(u), lm); time.sleep(pausa)
            if d:
                nueva[u] = {'lm': lm, 'd': d}; out.append(normaliza(d))
            else: fallos.append(u)
        except Exception as e:
            fallos.append(u + ' ' + str(e)[:60])
            if u in cache: nueva[u] = cache[u]; out.append(normaliza(cache[u]['d']))
    json.dump(nueva, open(CACHE, 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    return out, fallos
