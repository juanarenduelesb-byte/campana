"""Bisbat de Menorca: horaris de misses (https://bisbatdemenorca.org/horaris-de-misses/). Tabla por pueblo e iglesia:
feiners, dissabte, diumenge. Es el horario de invierno (de mediados de septiembre a mediados de junio); el asterisco marca misa en castellano."""
import re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from misas_lib import get, empty_season
from fuentes._comun import registro, txt

URL = 'https://bisbatdemenorca.org/horaris-de-misses/'
AB = {'dl': 0, 'dt': 1, 'dc': 2, 'dj': 3, 'dv': 4}

def horas(c):
    out = []
    for m in re.finditer(r'(?<![\d.])(\d{1,2})(?:[.:](\d{2}))?(?![\d])', c):
        if int(m.group(1)) < 24: out.append('%02d:%s' % (int(m.group(1)), m.group(2) or '00'))
    return out

def run():
    t = get(URL)
    tb = re.search(r'<table.*?</table>', t, re.S).group(0)
    out = []; pob = None
    for f in re.findall(r'<tr[^>]*>(.*?)</tr>', tb, re.S):
        cs = [re.sub(r'<br\s*/?>', '\n', c) for c in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', f, re.S)]
        cs = [txt(c) if '\n' not in c else '\n'.join(txt(x) for x in c.split('\n')).strip() for c in cs]
        if len(cs) == 1 or (len(cs) > 1 and not any(cs[1:])):
            pob = cs[0].strip(); continue
        if len(cs) < 4 or cs[0].startswith('Ciutat') or not pob: continue
        h = empty_season(); es = '*' in ' '.join(cs[1:])
        for linea in cs[1].split('\n'):
            ds = [AB[a] for a in re.findall(r'\b(dl|dt|dc|dj|dv)\b', linea.lower())]
            limpio = re.sub(r'\b(dl|dt|dc|dj|dv)\.?', '', linea, flags=re.I)
            for hh in horas(limpio.split(' al ')[0]):
                for d in (ds or range(5)):
                    if hh not in h['lab'][d]: h['lab'][d].append(hh)
        h['visp'] = sorted(set(horas(cs[2]))); h['fest'] = sorted(set(horas(cs[3])))
        for l in h['lab']: l.sort()
        out.append(registro('mn', pob + '-' + cs[0], cs[0], pob, 'Baleares', 'Menorca', 'Bisbat de Menorca', URL, {'inv': h, 'ver': h},
                            texto=f'Feiners: {cs[1]} / Dissabte: {cs[2]} / Diumenge: {cs[3]}', idiomas=['es', 'ca'] if es else ['ca'],
                            obs='Horario de invierno (de septiembre a junio). En verano puede cambiar. (*) = misa en castellano.'))
    return out, []

if __name__ == '__main__':
    o, f = run(); print(len(o))
    for x in o[:3] + o[12:14]: print(x['nombre'], '|', x['localidad'], '|', x['h']['inv']['lab'], x['h']['inv']['visp'], x['h']['inv']['fest'])
