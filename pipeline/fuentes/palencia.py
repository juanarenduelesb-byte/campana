"""Diócesis de Palencia: misas dominicales y de sábado en la ciudad (https://www.diocesispalencia.org/index.php/la-diocesis/horarios-de-misas).
Listas por hora; el asterisco indica que esa misa se suprime en verano. Los laborables se publican aparte y no se incluyen."""
import re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from misas_lib import get
from fuentes._comun import lineas
from fuentes._invertido import aplica, registros

URL = 'https://www.diocesispalencia.org/index.php/la-diocesis/horarios-de-misas'

def run():
    t = get(URL); i = t.find('MISAS DOMINICALES')
    L = lineas(re.sub(r'<(script|style)[^>]*>.*?</\1>', '', t[i:], flags=re.S))
    igl = {}; tipos = None
    for l in L:
        u = l.lower()
        if u.startswith('sábados por la tarde') or u.startswith('sabados por la tarde'): tipos = ['visp']; continue
        if u.startswith('domingos'): tipos = ['fest']; continue
        if u.startswith('parroquias y otros'): break
        if tipos: aplica(igl, tipos, l.replace('•', ' ').strip())
    return registros(igl, 'pl', 'Palencia', 'Palencia', 'Palencia', 'Diócesis de Palencia', URL,
                     obs='La diócesis publica en esta lista solo las misas de sábado y domingo.'), []

if __name__ == '__main__':
    o, f = run(); print(len(o))
    for x in o[:5]: print(x['nombre'], '|', x['h']['inv']['visp'], x['h']['inv']['fest'], '| ver', x['h']['ver']['fest'])
