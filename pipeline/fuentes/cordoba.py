"""Diócesis de Córdoba: buscador de horarios de misas de la ciudad (https://www.diocesisdecordoba.es/horarios-de-misas/).
La web carga un JSON con cada iglesia, su zona y el horario en texto (DIAS LABORABLES … SABADOS Y VISPERAS … DOMINGOS Y FESTIVOS …)."""
import re, json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from misas_lib import get
from texto import interpreta
from norm import titulo
from fuentes._comun import registro

JSON = 'https://diocesisdecordoba.es/media//ddctheme-busqueda/horarios.json'
BASE = 'https://www.diocesisdecordoba.es'

def run():
    d = json.loads(get(JSON)); out = []
    for x in d:
        s = x.get('x') or ''
        s = re.sub(r'D[IÍ]AS LABORABLES', '\nLaborables:', s)
        s = re.sub(r'S[AÁ]BADOS Y V[IÍ]SPERAS(?: DE)?(?: FESTIVOS?)?', '\nSábados y vísperas:', s)
        s = re.sub(r'DOMINGOS Y FESTIVOS', '\nDomingos y festivos:', s)
        L = [re.sub(r'\s*[–-]\s*', ', ', l).strip() for l in s.split('\n') if l.strip()]
        h, ver, ok, resto = interpreta(L)
        nom = titulo(x['t'].strip())
        loc = 'Córdoba'
        m = re.search(r'\(([^()]*(?:Alcolea|Higuerón|Villarrubia|Santa Cruz|Cerro Muriano|Trassierra|Encinarejo)[^()]*)\)', x['t'], re.I)
        if m: loc = titulo(m.group(1).split('–')[-1].split('(')[-1].strip(' )'))
        out.append(registro('co', x.get('u') or x['t'], nom, loc, 'Córdoba', 'Córdoba', 'Diócesis de Córdoba', BASE + (x.get('u') or ''), h,
                            verano=ver, arciprestazgo=x.get('z', ''), texto=x.get('x', ''), obs=' '.join(resto)))
    return out, []

if __name__ == '__main__':
    o, f = run(); print(len(o))
    vac = [x for x in o if not x['h']['inv']['fest'] and not x['h']['inv']['visp'] and not any(x['h']['inv']['lab'])]
    print('vacías', len(vac), [x['texto'][:60] for x in vac[:4]])
    for x in o[:5]: print(x['nombre'], '|', x['localidad'], '|', x['h']['inv']['lab'], x['h']['inv']['visp'], x['h']['inv']['fest'])
