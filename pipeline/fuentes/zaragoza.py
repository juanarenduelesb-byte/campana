"""Archidiócesis de Zaragoza: buscador «Encuentra tu misa» (https://www.archizaragoza.org/misas).
La página lleva incrustada la lista de misas: parroquia, localidad, dirección, día (1 = lunes … 7 = domingo), hora y periodo (inicio-fin)."""
import re, json, sys, os, datetime
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from misas_lib import get, empty_season
from fuentes._comun import registro

URL = 'https://www.archizaragoza.org/misas'

def _temporada(ini, fin):
    """('09-15','06-30') -> invierno; ('07-01','09-14') -> verano; sin fechas -> todo el año."""
    if not ini or not fin: return ['inv', 'ver'], None
    m1, d1 = map(int, ini.split('-')); m2, d2 = map(int, fin.split('-'))
    if m1 > m2:   # cruza el año: invierno
        a = datetime.date(2026, m2, d2) + datetime.timedelta(days=1); b = datetime.date(2026, m1, d1) - datetime.timedelta(days=1)
        return ['inv'], [a.month, a.day, b.month, b.day]
    return ['ver'], [m1, d1, m2, d2]

def run():
    t = get(URL)
    j = t.find('[', t.find('data-bmz-data>')); k = t.find('</script>', j)
    arr = json.loads(t[j:k])
    igl = {}
    for x in arr:
        if x.get('tipo') != 'semanal' or x.get('accion') not in ('añadir', '') or not x.get('dia', '').isdigit(): continue
        hh = (x.get('hora') or '')[:5]
        if not re.match(r'\d\d:\d\d$', hh): continue
        r = igl.setdefault((x['parroquia'].strip(), x['localidad'].strip()), {'dir': x.get('direccion', ''), 'h': {'inv': empty_season(), 'ver': empty_season()}, 'ver': None})
        seas, ver = _temporada(x.get('inicio'), x.get('fin'))
        if ver and not r['ver']: r['ver'] = ver
        d = int(x['dia'])
        for s in seas:
            l = r['h'][s]['lab'][d - 1] if d <= 5 else r['h'][s]['visp'] if d == 6 else r['h'][s]['fest']
            if hh not in l: l.append(hh)
    # festivos: solo se añaden a domingo si la parroquia no tiene domingo (los festivos entre semana sustituyen al horario normal)
    out = []
    for (nom, loc), r in igl.items():
        for s in r['h'].values():
            for l in s['lab']: l.sort()
            s['visp'].sort(); s['fest'].sort()
        dire = r['dir']; cp = re.search(r'\b(50\d{3}|44\d{3}|22\d{3})\b', dire)
        out.append(registro('zg', loc + '-' + nom, nom, loc, 'Zaragoza', 'Zaragoza', 'Archidiócesis de Zaragoza', URL, r['h'], verano=r['ver'],
                            calle=re.sub(r',?\s*\d{5}.*$', '', dire).strip(' ,.'), cp=cp.group(1) if cp else ''))
    return out, []

if __name__ == '__main__':
    o, f = run(); print(len(o))
    import collections; print(collections.Counter(x['localidad'] for x in o).most_common(6))
    for x in o[:4]: print(x['nombre'], '|', x['localidad'], '|', x['calle'], '|', x['h']['inv']['lab'][0], x['h']['inv']['visp'], x['h']['inv']['fest'], x['h']['ver']['fest'], x['verano'])
