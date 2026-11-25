"""Archidiócesis de Pamplona y Tudela: hoja de cálculo oficial «Horarios de Misas Pamplona y comarca» enlazada en https://iglesianavarra.org/.
Cada hoja es una matriz iglesia × hora; una marca en la celda indica misa (una hora escrita en la celda la corrige)."""
import re, sys, os, io, datetime, urllib.request
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from misas_lib import get, UA, empty_season
from fuentes._comun import registro

HOME = 'https://iglesianavarra.org/'

def _xlsx_url():
    t = get(HOME)
    m = re.search(r'href="(https://iglesianavarra\.org/wp-content/uploads/[^"]+Horarios-de-Misas-Pamplona[^"]*\.xlsx)"', t)
    return m.group(1) if m else None

def _hm(v):
    return '%02d:%02d' % (v.hour, v.minute) if isinstance(v, (datetime.time, datetime.datetime)) else None

def run():
    import openpyxl
    url = _xlsx_url()
    if not url: return [], ['no encuentro la hoja de horarios en ' + HOME]
    data = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=60).read()
    wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True)
    igl = {}
    for ws in wb.worksheets:
        tit = ws.title.upper()
        comarca = 'COMARCA' in tit
        filas = list(ws.iter_rows(values_only=True))
        if len(filas) < 3: continue
        grupos = filas[0]; horas = filas[1]
        # a qué tipo de día pertenece cada columna
        tipo = []; g = None
        for j, cab in enumerate(grupos):
            if cab: g = str(cab).lower()
            tipo.append(g)
        for f in filas[2:]:
            if not f or not f[0] or not isinstance(f[0], str): continue
            nombre = f[0].strip()
            if len(nombre) < 3 or '=' in nombre or len(nombre) > 60: continue
            x = igl.setdefault((comarca, nombre), {'inv': empty_season(), 'ver': empty_season()})
            for j in range(1, len(f)):
                v = f[j]
                if v in (None, '') or j >= len(horas): continue
                t = _hm(v) or _hm(horas[j])
                if not t or not tipo[j]: continue
                k = tipo[j]
                if 'domingo' in k or 'festivo' in k and 'víspera' not in k and 'vispera' not in k: dst = ['fest']
                elif 'sábado' in k or 'sabado' in k: dst = ['visp'] if 'lunes' not in k else ['lab', 'visp']
                else: dst = ['lab']
                if 'LABORABLES' in tit and 'lunes a sábado' in k: dst = ['lab', 'visp']
                marca = str(v).strip() if not _hm(v) else 'x'
                seas = ['inv'] if marca == '#' else ['ver'] if marca.lower() == 'o' else ['inv', 'ver']
                letras = {'L': 0, 'M': 1, 'C': 2, 'X': 2, 'J': 3, 'V': 4}
                if marca.upper() in ('L-V', 'X', 'T', 'E', '#', 'O'): dias = range(5)
                else:
                    dias = sorted({letras[c] for c in re.findall(r'[LMCXJV]', marca.upper())}) or range(5)
                for sk in seas:
                    for dk in dst:
                        if dk == 'lab':
                            for d in dias:
                                if t not in x[sk]['lab'][d]: x[sk]['lab'][d].append(t)
                        elif t not in x[sk][dk]: x[sk][dk].append(t)
    out = []
    for (comarca, nombre), h in igl.items():
        for se in h.values():
            for l in se['lab']: l.sort()
            se['visp'].sort(); se['fest'].sort()
        loc, nom = 'Pamplona', nombre
        if comarca:
            m = re.match(r'^([^(]+?)\s*\((.+)\)\s*$', nombre)
            loc, nom = (m.group(1), m.group(2)) if m else (nombre, 'Parroquia de ' + nombre)
        out.append(registro('pa', loc + '-' + nom, nom, loc.strip(), 'Navarra', 'Pamplona y Tudela', 'Archidiócesis de Pamplona y Tudela', url,
                            h, obs='Hoja oficial de horarios de Pamplona y comarca; en verano algunos horarios pueden cambiar.'))
    return out, []

if __name__ == '__main__':
    o, f = run(); print(len(o), f)
    for x in o[:4] + o[-4:]: print(x['nombre'], '|', x['localidad'], '|', x['h']['inv']['lab'][0], x['h']['inv']['visp'], x['h']['inv']['fest'])
