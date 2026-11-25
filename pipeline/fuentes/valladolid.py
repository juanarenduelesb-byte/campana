"""Archidiócesis de Valladolid: tablas de horarios de la capital y de los pueblos
(https://www.archivalladolid.org/horario-de-misas y .../horario-de-misas-pueblos). Columnas L, M, X, J, V, sábado y vísperas, domingo y festivos."""
import re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from misas_lib import get, empty_season
from fuentes._comun import registro, txt
from norm import titulo

BASE = 'https://www.archivalladolid.org/'
PAGS = ['horario-de-misas', 'horario-de-misas-pueblos']

def celda(c):
    c = re.sub(r'<span[^>]*>.*?</span>', '', c, flags=re.S)
    out = []
    for p in re.split(r'<br\s*/?>', c):
        p = txt(p)
        m = re.fullmatch(r'(\d{1,2})(?:[:.](\d{2}))?', p)
        if m and int(m.group(1)) < 24: out.append('%02d:%s' % (int(m.group(1)), m.group(2) or '00'))
    return sorted(set(out))

def run():
    out, fallos = [], []
    for pg in PAGS:
        t = get(BASE + pg)
        for li in re.split(r'<li>(?=<div class=imagen>)', t)[1:]:
            a = re.search(r'<a href="(entidad\.php\?Clave=([^"]+))">(.*?)</a>\s*<br\s*/?>\s*<span>(.*?)</span>', li, re.S)
            if not a: continue
            url, clave, nombre, dire = BASE + a.group(1), a.group(2), txt(a.group(3)), txt(a.group(4))
            filas = re.findall(r'<tr[^>]*>(.*?)(?=<tr|</table>)', li, re.S)
            if len(filas) < 2: continue   # «No hay horarios disponibles»
            cab = [txt(x) for x in re.findall(r'<th[^>]*>(.*?)(?=<th|$)', filas[0], re.S)]
            celdas = re.findall(r'<td[^>]*>(.*?)(?=<td|$)', filas[1], re.S)
            if len(cab) != 7 or len(celdas) != 7: fallos.append(url); continue
            hs = [celda(c) for c in celdas]
            h = {'lab': hs[:5], 'visp': hs[5], 'fest': hs[6]}
            partes = [x.strip() for x in dire.split('—')]
            cp = loc = calle = ''
            m = re.match(r'(\d{5})\s+(.+)', partes[-1])
            if m: cp, loc = m.group(1), m.group(2)
            calle = partes[0] if len(partes) > 1 else ''
            nombre = re.sub(r'^' + re.escape(loc.split(' (')[0]) + r'\s*-\s*', '', nombre) if loc else nombre
            nota = re.search(r'</table>\s*<p[^>]*>(.*?)</p>', li, re.S)
            out.append(registro('va', clave, nombre, loc or 'Valladolid', 'Valladolid', 'Valladolid', 'Archidiócesis de Valladolid', url,
                                {'inv': h, 'ver': h}, calle=calle, cp=cp, obs=txt(nota.group(1)) if nota else ''))
    return out, fallos

if __name__ == '__main__':
    o, f = run(); print(len(o), 'fallos', len(f))
    import collections; print(collections.Counter(x['localidad'] for x in o).most_common(5))
    for x in o[:3] + o[-3:]: print(x['nombre'], '|', x['calle'], x['cp'], x['localidad'], '|', x['h']['inv']['lab'][0], x['h']['inv']['visp'], x['h']['inv']['fest'])
