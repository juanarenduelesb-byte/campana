"""Listas «invertidas»: por tipo de día, cada línea es una hora seguida de las iglesias que tienen misa a esa hora.
Variante con dos columnas (hora de invierno al principio y de verano al final)."""
import re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from misas_lib import empty_season
from fuentes._comun import registro
from texto import dias as dias_txt

HORA = r'(?:2[0-3]|[01]?\d)(?:[:.,]\d{2})?\s*h?\.?'
DIAS = {'lunes': 0, 'martes': 1, 'miércoles': 2, 'miercoles': 2, 'jueves': 3, 'viernes': 4}

def hm(s):
    m = re.match(r'(\d{1,2})(?:[:.,](\d{2}))?', s.strip())
    return '%02d:%s' % (int(m.group(1)), m.group(2) or '00') if m and int(m.group(1)) < 24 else None

def clave(n):
    n = re.sub(r'\s+', ' ', n.lower().replace('ntra.', 'nuestra').replace('sra.', 'señora').replace('s.i.', '')).strip(' .,*')
    return n

def aplica(igl, tipos, linea, dos_col=False):
    """igl: dict clave -> {'nombre','h'}; tipos: lista de 'lab'/'visp'/'fest'."""
    linea = linea.strip(' •·-')
    m = re.match(r'^(' + HORA + r')\s+(.*)$', linea)
    if not m: return
    hi = hm(m.group(1)); resto = m.group(2); hv = hi
    if dos_col:
        m2 = re.search(r'\s(' + HORA + r')\s*$', resto)
        if m2: hv = hm(m2.group(1)); resto = resto[:m2.start()]
    # partir por comas que no estén dentro de paréntesis
    partes, prof, act = [], 0, ''
    for ch in resto:
        if ch == '(': prof += 1
        elif ch == ')': prof = max(0, prof - 1)
        if ch == ',' and prof == 0: partes.append(act); act = ''
        else: act += ch
    partes.append(act)
    for p in partes:
        p = p.strip(' .;')
        if len(p) < 3: continue
        nota = ' '.join(re.findall(r'\(([^)]*)\)?', p)).lower()
        nombre = re.sub(r'\s*\([^)]*\)?', '', p).strip(' *.')
        if not nombre: continue
        seas = ['inv', 'ver']
        if '*' in p: seas = ['inv']   # asterisco: se suprime en verano
        if re.search(r'(s[oó]lo|solamente)[^)]*(verano|julio|agosto)', nota): seas = ['ver']
        elif re.search(r'(excepto|salvo|menos)[^)]*(verano|julio|agosto|junio)', nota): seas = ['inv']
        if re.search(r'primer|segundo|[1-4]º|mes\b', nota): continue
        dd = dias_txt(nota)[0]
        dias = sorted(x for x in dd if x < 5) or list(range(5))
        x = igl.setdefault(clave(nombre), {'nombre': nombre, 'h': {'inv': empty_season(), 'ver': empty_season()}})
        for s in seas:
            hh = hi if s == 'inv' else hv
            if not hh: continue
            for k in tipos:
                if k == 'lab':
                    for d in dias:
                        if hh not in x['h'][s]['lab'][d]: x['h'][s]['lab'][d].append(hh)
                elif hh not in x['h'][s][k]: x['h'][s][k].append(hh)

def registros(igl, pref, loc, prov, diocesis, fuente, url, obs=''):
    out = []
    for k, x in igl.items():
        for s in x['h'].values():
            for l in s['lab']: l.sort()
            s['visp'].sort(); s['fest'].sort()
        out.append(registro(pref, loc + '-' + k, x['nombre'], loc, prov, diocesis, fuente, url, x['h'], obs=obs))
    return out
