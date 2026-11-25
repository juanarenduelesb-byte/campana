"""Diócesis de Lugo: buscador de horarios (Kyrios), https://www.diocesisdelugo.org/horarios-de-misa/.
Servicio JSON con cada misa: templo, parroquia, hora, días (1=lunes … 7=domingo), meses y frecuencia (1 = semanal)."""
import re, json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from misas_lib import get, empty_season
from fuentes._comun import registro

API = 'https://www.diocesisdelugo.org/wp-json/kyrios_integration/search_available_masses'
PAG = 'https://www.diocesisdelugo.org/horarios-de-misa/'

def run():
    t = get(PAG)
    ids = sorted(set(re.findall(r'<option value="(\d+)">Arciprestazgo', t))) or ['']
    misas = {}
    for i in ids:
        d = json.loads(get(API + ('?archpriestship=' + i if i else '')))
        for a in (d.values() if isinstance(d, dict) else []):
            for ms in a.values():
                for m in ms: misas[m['mass_id']] = m
    tem = {}
    for m in misas.values():
        if m.get('for_confessions') == '1' or m.get('frequency') not in ('1', '2', None): continue   # 1 = diaria, 2 = semanal; 3 y 4 (mensual, anual) quedan fuera
        meses = {int(x) for x in (m.get('months') or '').split(',') if x.strip().isdigit()} or set(range(1, 13))
        seas = ['inv', 'ver'] if len(meses) >= 11 else ['ver'] if meses <= {5, 6, 7, 8, 9, 10} else ['inv']
        x = tem.setdefault(m['worshipplace_id'], {'m': m, 'h': {'inv': empty_season(), 'ver': empty_season()}})
        hh = (m.get('mass_start_hour') or '')[:5]
        if not re.match(r'\d\d:\d\d', hh): continue
        for d in [int(v) for v in (m.get('weekdays') or '').split(',') if v.strip().isdigit()]:
            for s in seas:
                l = x['h'][s]['lab'][d - 1] if d <= 5 else x['h'][s]['visp'] if d == 6 else x['h'][s]['fest']
                if hh not in l: l.append(hh)
    out = []
    for wid, x in tem.items():
        m, h = x['m'], x['h']
        for s in h.values():
            for l in s['lab']: l.sort()
            s['visp'].sort(); s['fest'].sort()
        par = (m.get('chapelrie_description') or '').strip()
        loc = par.split(',')[0].strip()
        templo = (m.get('worshipplace_description') or '').split('>')[-1].strip()
        par = par.split('>')[-1].strip()
        nombre = templo if templo and templo.lower() not in ('iglesia parroquial', 'iglesia') else 'Iglesia parroquial de ' + par
        if loc.lower() == 'lugo' or loc.lower().startswith('lugo-'): loc = 'Lugo'
        out.append(registro('lu', wid, nombre, loc, 'Lugo', 'Lugo', 'Diócesis de Lugo', m.get('url') or PAG, h,
                            arciprestazgo='Parroquia de ' + par, idiomas=['es', 'gl']))
    return out, []

if __name__ == '__main__':
    o, f = run(); print(len(o))
    for x in o[:5]: print(x['nombre'], '|', x['localidad'], '|', x['h']['inv']['lab'][0], x['h']['inv']['visp'], x['h']['inv']['fest'])
