"""Comprobaciones antes de publicar: si algo no cuadra, el job falla y Cloudflare sigue sirviendo la versión anterior."""
import json, os, re, sys
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'site', 'data')
idx = json.load(open(os.path.join(DATA, 'indice.json'), encoding='utf8'))
err = []; aviso = []
ok_h = re.compile(r'^([01]\d|2[0-3]):[0-5]\d$')
def horas(h): return [t for s in h.values() for l in s['lab'] for t in l] + [t for s in h.values() for k in ('visp', 'fest') for t in s[k]]
ids = set(); total = 0
if len(idx['dioc']) < 3: err.append('faltan diócesis en el índice')
for d in idx['dioc']:
    try:
        t = open(os.path.join(DATA, d['id'] + '.js'), encoding='utf8').read()
        I = json.loads(t[t.index(']=') + 2:t.rindex(';')])
    except Exception as e:
        err.append(f"{d['nombre']}: archivo ilegible ({e})"); continue
    total += len(I)
    if len(I) != d['n']: err.append(f"{d['nombre']}: el índice dice {d['n']} y hay {len(I)}")
    if len(I) < 20: err.append(f"{d['nombre']}: solo {len(I)} iglesias")
    if sum(1 for x in I if x['interpretado']) < 0.6 * len(I): err.append(f"{d['nombre']}: demasiados horarios sin interpretar")
    b = d['bbox']
    if any(not (27 < x['lat'] < 44.5 and -19 < x['lon'] < 5) for x in I): err.append(f"{d['nombre']}: coordenadas fuera de España")
    if any(not ok_h.match(t) for x in I for t in horas(x['h'])): err.append(f"{d['nombre']}: horas con formato inválido")
    for x in I:
        if x['id'] in ids: err.append('id repetido ' + x['id']); break
        ids.add(x['id'])
    if d['id'] == 'cadiz' and sum(1 for x in I if x['id'].startswith('l-')) < 4: err.append('faltan las iglesias de Sotogrande')
    if d['estado'] != 'ok': aviso.append(d['nombre'] + ' (datos antiguos)')
print(f"{len(idx['dioc'])} diócesis, {total} iglesias. Avisos: {aviso or 'ninguno'}")
if err: print('ERROR:', '; '.join(err)); sys.exit(1)
