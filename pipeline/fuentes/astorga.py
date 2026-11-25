"""Diócesis de Astorga: horario de misas de Astorga, La Bañeza, Ponferrada y otras localidades
(https://www.diocesisastorga.es/actualidad/horario-de-misas), en prosa por localidad y templo."""
import re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from misas_lib import get
from fuentes._comun import registro, lineas
from fuentes._porlocalidad import registros

URL = 'https://www.diocesisastorga.es/actualidad/horario-de-misas'

def run():
    t = get(URL)
    i = t.find('>ASTORGA<'); i = i if i > 0 else t.find('CATEDRAL')
    L = lineas(re.sub(r'<(script|style)[^>]*>.*?</\1>', '', t[i + 1:], flags=re.S))
    fin = next((k for k, l in enumerate(L) if re.match(r'^(Volver|Compartir|Diócesis de Astorga|Aviso legal|©|Más Info|Síganos|Reportero|Día 7|Plan Pastoral)', l)), len(L))
    L = ['ASTORGA'] + L[:fin]
    out = registros(L, 'at', 'León', 'Astorga', 'Diócesis de Astorga', URL, registro)
    return [x for x in out if not re.search(r'día 7|plan pastoral|más info|síganos|reportero', x['localidad'], re.I)], []

if __name__ == '__main__':
    o, f = run(); print(len(o))
    import collections; print(collections.Counter(x['localidad'] for x in o))
    for x in o[:5]: print(x['nombre'], '|', x['localidad'], '|', x['h']['inv']['lab'][0], x['h']['inv']['visp'], x['h']['inv']['fest'])
