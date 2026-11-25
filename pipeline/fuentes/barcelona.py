"""Arquebisbat de Barcelona: mapa de parròquies (https://esglesia.barcelona/parroquia/) con coordenadas y horario de misas
(en catalán o castellano, texto libre)."""
import re, json, html, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from misas_lib import get
from texto import interpreta
from fuentes._comun import registro, txt, lineas

URL = 'https://esglesia.barcelona/parroquia/'
POBLES = ["l'Hospitalet de Llobregat", 'Hospitalet', 'Badalona', 'Sant Adrià de Besòs', 'Santa Coloma de Gramenet', 'Esplugues de Llobregat',
          'Sant Just Desvern', 'Montcada i Reixac', 'Sant Feliu de Llobregat', 'Les Planes', 'Vallvidrera', 'Sant Cugat']

def run():
    t = get(URL); out, fallos = [], []
    cards = {m.group(1): m.group(2) for m in re.finditer(r'id="(esglesia-map_\d+)_card">(.*?)(?=<div class="ob-block-map__card"|</ul>|<li class="ob-block-map__list-point")', t, re.S)}
    for m in re.finditer(r'data-point_data="([^"]+)"', t):
        try: p = json.loads(html.unescape(m.group(1)))
        except Exception: continue
        c = cards.get(p['id'], '')
        nombre = txt(p.get('point_title', ''))
        lat, lon = float(p['point_left']), float(p['point_top'])
        desc = re.search(r'description_long_text">(.*?)</div>', c, re.S)
        L = lineas(desc.group(1)) if desc else []
        h, ver, ok, resto = interpreta(L)
        link = re.search(r'href="(https://esglesia.barcelona/parroquies/[^"]+)"', c)
        loc = 'Barcelona'
        for pob in POBLES:
            if pob.lower() in nombre.lower():
                loc = "L'Hospitalet de Llobregat" if 'hospitalet' in pob.lower() else pob; break
        m2 = re.search(r",\s*(?:de |d')(.+)$", nombre)
        m3 = re.search(r"\(([^)]+)\)\s*$", nombre)
        fuera = not (41.32 < lat < 41.47 and 2.05 < lon < 2.23)
        if m2:
            loc = m2.group(1).strip(); nombre = nombre[:m2.start()].strip()
            if loc.lower().startswith("l'hospitalet"): loc = "L'Hospitalet de Llobregat"
        elif m3 and fuera:
            loc = m3.group(1).strip(); nombre = nombre[:m3.start()].strip()
        nom = re.sub(r",\s*(de |d')?(l'Hospitalet de Llobregat|Badalona|Sant Adrià de Besòs|Santa Coloma de Gramenet|Esplugues de Llobregat|Sant Just Desvern|Montcada i Reixac|Sant Feliu de Llobregat)\s*$", '', nombre, flags=re.I)
        r = registro('bc', (link.group(1).rstrip('/').split('/')[-1] if link else p['id']), nom, loc, 'Barcelona', 'Barcelona', 'Arquebisbat de Barcelona',
                     link.group(1) if link else URL, h, verano=ver, texto=' / '.join(L), obs=' '.join(resto), idiomas=['es', 'ca'])
        if 41.2 < lat < 41.6 and 1.9 < lon < 2.4: r.update(lat=round(lat, 5), lon=round(lon, 5), aprox=False)
        out.append(r)
    return out, fallos

if __name__ == '__main__':
    o, f = run(); print(len(o))
    vac = [x for x in o if not x['h']['inv']['fest'] and not x['h']['inv']['visp'] and not any(x['h']['inv']['lab'])]
    print(len(vac), 'sin horario', sum(1 for x in o if 'lat' in x), 'con coord')
    for x in vac[:6]: print('  VACIO', x['nombre'], '|', x['texto'][:200])
    for x in o[:5]: print(x['nombre'], '|', x['localidad'], '|', x['h']['inv']['lab'], x['h']['inv']['visp'], x['h']['inv']['fest'], '|', x['texto'][:120])
