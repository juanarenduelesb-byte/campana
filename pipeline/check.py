"""Comprobaciones antes de publicar: si algo no cuadra, el job falla y Cloudflare sigue sirviendo la versión anterior."""
import json, os, re, sys
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'site', 'misas.js')
t = open(p, encoding='utf8').read()
d = json.loads(t[t.index('=') + 1:].rstrip(';\n'))
I = d['i']; err = []
if len(I) < 60: err.append(f'solo {len(I)} iglesias')
if sum(1 for x in I if x['interpretado']) < 0.7 * len(I): err.append('demasiados horarios sin interpretar')
if sum(1 for x in I if x['id'].startswith('l-')) < 4: err.append('faltan las iglesias de Sotogrande')
if any(not (35.8 < x['lat'] < 36.8 and -5.95 < x['lon'] < -4.7) for x in I): err.append('coordenadas fuera de la zona')
ok = re.compile(r'^([01]\d|2[0-3]):[0-5]\d$')
def horas(h): return [t for s in h.values() for t in s['lab'] for t in t] + [t for s in h.values() for k in ('visp', 'fest') for t in s[k]]
if any(not ok.match(t) for x in I for t in horas(x['h'])): err.append('horas con formato inválido')
if len({x['id'] for x in I}) != len(I): err.append('ids repetidos')
print(f'{len(I)} iglesias, {sum(1 for x in I if x["interpretado"])} con horario, fallos de fuente: {d["meta"].get("fallos")}')
if err: print('ERROR:', '; '.join(err)); sys.exit(1)
