"""Arquebisbat de Tarragona: buscador oficial de horaris de missa (https://horarismissa.arqtgn.cat/).
Cada misa trae hora, tipo de día (feiners, dissabtes i vigílies, diumenges i festius o un dia concret), època (hivern, estiu, tot l'any) e idioma."""
import re, sys, os, html, time, urllib.request, urllib.parse
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from misas_lib import get, UA, empty_season
from fuentes._comun import registro, txt
from norm import titulo

URL = 'https://horarismissa.arqtgn.cat/'
DIES = [('dilluns', 0), ('dimarts', 1), ('dimecres', 2), ('dijous', 3), ('divendres', 4), ('dissabte', 5), ('diumenge', 6)]
MESOS = {'gener': 1, 'febrer': 2, 'març': 3, 'abril': 4, 'maig': 5, 'juny': 6, 'juliol': 7, 'agost': 8, 'setembre': 9, 'octubre': 10, 'novembre': 11, 'desembre': 12}
ULT = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}

def aplica(h, hora, dies, epoca, obs):
    """Añade una fila «hora / dies / època / observacions» al horario h. Devuelve la temporada de verano si la deduce."""
    ver = None
    mm = re.match(r'(\d{1,2})(?:[:.h,](\d{2}))?', hora.strip())
    if not mm or int(mm.group(1)) > 23: return None
    hh = '%02d:%s' % (int(mm.group(1)), mm.group(2) or '00')
    if re.search(r'\b\d+(r|n|t|è|er|º|o)\b|primer|segon|tercer|quart|últim|ultim|mensual|del mes', (obs + ' ' + dies), re.I): return None
    e = epoca.lower()
    seas = ['ver'] if 'estiu' in e or 'verano' in e else ['inv'] if 'hivern' in e or 'invierno' in e else ['inv', 'ver']
    if seas == ['ver']:
        ms = [MESOS[x] for x in re.findall(r'(' + '|'.join(MESOS) + ')', obs.lower())]
        if len(ms) == 2: ver = [ms[0], 1, ms[1], ULT[ms[1]]]
    d = dies.lower(); dd = set(); visp = fest = False
    if 'feiner' in d or 'laborable' in d: dd = set(range(5))
    if 'dissabte' in d or 'vigíli' in d or 'vigili' in d or 'víspera' in d: visp = True
    if 'diumenge' in d or 'festiu' in d or 'domingo' in d: fest = True
    for nomd, i in DIES:
        if nomd in d and i < 5: dd.add(i)
    if 'tots els dies' in d or 'cada dia' in d or 'diari' in d: dd = set(range(5)); visp = fest = True
    for s in seas:
        for i in dd:
            if hh not in h[s]['lab'][i]: h[s]['lab'][i].append(hh)
        if visp and hh not in h[s]['visp']: h[s]['visp'].append(hh)
        if fest and hh not in h[s]['fest']: h[s]['fest'].append(hh)
    return ver

def post(pobles):
    data = urllib.parse.urlencode([('p[]', p) for p in pobles] + [('hd', '00'), ('ha', '23')]).encode()
    req = urllib.request.Request(URL, data=data, headers={'User-Agent': UA, 'X-Requested-With': 'XMLHttpRequest'})
    for i in range(3):
        try: return urllib.request.urlopen(req, timeout=90).read().decode('utf8', 'ignore')
        except Exception:
            if i == 2: raise
            time.sleep(5)

def run():
    t = get(URL)
    sel = t[t.find('id="poblacio"'):]; sel = sel[:sel.find('</select>')]
    pobles = [html.unescape(v) for v in re.findall(r'<option>([^<]*)</option>', sel)]
    out, fallos = [], []
    for k in range(0, len(pobles), 20):
        try: r = post(pobles[k:k + 20])
        except Exception as e: fallos.append(str(pobles[k:k + 20])[:60]); continue
        for bloc in re.split(r'<tr><td colspan="2"><h2>', r)[1:]:
            m = re.match(r'(.*?)<small>(.*?)</small>', bloc, re.S)
            if not m: continue
            nom, poble = txt(m.group(1)), txt(m.group(2))
            h = {'inv': empty_season(), 'ver': empty_season()}; ver = None; files = []
            for f in re.findall(r'<tr><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td></tr>', bloc, re.S):
                hora, dies, epoca, idioma, obs = [txt(x) for x in f]
                files.append(f'{hora} {dies} ({epoca}{", " + obs if obs else ""})')
                v = aplica(h, hora, dies, epoca, obs)
                ver = ver or v
            for s in h.values():
                for l in s['lab']: l.sort()
                s['visp'].sort(); s['fest'].sort()
            loc = titulo(poble)
            out.append(registro('tg', poble + '-' + nom, nom, loc, 'Tarragona', 'Tarragona', 'Arquebisbat de Tarragona', URL, h,
                                verano=ver, texto=' / '.join(files), idiomas=['es', 'ca']))
        time.sleep(1)
    return out, fallos

if __name__ == '__main__':
    o, f = run(); print(len(o), 'fallos', f)
    for x in o[:3]: print(x['nombre'], '|', x['localidad'], '|', x['h']['inv'], x['h']['ver']['fest'], x['verano'])
