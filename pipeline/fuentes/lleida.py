"""Bisbat de Lleida: horaris de missa (https://www.bisbatlleida.org/ca/content/horaris-missa), vista paginada con una tabla por iglesia
(hora, dies, època, idioma, observacions)."""
import re, sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from misas_lib import get, empty_season
from fuentes._comun import registro, txt
from fuentes.tarragona import aplica

BASE = 'https://www.bisbatlleida.org'
URL = BASE + '/ca/content/horaris-missa'

def run():
    out, fallos, vistos = [], [], set()
    t = get(URL)
    ult = max([int(x) for x in re.findall(r'\?page=(\d+)', t)] or [0])
    for pg in range(ult + 1):
        if pg: t = get(URL + '?page=%d' % pg); time.sleep(0.5)
        for art in re.findall(r'<article class="mass-times-item">(.*?)</article>', t, re.S):
            a = re.search(r'<a href="([^"]+)"[^>]*>(.*?)</a>', art, re.S)
            if not a or a.group(1) in vistos: continue
            vistos.add(a.group(1))
            tit = txt(a.group(2))
            m = re.match(r'^(.*?)\s*\((.+)\)\s*$', tit)
            loc, nom = (m.group(1), m.group(2)) if m else (tit, tit)
            mm = re.match(r"^(.*),\s*(El|Els|La|Les|L')$", loc.strip())
            if mm: loc = (mm.group(2) + ('' if mm.group(2).endswith("'") else ' ') + mm.group(1)).strip()
            h = {'inv': empty_season(), 'ver': empty_season()}; ver = None; files = []
            for f in re.findall(r'<tr>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*</tr>', art, re.S):
                hora, dies, epoca, idioma, obs = [txt(x).strip(' .') for x in f]
                files.append(f'{hora} {dies}{" (" + epoca + ")" if epoca else ""}{" — " + obs if obs else ""}')
                ver = aplica(h, hora, dies, epoca, obs) or ver
            for s in h.values():
                for l in s['lab']: l.sort()
                s['visp'].sort(); s['fest'].sort()
            out.append(registro('ll', a.group(1).split('/')[-1], nom[:1].upper() + nom[1:], loc, 'Lleida', 'Lleida', 'Bisbat de Lleida', BASE + a.group(1),
                                h, verano=ver, texto=' / '.join(files), idiomas=['es', 'ca']))
    return out, fallos

if __name__ == '__main__':
    o, f = run(); print(len(o))
    for x in o[:4]: print(x['nombre'], '|', x['localidad'], '|', x['h']['inv']['lab'][0], x['h']['inv']['visp'], x['h']['inv']['fest'])
