"""Archidiócesis de Mérida-Badajoz: horarios de misas en Badajoz y Mérida (https://www.meridabadajoz.net/horario-de-misas/).
Cinco tablas por hora: Badajoz festivos, vísperas, laborables; Mérida festivos; Mérida vísperas y laborables."""
import re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from misas_lib import get
from fuentes._comun import lineas
from fuentes._invertido import aplica, registros

URL = 'https://www.meridabadajoz.net/horario-de-misas/'
ORDEN = [('Badajoz', ['fest']), ('Badajoz', ['visp']), ('Badajoz', ['lab']), ('Mérida', ['fest']), ('Mérida', ['visp', 'lab'])]

def run():
    t = get(URL); i = t.find('Hora')
    L = lineas(re.sub(r'<(script|style)[^>]*>.*?</\1>', '', t[t.find('Badajoz Festivos'):], flags=re.S))
    grupos = {'Badajoz': {}, 'Mérida': {}}; k = -1
    for l in L:
        if l.startswith('Hora Parroquias') or l == 'Hora':
            k += 1; continue
        if k < 0 or k >= len(ORDEN): continue
        ciudad, tipos = ORDEN[k]
        aplica(grupos[ciudad], tipos, l)
    out = []
    for c, igl in grupos.items():
        out += registros(igl, 'mb', c, 'Badajoz', 'Mérida-Badajoz', 'Archidiócesis de Mérida-Badajoz', URL)
    return out, []

if __name__ == '__main__':
    o, f = run(); print(len(o))
    for x in o[:5]: print(x['nombre'], '|', x['localidad'], '|', x['h']['inv']['lab'][0], x['h']['inv']['visp'], x['h']['inv']['fest'])
