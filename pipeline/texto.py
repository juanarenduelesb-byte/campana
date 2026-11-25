"""Intérprete de horarios de misa escritos en texto libre (español y catalán).

Entiende cosas como:
  Invierno (1/oct - 31/may) / LABORABLES / - 09:00 / VÍSPERAS / - 19:30 / FESTIVOS / - 12:00
  Lunes a Sábado: 19h. / Domingos: 9:30, 11:30 y 19h
  Feiners: Dimecres i Divendres 20:00h. / Diumenges i festius: 10 i 12h
Devuelve el horario en el formato de Campana y la temporada de verano si viene indicada."""
import re, unicodedata
from misas_lib import empty_season, season_empty
from temporadas import DEFECTO

def _plano(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if unicodedata.category(c) != 'Mn')

DIAS = [('lunes', 0), ('dilluns', 0), ('martes', 1), ('dimarts', 1), ('miercoles', 2), ('dimecres', 2), ('jueves', 3), ('dijous', 3),
        ('viernes', 4), ('divendres', 4), ('sabado', 5), ('dissabte', 5), ('domingo', 6), ('diumenge', 6)]
ABREV = {'l': 0, 'm': 1, 'x': 2, 'mi': 2, 'j': 3, 'v': 4, 's': 5, 'd': 6, 'lun': 0, 'mar': 1, 'mie': 2, 'jue': 3, 'vie': 4, 'sab': 5, 'dom': 6}
NOMBRES = {n: i for n, i in DIAS}
NOMBRES.update({n + 's': i for n, i in DIAS})
DIA_RE = r'(lunes|dilluns|martes|dimarts|miercoles|dimecres|jueves|dijous|viernes|divendres|sabados?|dissabtes?|domingos?|diumenges?)'

CAB = [  # (regex sobre texto plano, categoría)
    (r'^(laborables?|dias? laborables?|entre semana|diario|feiners?|dies feiners|de dilluns a divendres|de lunes a viernes|lunes a viernes)\b', 'lab'),
    (r'^(visperas?|sabados? y visperas|sabados?|vigilias?|dissabtes?|vespres?|vigilies)\b', 'visp'),
    (r'^(festivos?|domingos?( y festivos)?|domingos y fiestas|dominicals?|diumenges?( i festius)?|festius?|dias? festivos?)\b', 'fest'),
]
TEMP = re.compile(r'^(horario de |horari d\'|horari de |horarios de misa |horaris de missa )?(invierno|verano|hivern|estiu)\b')
MESES = {'ene': 1, 'gen': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'mai': 5, 'jun': 6, 'jul': 7, 'ago': 8, 'set': 9, 'sep': 9, 'oct': 10,
         'nov': 11, 'dic': 12, 'des': 12}

def horas(s):
    """'9:30, 11:30 y 19h' -> ['09:30','11:30','19:00']. Una cifra sola solo cuenta si lleva 'h'."""
    out = []
    for m in re.finditer(r'(?<![\d:.,/])(2[0-3]|[01]?\d)(?!\d)\s*(?:[:.,\']\s*([0-5]\d))?\s*(h\b|h\.|hs\b|hrs?\b|horas?\b|hores\b)?', s):
        if m.group(2) is None and not m.group(3): continue
        t = '%02d:%s' % (int(m.group(1)), m.group(2) or '00')
        if t not in out: out.append(t)
    return out

def dias(txt):
    """Días mencionados en un texto: (set de 0-6, laborables, vísperas, festivos)."""
    t = _plano(txt)
    lab = bool(re.search(r'laborable|diario|entre semana|feiner|cada dia|todos los dias|tots els dies', t))
    visp = bool(re.search(r'vispera|vigilia|vespre|vigil', t))
    fest = bool(re.search(r'festiv|festius|fiesta|dominical', t))
    d = set()
    for m in re.finditer(DIA_RE + r'\s+(?:a|al|hasta)\s+' + DIA_RE, t):
        a, b = NOMBRES[m.group(1)], NOMBRES[m.group(2)]
        if a <= b: d.update(range(a, b + 1))
    t2 = re.sub(DIA_RE + r'\s+(?:a|al|hasta)\s+' + DIA_RE, ' ', t)
    for m in re.finditer(r'\b' + DIA_RE + r'\b', t2): d.add(NOMBRES[m.group(1)])
    for m in re.finditer(r'\b([lmxjvsd]|lun|mar|mie|jue|vie|sab|dom)\s*[-–a]\s*([lmxjvsd]|lun|mar|mie|jue|vie|sab|dom)\b', t):
        a, b = ABREV[m.group(1)], ABREV[m.group(2)]
        if a <= b: d.update(range(a, b + 1))
    if (lab or 'todos los dias' in t or 'tots els dies' in t) and not d & {0, 1, 2, 3, 4}: d.update(range(5))
    if re.search(r'todos los dias|tots els dies|cada dia|diariamente', t): d.update(range(7))
    return d, lab, visp, fest

def _poner(h, d, visp, fest, ts):
    for t in ts:
        for x in d:
            l = h['lab'][x] if x < 5 else h['visp'] if x == 5 else h['fest']
            if t not in l: l.append(t)
        if visp and t not in h['visp']: h['visp'].append(t)
        if fest and t not in h['fest']: h['fest'].append(t)

def temporada(txt, sea):
    """Fechas de verano a partir de '(1/jun - 30/sep)' o 'de junio a septiembre' en una línea de temporada."""
    t = _plano(txt)
    m = re.search(r'(\d{1,2})\s*/\s*(\d{1,2}|[a-z]{3})[a-z]*\s*[-–a]+\s*(\d{1,2})\s*/\s*(\d{1,2}|[a-z]{3})', t)
    if m:
        def mes(x): return int(x) if x.isdigit() else MESES.get(x[:3])
        d1, m1, d2, m2 = int(m.group(1)), mes(m.group(2)), int(m.group(3)), mes(m.group(4))
        if m1 and m2 and 1 <= m1 <= 12 and 1 <= m2 <= 12:
            if sea == 'ver': return [m1, d1, m2, d2]
            # invierno: el verano empieza el día siguiente a su fin y acaba el anterior a su inicio
            import datetime
            try:
                a = datetime.date(2026, m2, d2) + datetime.timedelta(days=1); b = datetime.date(2026, m1, d1) - datetime.timedelta(days=1)
                return [a.month, a.day, b.month, b.day]
            except ValueError: return None
    return None

def interpreta(lineas):
    """lineas: lista de textos. Devuelve (h, verano, interpretadas, sin_interpretar)."""
    H = {'inv': empty_season(), 'ver': empty_season()}
    sea = None; cat = None; verano = None; ok = 0; resto = []; tocado = set()
    for l in lineas:
        l = re.sub(r'\s+', ' ', l).strip(' -–•·*|')
        if not l: continue
        p = _plano(l)
        mt = TEMP.match(p)
        if mt:
            sea = 'inv' if mt.group(2) in ('invierno', 'hivern') else 'ver'
            verano = verano or temporada(p, sea)
            l = re.sub(r'^[^:)]*(\)|:)', '', l).strip() if (':' in l or ')' in l) else ''
            cat = None
            if not l: continue
            p = _plano(l)
        destinos = [sea] if sea else ['inv', 'ver']
        pc = re.sub(r'^(santas? )?(misas?|misses?|eucaristias?|horarios?|horaris?)( de| d\')?\s*', '', p)
        cab = next((c for rx, c in CAB if re.match(rx, pc)), None)
        ts = horas(l)
        sp = re.search(r'(?<!\d)\s*:\s*', l)
        if sp and sp.start() > 0:
            izq, der = l[:sp.start()], l[sp.end():]
            d, lab, visp, fest = dias(izq)
            d2, lab2, visp2, fest2 = dias(der)
            if not (d or visp or fest) and (d2 or visp2 or fest2):
                d, visp, fest = d2, visp2, fest2
            elif (lab or cab == 'lab') and d2 and d2 <= {0, 1, 2, 3, 4} and not lab2:
                d = d2
            if cab and not d and not visp and not fest:
                if cab == 'lab': d = set(range(5))
                elif cab == 'visp': visp = True
                else: fest = True
            tsd = horas(der)
            if tsd and (d or visp or fest):
                for s in destinos: _poner(H[s], d, visp, fest, tsd); tocado.add(s)
                ok += 1; cat = cab or cat; continue
            if cab and not tsd: cat = cab; continue
        if cab:
            cat = cab
            d, lab, visp, fest = dias(l)
            if ts:
                if not (d or visp or fest):
                    d = set(range(5)) if cab == 'lab' else set(); visp = cab == 'visp'; fest = cab == 'fest'
                for s in destinos: _poner(H[s], d, visp, fest, ts); tocado.add(s)
                ok += 1
            continue
        d, lab, visp, fest = dias(l)
        if ts and (d or visp or fest):
            for s in destinos: _poner(H[s], d, visp, fest, ts); tocado.add(s)
            ok += 1; continue
        if ts and cat:
            d = set(range(5)) if cat == 'lab' else set()
            for s in destinos: _poner(H[s], d, cat == 'visp', cat == 'fest', ts); tocado.add(s)
            ok += 1; continue
        if ts: resto.append(l)
    for s in H.values():
        for x in s['lab']: x.sort()
        s['visp'].sort(); s['fest'].sort()
    if season_empty(H['ver']) and not season_empty(H['inv']): H['ver'] = H['inv']
    if season_empty(H['inv']) and not season_empty(H['ver']): H['inv'] = H['ver']
    return H, (verano or DEFECTO), ok, resto

if __name__ == '__main__':
    import json
    for ej in [
        ['Invierno (1/oct - 31/may)', 'LABORABLES', '- 09:00', '- 19:30', 'VíSPERAS', '- 19:30', 'FESTIVOS', '- 09:00 Se suprime', '- 12:30 Bilingüe', 'Verano (1/jun - 30/sep)', 'LABORABLES', '- 09:00', 'FESTIVOS', '- 12:30'],
        ['Horario de invierno:', 'Lunes a Sábado: 19h.', 'Domingos: 9:30, 11:30 y 19h', 'Horario de verano:', 'Lunes a Sábado: 20h', 'Domingos: 9:30 y 20h'],
        ['Feiners: Dimecres i Divendres 20:00h.', 'Diumenges i festius: 10:00h i 12h', 'Dissabte: 20:00h.'],
        ['L-V 12:00 · 19:30'], ['M-V 18:30'],
    ]:
        h, v, ok, r = interpreta(ej); print(ok, v, json.dumps(h['inv']), '| ver fest', h['ver']['fest'], r)
