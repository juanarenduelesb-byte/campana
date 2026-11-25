"""Diócesis de Vitoria: mapas de horarios de Vitoria-Gasteiz y del resto de Álava, Orduña y Treviño (diocesisvitoria.org).
Cada iglesia trae coordenadas y su horario en texto («Misas, lunes a viernes: 10:30 h …»)."""
import re, json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from misas_lib import get
from texto import interpreta
from fuentes._comun import registro, lineas

PAGS = ['https://diocesisvitoria.org/horario-misas-vitoria-gasteiz/', 'https://diocesisvitoria.org/misas-alava-orduna-trevino/']
OBJ = re.compile(r'\{"title":"((?:[^"\\]|\\.)*)","cssClass":"[^"]*","description":"((?:[^"\\]|\\.)*)".*?"categories":\[(?:\{"title":"((?:[^"\\]|\\.)*)")?.*?"latitude":"(-?[\d.]*)","longitude":"(-?[\d.]*)"', re.S)

def run():
    out, vistos = [], set()
    for u in PAGS:
        t = get(u)
        for m in OBJ.finditer(t):
            tit, desc, cat, la, lo = [json.loads('"%s"' % g) if g is not None else '' for g in m.groups()]
            if tit in vistos or not la: continue
            vistos.add(tit)
            mm = re.match(r'^(.*?)\s*\(([^()]*)\)\s*$', tit)
            nom, loc = (mm.group(1), mm.group(2)) if mm else (tit, cat or 'Vitoria-Gasteiz')
            if ',' in loc: loc = loc.split(',')[-1].strip()
            L = [l for l in lineas(desc) if not re.match(r'^(tel|tfno|e-?mail|www|http)', l, re.I)]
            L = [re.sub(r'^misas?,?\s*', '', l, flags=re.I) for l in L]
            h, ver, ok, resto = interpreta(L)
            r = registro('vi', tit, nom, loc, 'Álava', 'Vitoria', 'Diócesis de Vitoria', u, h, verano=ver, texto=' / '.join(L), obs=' '.join(resto))
            tel = re.search(r'Tel\.?\s*([\d ]{9,12})', desc)
            if tel: r['tel'] = re.sub(r'\D', '', tel.group(1))[:9]
            lat, lon = float(la), float(lo)
            if 42.3 < lat < 43.3 and -3.3 < lon < -2.2: r.update(lat=round(lat, 5), lon=round(lon, 5), aprox=False)
            out.append(r)
    return out, []

if __name__ == '__main__':
    o, f = run(); print(len(o), sum(1 for x in o if 'lat' in x))
    vac = [x for x in o if not x['h']['inv']['fest'] and not x['h']['inv']['visp'] and not any(x['h']['inv']['lab'])]
    print('vacías', len(vac), [(x['nombre'], x['texto'][:80]) for x in vac[:5]])
    for x in o[:4]: print(x['nombre'], '|', x['localidad'], '|', x['h']['inv']['lab'][0], x['h']['inv']['visp'], x['h']['inv']['fest'])
