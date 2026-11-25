"""Diócesis de Plasencia: horario de misas de la ciudad de Plasencia (https://diocesisplasencia.org/horario-de-misas/), listas por hora
con notas numeradas («(1) Solo los viernes»). Es el horario de octubre a marzo."""
import re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from misas_lib import get
from fuentes._comun import lineas
from fuentes._invertido import aplica, registros

URL = 'https://diocesisplasencia.org/horario-de-misas/'

def run():
    t = get(URL); i = t.find('Arciprestazgo de Plasencia')
    L = lineas(re.sub(r'<(script|style)[^>]*>.*?</\1>', '', t[i:], flags=re.S))
    fin = next((k for k, l in enumerate(L) if l.startswith('CURSILLOS') or l.startswith('Unidad Pastoral')), len(L))
    L = L[:fin]
    notas = {}
    for l in L:
        for n, txt in re.findall(r'\((\d)\)\s*([^()]+?)(?=\s*\(\d\)|$)', l):
            if l.lstrip().startswith('(1)'): notas[n] = txt.strip(' .')
    igl = {}; tipos = None
    for l in L:
        u = l.lower()
        if u.startswith('misas de diario'): tipos = ['lab']; continue
        if u.startswith('sábados') or u.startswith('sabados'): tipos = ['visp']; continue
        if u.startswith('domingos'): tipos = ['fest']; continue
        if l.lstrip().startswith('(1)') or not tipos: continue
        l = re.sub(r'\((\d)\)', lambda m: '(' + notas.get(m.group(1), '') + ')', l)
        aplica(igl, tipos, l)
    return registros(igl, 'ps', 'Plasencia', 'Cáceres', 'Plasencia', 'Diócesis de Plasencia', URL,
                     obs='Horario publicado de octubre a marzo; en verano puede cambiar.'), []

if __name__ == '__main__':
    o, f = run(); print(len(o))
    for x in o:
        if x['nombre'] in ('San Nicolás', 'Cristo de las Batallas', 'San Pedro', 'Ildefonsas'): print(x['nombre'], x['h']['inv']['lab'], x['h']['inv']['visp'], x['h']['inv']['fest'])
