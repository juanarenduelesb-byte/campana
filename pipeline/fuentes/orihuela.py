"""Diócesis de Orihuela-Alicante: listado de parroquias con horario de invierno y verano (https://diocesisoa.org/parroquias)."""
import re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from misas_lib import get
from texto import interpreta
from fuentes._comun import registro, txt, lineas
from norm import titulo

URL = 'https://diocesisoa.org/parroquias'

def run():
    t = get(URL); out, fallos = [], []
    for m in re.split(r'<div class="modal fade" id="modal-', t)[1:]:
        n = re.search(r'<h5[^>]*>(.*?)</h5>\s*<p[^>]*>(.*?)</p>', m, re.S)
        info = re.search(r'parroquia-info-text-modal">(.*?)</div>', m, re.S)
        if not n or not info: fallos.append(m[:12]); continue
        nombre, loc = titulo(txt(n.group(1))), titulo(txt(n.group(2)))
        L = lineas(info.group(1))
        # quitar despacho y lo que venga detrás de él
        corte = next((i for i, l in enumerate(L) if re.match(r'horario de despacho', l, re.I)), len(L))
        L = L[:corte]
        h, ver, ok, resto = interpreta(L)
        dire = re.search(r'fa-compass.*?<div[^>]*>(.*?)</div>', m, re.S)
        calle = lineas(dire.group(1))[0] if dire and lineas(dire.group(1)) else ''
        tel = re.search(r'href="tel:\+?34?(\d{9})"', m)
        mid = re.match(r'(\d+)', m)
        out.append(registro('oa', (mid.group(1) if mid else '') + '-' + nombre, nombre, loc, 'Alicante', 'Orihuela-Alicante', 'Diócesis de Orihuela-Alicante', URL,
                            h, verano=ver, calle=calle, tel=tel.group(1) if tel else '', texto=' / '.join(L), obs=' '.join(resto)))
    return out, fallos

if __name__ == '__main__':
    o, f = run(); print(len(o), 'fallos', len(f))
    vac = [x for x in o if not x['h']['inv']['fest'] and not x['h']['inv']['visp'] and not any(x['h']['inv']['lab'])]
    print(len(vac), 'sin horario'); [print('  ', x['nombre'], '|', x['texto'][:150]) for x in vac[:8]]
    for x in o[:4]: print(x['nombre'], '|', x['localidad'], '|', x['calle'], '|', x['h']['inv']['lab'][0], x['h']['inv']['visp'], x['h']['inv']['fest'], x['h']['ver']['fest'])
