"""Recalcula el índice (número de iglesias, con horario y zona) a partir de los archivos de cada diócesis."""
import json, os
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'site', 'data')
p = os.path.join(DATA, 'indice.json'); idx = json.load(open(p, encoding='utf8'))
for d in idx['dioc']:
    t = open(os.path.join(DATA, d['id'] + '.js'), encoding='utf8').read()
    I = json.loads(t[t.index(']=') + 2:t.rindex(';')])
    la = [x['lat'] for x in I]; lo = [x['lon'] for x in I]
    d.update(n=len(I), ok=sum(1 for x in I if x['interpretado']), bbox=[round(min(la), 3), round(min(lo), 3), round(max(la), 3), round(max(lo), 3)])
open(p, 'w', encoding='utf8').write(json.dumps(idx, ensure_ascii=False))
open(os.path.join(DATA, 'indice.js'), 'w', encoding='utf8').write('window.CAMPANA_IDX=' + json.dumps(idx, ensure_ascii=False, separators=(',', ':')) + ';\n')
print(len(idx['dioc']), 'diócesis,', sum(d['n'] for d in idx['dioc']), 'iglesias')
