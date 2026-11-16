"""Parroquias de la Diócesis de Málaga (https://diocesismalaga.es/parroquias).
Las fichas traen el horario en texto libre (INVIERNO / VERANO); aquí se interpreta
y, si una línea no se entiende, se conserva el texto original para mostrarlo tal cual."""
import re, time
from misas_lib import *

BASE = 'https://diocesismalaga.es'
# Localidades de la diócesis de Málaga a menos de ~60 km de Sotogrande (luego se filtra por distancia real)
LOCALIDADES = ['estepona', 'manilva', 'casares', 'gaucin', 'marbella', 'san-pedro-de-alcantara', 'benahavis', 'genalguacil',
               'jubrique', 'algatocin', 'benarraba', 'cancelada', 'secadero', 'sabinillas', 'nueva-andalucia', 'istan', 'ojen',
               'cortes-de-la-frontera', 'benadalid', 'atajate', 'faraján', 'farajan', 'igualeja', 'pujerra', 'parauta', 'cartajima',
               'juzcar', 'jimena', 'san-luis', 'monda', 'ronda', 'montejaque', 'benaojan', 'jimera', 'arriate', 'cortes']

def listar():
    t = get(BASE + '/parroquias')
    ls = sorted(set(re.findall(r'href="(/parroquias/\d+/[^"]+)"', t)))
    return [BASE + l for l in ls if any(k in l for k in LOCALIDADES)]

DIAS_RE = r'(lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bados?|domingos?)'
def dias_de(txt):
    """Devuelve (lista de días 0-6, es_vispera, es_festivo) para un texto como 'Viernes y sábados' o 'Lunes a viernes'."""
    t = txt.lower()
    t = t.replace('á', 'a').replace('é', 'e')
    fest = 'festivo' in t
    visp = 'vispera' in t or 'víspera' in txt.lower()
    lab = 'laborable' in t or 'diario' in t or 'dias de semana' in t or 'entre semana' in t
    dias = set()
    m = re.search(r'(lunes|martes|miercoles|jueves|viernes)\s+a\s+(lunes|martes|miercoles|jueves|viernes|sabado)', t)
    names = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
    if m:
        a, b = names.index(m.group(1)), names.index(m.group(2))
        dias.update(range(a, b + 1))
        t = t.replace(m.group(0), ' ')
    for i, n in enumerate(names):
        if re.search(r'\b' + n + r's?\b', t): dias.add(i)
    if lab and not (dias & {0, 1, 2, 3, 4}): dias.update(range(5))
    return sorted(dias), visp, fest

def add_times(sea, dias, visp, fest, times):
    for tm in times:
        for dd in dias:
            if dd <= 4:
                if tm not in sea['lab'][dd]: sea['lab'][dd].append(tm)
            elif dd == 5:
                if tm not in sea['visp']: sea['visp'].append(tm)
            elif dd == 6:
                if tm not in sea['fest']: sea['fest'].append(tm)
        if visp and tm not in sea['visp']: sea['visp'].append(tm)
        if fest and tm not in sea['fest']: sea['fest'].append(tm)

def parse(url, t):
    L = body_lines(t)
    try:
        i = next(k for k, l in enumerate(L) if l == 'Horario de Misas')
    except StopIteration:
        return None
    # cabecera: título, localidad, párroco, teléfono, email, dirección, arciprestazgo
    j = max(k for k, l in enumerate(L[:i]) if l.startswith('Inicio'))
    cab = L[j:i]
    d = {'url': url, 'diocesis': 'Málaga'}
    nombre = ''; loc = ''
    for n, l in enumerate(cab):
        if l == 'Parroquias /' and n + 3 < len(cab): nombre = cab[n + 2]; loc = cab[n + 3]
    d['nombre'] = nombre; d['localidad'] = loc
    d['parroco'] = ''; d['rol'] = ''; d['tel'] = ''; d['dir'] = []; d['arciprestazgo'] = ''
    for l in cab:
        m = re.match(r'(Párroco|Administrador parroquial|Vicario[^:]*|Rector):\s*(.*)', l)
        if m and not d['parroco']: d['rol'], d['parroco'] = m.group(1), m.group(2).strip()
        elif re.fullmatch(r'[\d ]{9,12}', l): d['tel'] = re.sub(r'\D', '', l)
        elif '·' in l and re.search(r'\b\d{5}\b', l): d['dir'] = [x.strip() for x in l.split('·')]
        elif l.startswith('Arciprestazgo:'): d['arciprestazgo'] = l.split(':', 1)[1].strip()
    # horario en texto libre
    fin = next((k for k in range(i, len(L)) if L[k] in ('Otros horarios', 'Fiestas', 'Histórico')), len(L))
    seg = L[i + 1:fin]
    h = {'inv': empty_season(), 'ver': empty_season()}
    obs, sin_interpretar = [], []
    sea = None; texto = []
    for l in seg:
        if re.match(r'Horarios sujetos|En "Domingos', l):
            continue
        texto.append(l)
        u = l.upper()
        if re.match(r'^(INVIERNO|VERANO)\b', u):
            sea = 'inv' if u.startswith('INVIERNO') else 'ver'
            resto = re.sub(r'^(INVIERNO|VERANO)\s*(\([^)]*\))?[:\s]*', '', l, flags=re.I).strip()
            if re.search(r'\(([^)]*)\)', l): obs.append(l.strip())
            if not resto: continue
            l = resto
        for parte in re.split(r'\n', l):
            if ':' in parte:
                dtxt, htxt = parte.split(':', 1)
                times = times_in(htxt)
                dias, visp, fest = dias_de(dtxt)
                if times and (dias or visp or fest):
                    for ss in ([sea] if sea else ['inv', 'ver']): add_times(h[ss], dias, visp, fest, times)
                    continue
            if parte.strip() and not re.match(r'(Confesiones|Despacho)', parte):
                sin_interpretar.append(parte.strip())
    for s in h.values():
        for x in s['lab']: x.sort()
        s['visp'].sort(); s['fest'].sort()
    # Si solo se da una temporada, vale para las dos
    if season_empty(h['ver']) and not season_empty(h['inv']): h['ver'] = h['inv']
    if season_empty(h['inv']) and not season_empty(h['ver']): h['inv'] = h['ver']
    d['h'] = h
    d['texto'] = ' / '.join(texto)
    d['obs'] = ' '.join(obs + sin_interpretar).strip()
    d['modificado'] = ''
    return d

def run(urls=None, pausa=0.25):
    urls = urls or listar()
    out, fallos = [], []
    for u in urls:
        try:
            t = get(u); d = parse(u, t)
            (out if d else fallos).append(d or u)
        except Exception as e:
            fallos.append(u + ' ' + str(e)[:60])
        time.sleep(pausa)
    return out, fallos

if __name__ == '__main__':
    import sys, json
    d = parse(sys.argv[1], open(sys.argv[2], encoding='utf8').read())
    print(json.dumps(d, ensure_ascii=False, indent=1))
