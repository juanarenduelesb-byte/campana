"""Parroquias del Obispado de Cádiz y Ceuta (https://www.obispadocadizyceuta.es/parroquias/).
Lee el sitemap, descarga cada ficha y devuelve datos y horarios de invierno y verano.
"""
import re, time, json, sys, os
from misas_lib import *

BASE = 'https://www.obispadocadizyceuta.es'
LETRAS = {'L': 0, 'M': 1, 'X': 2, 'J': 3, 'V': 4}

def listar():
    t = get(BASE + '/parroquias-sitemap.xml')
    return [u for u in re.findall(r'<loc>([^<]+)</loc>', t) if '/parroquias/' in u and u.rstrip('/').split('/')[-1] != 'parroquias']

def parse(url, t):
    L = body_lines(t)
    try:
        i = next(k for k, l in enumerate(L) if l.startswith('Arciprestazgo:'))
    except StopIteration:
        return None
    fin = next((k for k in range(i, len(L)) if L[k].startswith('Donaciones') or L[k].startswith('C/ Hospital de mujeres')), len(L))
    seg = []
    for l in L[i:fin]:
        if seg and re.match(r'^(Arciprestazgo|Templo|Párroco[^:]*|Administrador parroquial|Vicario[^:]*|Rector|Dirección|Teléfono):$', seg[-1]): seg[-1] = seg[-1] + ' ' + l
        else: seg.append(l)
    d = {'url': url, 'diocesis': 'Cádiz y Ceuta', 'arciprestazgo': seg[0].split(':', 1)[1].strip().title().replace(' – ', ' – ')}
    d['nombre'] = ''
    resp = []
    k = 1
    while k < len(seg) and not seg[k].startswith('Horarios de misa'):
        l = seg[k]
        if l.startswith('Templo:'): d['nombre'] = l.split(':', 1)[1].strip()
        elif re.match(r'(Párroco|Administrador parroquial|Vicario|Rector|Párrocos?)[^:]*:', l): resp.append(l)
        elif l.startswith('Dirección:'):
            parts = [l.split(':', 1)[1].strip()]; k += 1
            while k < len(seg) and not re.match(r'(Teléfono|Email|Horarios)', seg[k]):
                parts.append(seg[k]); k += 1
            d['dir'] = parts; continue
        elif l.startswith('Teléfono:'): d['tel'] = re.sub(r'\D', '', l.split(':', 1)[1])
        k += 1
    d['parroco'] = resp[0].split(':', 1)[1].strip() if resp else ''
    d['rol'] = resp[0].split(':', 1)[0].strip() if resp else ''
    # horarios
    h = {'inv': empty_season(), 'ver': empty_season()}
    obs = []
    sea = None; blk = None; pend = []; in_obs = False
    def volcar():
        nonlocal pend
        if pend and sea:
            for dd in range(5):
                for hh in pend:
                    if hh not in h[sea]['lab'][dd]: h[sea]['lab'][dd].append(hh)
        pend = []
    for l in seg[k + 1:]:
        if l.startswith('Observaciones:'):
            volcar(); obs.append(l.split(':', 1)[1].strip()); in_obs = True; continue
        if in_obs: obs.append(l); continue
        if l in ('Invierno', 'Verano'):
            volcar(); sea = 'inv' if l == 'Invierno' else 'ver'; blk = None; continue
        if sea is None: continue
        m = re.match(r'(Laborables|Visperas|Vísperas|Festivos)\b(.*)', l)
        if m:
            volcar()
            blk = {'laborables': 'lab', 'visperas': 'visp', 'vísperas': 'visp', 'festivos': 'fest'}[m.group(1).lower()]
            rest = m.group(2).strip()
            if not rest: continue
            l = rest
        if blk is None: continue
        if re.fullmatch(r'\d{1,2}[:.]\d{2}', l):
            hh = norm_time(*re.split(r'[:.]', l))
            if blk == 'lab': pend.append(hh)
            elif hh not in h[sea][blk]: h[sea][blk].append(hh)
        elif re.fullmatch(r'[LMXJV](\s*[,y]\s*[LMXJV])*\s*[,.]?', l):
            for dd in [LETRAS[c] for c in re.findall(r'[LMXJV]', l)]:
                for hh in pend:
                    if hh not in h[sea]['lab'][dd]: h[sea]['lab'][dd].append(hh)
            pend = []
    volcar()
    for s in h.values():
        for x in s['lab']: x.sort()
        s['visp'].sort(); s['fest'].sort()
    d['h'] = h
    d['obs'] = ' '.join(obs).strip()
    mod = re.search(r'article:modified_time" content="([^"]+)"', t)
    d['modificado'] = mod.group(1)[:10] if mod else ''
    return d

def run(urls=None, pausa=0.25):
    urls = urls or listar()
    out, fallos = [], []
    for u in urls:
        try:
            t = get(u)
            d = parse(u, t)
            if d: out.append(d)
            else: fallos.append(u)
        except Exception as e:
            fallos.append(u + ' ' + str(e)[:60])
        time.sleep(pausa)
    return out, fallos

if __name__ == '__main__':
    # prueba sobre copias locales: python3 fetch_cadiz.py /ruta/a/*.html
    import glob
    for f in sorted(glob.glob(sys.argv[1])):
        t = open(f, encoding='utf8', errors='ignore').read()
        d = parse('https://www.obispadocadizyceuta.es/parroquias/' + os.path.basename(f)[:-5] + '/', t)
        print(os.path.basename(f), json.dumps(d, ensure_ascii=False)[:0] or '', (d or {}).get('nombre'), (d or {}).get('dir'), (d or {}).get('tel'), 'obs=' + (d or {}).get('obs', '')[:80])
        if d:
            for s in ('inv', 'ver'):
                print('   ', s, d['h'][s])
