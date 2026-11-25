"""Diócesis de Segovia: horarios de misas de la ciudad (https://diocesisdesegovia.es/horarios-de-misas/), listas por hora."""
import re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from misas_lib import get
from fuentes._comun import lineas
from fuentes._invertido import aplica, registros

URL = 'https://diocesisdesegovia.es/horarios-de-misas/'

def run():
    t = get(URL); i = t.find('LABORABLES MAÑANA')
    L = lineas(re.sub(r'<(script|style)[^>]*>.*?</\1>', '', t[i:], flags=re.S))
    igl = {}; tipos = None; dos = False
    for l in L:
        u = l.lower()
        if re.match(r'^laborables', u): tipos = ['lab']; dos = False; continue
        if re.match(r'^s[aá]bados', u): tipos = ['visp']; dos = False; continue
        if re.match(r'^domingos', u): tipos = ['fest']; dos = False; continue
        if 'invierno' in u and 'verano' in u and len(l) < 25: dos = True; continue
        if re.match(r'^(compartir|comparte|síguenos|diócesis de segovia|aviso|política)', u): break
        if tipos: aplica(igl, tipos, l, dos)
    return registros(igl, 'sg', 'Segovia', 'Segovia', 'Segovia', 'Diócesis de Segovia', URL), []

if __name__ == '__main__':
    o, f = run(); print(len(o))
    for x in o[:6]: print(x['nombre'], '|', x['h']['inv']['lab'][0], x['h']['inv']['visp'], x['h']['inv']['fest'], '| ver', x['h']['ver']['lab'][0])
