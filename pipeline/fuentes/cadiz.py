import re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import geocode
from norm import titulo
from temporadas import temporada_verano
import fetch_cadiz
DIOCESIS="Cádiz y Ceuta"

def calle_num(dirs):
    """['Cl Romero De Figueroa, Nº 2', ...] -> ('Calle Romero de Figueroa', '2')"""
    s = dirs[0] if dirs else ''
    num = ''
    m = re.search(r',?\s*N[ºo°]\.?\s*(\d+)', s)
    if m: num = m.group(1)
    return geocode.limpia_calle(s), num

def norm_cadiz(d):
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


def run():
    datos, fallos = fetch_cadiz.run()
    return [x for x in (norm_cadiz(d) for d in datos) if x], fallos
