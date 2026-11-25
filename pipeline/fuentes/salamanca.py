"""Diócesis de Salamanca: horario de misas de la ciudad (https://www.diocesisdesalamanca.com/horario-de-misas/).
Tres tablas (laborables, sábados y vísperas, domingos y festivos) de octubre a junio; se usan también para el verano y se avisa en la ficha."""
import re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from misas_lib import get, empty_season
from fuentes._comun import registro, txt

URL = 'https://www.diocesisdesalamanca.com/horario-de-misas/'
TIPOS = {'Dias-Laborables': 'lab', 'Sabados-y-Visperas': 'visp', 'Domingos-y-Festivos': 'fest'}

def run():
    s = get(URL); igl = {}
    for m in re.finditer(r'<table id="(tablepress-\d+)"', s):
        imgs = re.findall(r'uploads/\d+/\d+/Horario-de-Misas-[^"\s]*?(Dias-Laborables|Sabados-y-Visperas|Domingos-y-Festivos)', s[m.start() - 6000:m.start()])
        if not imgs: continue
        tipo = TIPOS[imgs[-1]]
        tabla = s[m.start():s.find('</table>', m.start())]
        for fila in re.findall(r'<tr[^>]*>(.*?)</tr>', tabla, re.S):
            c = [txt(x) for x in re.findall(r'<td[^>]*>(.*?)</td>', fila, re.S)]
            if len(c) < 4 or not re.match(r'\d{1,2}:\d{2}', c[1]): continue
            nombre = c[0].strip(' .'); hora = '%02d:%s' % (int(c[1].split(':')[0]), c[1].split(':')[1][:2])
            dire = c[3]; nota = ''
            if '**' in dire: dire, nota = dire.split('**', 1)
            k = nombre.lower()
            x = igl.setdefault(k, {'nombre': nombre, 'calle': dire.strip(' .'), 'h': empty_season(), 'obs': set()})
            if nota: x['obs'].add(nota.strip())
            if tipo == 'lab':
                for d in range(5):
                    if hora not in x['h']['lab'][d]: x['h']['lab'][d].append(hora)
            elif hora not in x['h'][tipo]: x['h'][tipo].append(hora)
    out = []
    for k, x in igl.items():
        for l in x['h']['lab']: l.sort()
        x['h']['visp'].sort(); x['h']['fest'].sort()
        obs = ' '.join(sorted(x['obs'])) + ' Horario publicado para octubre a junio; en verano puede cambiar.'
        out.append(registro('sa', k, x['nombre'], 'Salamanca', 'Salamanca', 'Salamanca', 'Diócesis de Salamanca', URL,
                            {'inv': x['h'], 'ver': x['h']}, calle=x['calle'], obs=obs.strip()))
    return out, []

if __name__ == '__main__':
    o, _ = run(); print(len(o))
    for x in o[:5]: print(x['nombre'], '|', x['calle'], '|', x['h']['inv']['lab'][0], x['h']['inv']['visp'], x['h']['inv']['fest'])
