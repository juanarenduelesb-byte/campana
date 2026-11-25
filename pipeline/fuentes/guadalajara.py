"""Diócesis de Sigüenza-Guadalajara: horarios de misas en las parroquias (página de la diócesis, por localidad, texto libre)."""
import re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from misas_lib import get
from fuentes._comun import registro, lineas
from fuentes._porlocalidad import registros

URL = 'https://www.siguenza-guadalajara.org/index.php/destacados/3800-horarios-misas-guadalajara'

def run():
    t = get(URL)
    i = t.find('itemprop="articleBody"'); i = i if i > 0 else t.find('ALBALATE')
    j = t.find('</article>', i); j = j if j > 0 else i + 150000
    L = lineas(re.sub(r'<(script|style)[^>]*>.*?</\1>', '', t[i:j], flags=re.S))
    return registros(L, 'gu', 'Guadalajara', 'Sigüenza-Guadalajara', 'Diócesis de Sigüenza-Guadalajara', URL, registro), []

if __name__ == '__main__':
    o, f = run(); print(len(o))
    vac = [x for x in o if not x['h']['inv']['fest'] and not x['h']['inv']['visp'] and not any(x['h']['inv']['lab'])]
    print('vacías', len(vac), [ (x['localidad'], x['nombre'], x['texto'][:80]) for x in vac[:6]])
    for x in o[:8]: print(x['nombre'], '|', x['localidad'], '|', x['h']['inv']['lab'], x['h']['inv']['visp'], x['h']['inv']['fest'])
