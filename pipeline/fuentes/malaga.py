import re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import geocode
from norm import titulo
from temporadas import temporada_verano
import fetch_malaga
DIOCESIS="Málaga"

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


def run():
    datos, fallos = fetch_malaga.run()
    return [x for x in (norm_malaga(d) for d in datos) if x], fallos
