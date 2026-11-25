"""Diócesis de Zamora: horario de misas por parroquia (https://www.diocesisdezamora.es/parroquias_horarios).
Bloques de laborables, sábados y vísperas, domingos y festivos; notas como «(solo en julio y agosto)» marcan el verano."""
import re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from misas_lib import get, empty_season
from fuentes._comun import registro, txt

URL = 'https://www.diocesisdezamora.es/parroquias_horarios'
TIPO = {'1': 'lab', '2': 'visp', '3': 'fest'}

def run():
    out, vistos = [], set()
    for sub in ('',):
        t = get(URL + sub)
        for b in t.split('<div class="horario_misa">')[1:]:
            m = re.search(r'<h2 class="titular_grande">(.*?)<span>\((.*)\)</span></h2>', b, re.S)
            if m: loc, nom = txt(m.group(1)), txt(m.group(2))
            else:
                m = re.search(r'<h2 class="titular_grande">(.*?)</h2>', b, re.S)
                if not m: continue
                loc, nom = 'Zamora', txt(m.group(1))
            if (loc, nom) in vistos: continue
            vistos.add((loc, nom))
            h = {'inv': empty_season(), 'ver': empty_season()}; ver = None; texto = []
            for tipo, cuerpo in re.findall(r'bloque_horario tipo_(\d)">(.*?)</div>', b, re.S):
                k = TIPO.get(tipo)
                for p in re.findall(r'<p class="dato[^"]*">(.*?)</p>', cuerpo, re.S):
                    hm = re.match(r'\s*(\d{1,2})[:.](\d{2})', txt(re.sub(r'<em.*', '', p, flags=re.S)))
                    obs = txt(re.search(r'<em[^>]*>(.*?)</em>', p, re.S).group(1)) if '<em' in p else ''
                    texto.append(f'{ {"lab": "Laborables", "visp": "Sábados", "fest": "Domingos"}[k]}: {txt(p)}')
                    if not hm or not k: continue
                    hh = '%02d:%s' % (int(hm.group(1)), hm.group(2)); o = obs.lower()
                    seas = ['inv', 'ver']
                    if re.search(r'(menos|excepto)[^)]*(julio|agosto)', o): seas = ['inv']
                    elif re.search(r'solo[^)]*(julio|agosto)', o): seas = ['ver']; ver = [7, 1, 8, 31]
                    elif re.search(r'(menos|excepto|solo)', o) and re.search(r'mes|domingo|sábado', o): continue
                    for s in seas:
                        if k == 'lab':
                            for d in range(5):
                                if hh not in h[s]['lab'][d]: h[s]['lab'][d].append(hh)
                        elif hh not in h[s][k]: h[s][k].append(hh)
            for s in h.values():
                for l in s['lab']: l.sort()
                s['visp'].sort(); s['fest'].sort()
            out.append(registro('za', loc + '-' + nom, nom, loc, 'Zamora', 'Zamora', 'Diócesis de Zamora', URL, h, verano=ver, texto=' / '.join(texto)))
    return out, []

if __name__ == '__main__':
    o, f = run(); print(len(o))
    import collections; print(collections.Counter(x['localidad'] for x in o).most_common(5))
    for x in o[:3]: print(x['nombre'], '|', x['localidad'], '|', x['h']['inv']['lab'][0], x['h']['inv']['visp'], x['h']['inv']['fest'], x['h']['ver']['fest'])
