"""Utilidades comunes: lectura de las páginas oficiales de las diócesis y normalización de horarios.

Modelo de horario de una temporada (inv / ver):
  {"lab": [[lunes], [martes], [miércoles], [jueves], [viernes]],  # listas de "HH:MM"
   "visp": [...],   # sábado por la tarde y vísperas de fiesta
   "fest": [...]}   # domingos y festivos
"""
import html, re, urllib.request, time

UA = 'Mozilla/5.0 (compatible; campana-bot; +https://github.com/juanarenduelesb-byte/campana)'

def get(url, tries=3, timeout=40):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'es'})
            return urllib.request.urlopen(req, timeout=timeout).read().decode('utf8', 'ignore')
        except Exception as e:
            last = e; time.sleep(2 + 3 * i)
    raise last

def body_lines(t):
    t = re.sub(r'<script.*?</script>|<style.*?</style>|<!--.*?-->', '', t, flags=re.S)
    t = re.sub(r'<(br|/p|/div|/h\d|/li|/tr|/td|/span|/a)[^>]*>', '\n', t)
    t = re.sub(r'<[^>]+>', ' ', t)
    t = html.unescape(t)
    out = []
    for l in t.split('\n'):
        l = re.sub(r'[ \t\xa0]+', ' ', l).strip()
        if l: out.append(l)
    return out

def empty_season():
    return {'lab': [[], [], [], [], []], 'visp': [], 'fest': []}

def season_empty(s):
    return not (any(s['lab']) or s['visp'] or s['fest'])

def norm_time(h, m=None):
    h = int(h); m = int(m or 0)
    if not (0 <= h < 24 and 0 <= m < 60): return None
    return '%02d:%02d' % (h, m)

TIME_RE = re.compile(r'(?<![\d:.,])(\d{1,2})(?:\s*[:.,hH]\s*(\d{2}))?\s*(?:h\b|hs\b|hrs\b|horas\b|h\.)?(?![\d])')

def times_in(s):
    """Extrae horas de un texto libre: '19.30 h', '12:00', '9h', '20h.'"""
    out = []
    for m in re.finditer(r'(?<![\d:.,/])(\d{1,2})\s*(?:[:.,]\s*(\d{2}))?\s*(?:h\b|hs\b|hrs\b|horas\b|h\.|(?=\s*[,;y]|\s*$))', s):
        h, mi = m.group(1), m.group(2)
        # sin minutos ni 'h' detrás no es una hora (p. ej. "1º domingo")
        if mi is None and not re.match(r'\s*(?:h\b|hs\b|hrs\b|horas\b|h\.)', s[m.start(1) + len(h):]):
            continue
        t = norm_time(h, mi)
        if t and t not in out: out.append(t)
    return out

DAYS = {'lunes': 0, 'martes': 1, 'miercoles': 2, 'miércoles': 2, 'jueves': 3, 'viernes': 4, 'sabado': 5, 'sábado': 5, 'domingo': 6,
        'lun': 0, 'mar': 1, 'mie': 2, 'mié': 2, 'jue': 3, 'vie': 4, 'sab': 5, 'sáb': 5, 'dom': 6}
