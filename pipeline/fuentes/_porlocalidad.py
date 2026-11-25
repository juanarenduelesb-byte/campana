"""Páginas que listan los horarios por localidad: LOCALIDAD en mayúsculas, a veces el templo en una línea propia, y debajo los horarios."""
import re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from texto import interpreta, horas
from norm import titulo

TEMPLO = re.compile(r'^(pp(?=\.)|pp |ss(?=\.)|parroquia|iglesia|monasterio|residencia|ermita|capilla|santuario|convento|colegio|bas[ií]lica|catedral|concatedral|hospital|santa iglesia|templo|carmelitas|clarisas|madres|hermanas|religiosas|padres|seminario|real monasterio)\b', re.I)

def es_localidad(l):
    letras = re.sub(r'[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ]', '', l)
    return len(letras) >= 3 and sum(c.isupper() for c in letras) / len(letras) > 0.85 and not horas(l) and len(l) < 70

def bloques(L):
    """Devuelve [(localidad, templo, [líneas])]."""
    out = []; loc = None; tem = None; buf = []
    def cierra():
        if loc and buf: out.append((loc, tem, list(buf)))
    for l in L:
        l = l.strip(' ->•·')
        if not l: continue
        if TEMPLO.match(l) and not horas(l) and loc is not None:
            cierra(); buf.clear(); tem = l.rstrip(':').strip(); continue
        if es_localidad(l):
            cierra(); buf.clear(); tem = None
            loc = l.split(':')[0].strip(); resto = l.split(':', 1)[1].strip() if ':' in l else ''
            if resto: tem = titulo(resto)
            continue
        if loc is None: continue
        m = re.match(r'^([^:]{4,90}?)\s*:\s*(.*)$', l)
        if TEMPLO.match(l) and (not horas(l) or (m and TEMPLO.match(m.group(1)) and not re.search(r'lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo|laborable|diario|festivo', m.group(1), re.I))):
            cierra(); buf.clear()
            if m and horas(m.group(2)): tem, rest = m.group(1).strip(), m.group(2)
            else: tem, rest = l.rstrip(':').strip(), ''
            if rest: buf.append(rest)
            continue
        buf.append(l)
    cierra()
    return out

def registros(L, pref, prov, diocesis, fuente, url, registro):
    out = []; vistos = {}
    for loc, tem, lin in bloques(L):
        h, ver, ok, resto = interpreta(lin)
        locn = titulo(loc)
        nombre = titulo(tem) if tem else 'Parroquia de ' + locn
        k = (locn, nombre); vistos[k] = vistos.get(k, 0) + 1
        out.append(registro(pref, locn + '-' + nombre + ('-%d' % vistos[k] if vistos[k] > 1 else ''), nombre, locn, prov, diocesis, fuente, url, h,
                            verano=ver, texto=' / '.join(lin), obs=' '.join(resto)))
    return out
