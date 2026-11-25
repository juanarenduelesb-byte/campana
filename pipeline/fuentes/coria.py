"""Diócesis de Coria-Cáceres: fichas de parroquias (https://diocesiscoriacaceres.es/misas/) con dirección y «Horario de las Misas» en texto."""
import re, sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from misas_lib import get
from texto import interpreta
from fuentes._comun import registro, lineas

API = 'https://diocesiscoriacaceres.es/wp-json/wp/v2/parroquia?per_page=100&_fields=link&page=%d'

def run(pausa=0.3):
    links = []
    for p in (1, 2, 3):
        try: d = json.loads(get(API % p))
        except Exception: break
        if not isinstance(d, list) or not d: break
        links += [x['link'] for x in d]
    out, fallos = [], []
    for u in links:
        try: t = get(u)
        except Exception: fallos.append(u); continue
        L = lineas(re.sub(r'<(script|style|header|footer|nav)[^>]*>.*?</\1>', '', t, flags=re.S))
        campo = {}
        for l in L:
            m = re.match(r'^(Nombre del Templo|Arciprestazgo|Localidad|Párroco/Responsable|Dirección|Teléfono)\s*:\s*(.*)$', l)
            if m: campo[m.group(1)] = m.group(2).strip()
        i = next((k for k, l in enumerate(L) if l.startswith('Horario de las Misas')), None)
        hl = []
        if i is not None:
            for l in L[i + 1:]:
                if l.startswith(('Buscar por', 'Correo', 'Comienza a escribir', 'Scroll')): break
                hl.append(l)
        h, ver, ok, resto = interpreta(hl)
        dire = campo.get('Dirección', '')
        cp = re.search(r'\b(10\d{3})\b', dire)
        out.append(registro('cc', u.rstrip('/').split('/')[-1], campo.get('Nombre del Templo') or 'Parroquia', campo.get('Localidad', ''), 'Cáceres',
                            'Coria-Cáceres', 'Diócesis de Coria-Cáceres', u, h, verano=ver, calle=dire.split(',')[0] if dire else '',
                            cp=cp.group(1) if cp else '', tel=re.sub(r'\D', '', campo.get('Teléfono', ''))[:9], parroco=campo.get('Párroco/Responsable', ''),
                            arciprestazgo=campo.get('Arciprestazgo', ''), texto=' / '.join(hl), obs=' '.join(resto)))
        time.sleep(pausa)
    return out, fallos

if __name__ == '__main__':
    o, f = run(0.1); print(len(o), 'fallos', len(f))
    vac = [x for x in o if not x['h']['inv']['fest'] and not x['h']['inv']['visp'] and not any(x['h']['inv']['lab'])]
    print('vacías', len(vac), [(x['localidad'], x['texto'][:90]) for x in vac[:8]])
    for x in o[:4]: print(x['nombre'], '|', x['localidad'], '|', x['h']['inv']['lab'][0], x['h']['inv']['visp'], x['h']['inv']['fest'])
