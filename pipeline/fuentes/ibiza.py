"""Obispado de Ibiza: horarios de misas de las iglesias de la ciudad de Ibiza (https://www.obispadodeibiza.es/horarios-de-misas/)."""
import re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from misas_lib import get
from texto import interpreta, horas
from norm import titulo
from fuentes._comun import registro, lineas
from fuentes._porlocalidad import es_localidad

URL = 'https://www.obispadodeibiza.es/horarios-de-misas/'

def run():
    t = get(URL); i = t.find('CATEDRAL SANTA', t.find('<body'))
    L = lineas(re.sub(r'<(script|style)[^>]*>.*?</\1>', '', t[i:], flags=re.S))
    bloques = []; nom = None; buf = []
    for l in L:
        if re.match(r'^(Inicio|Contacto|Obispado de Ibiza|©|Aviso legal|Síguenos)', l): break
        if es_localidad(l) and not re.match(r'^HORARIO', l):
            if nom and not buf: nom += ' ' + l          # nombre partido en dos líneas
            else:
                if nom and buf: bloques.append((nom, buf))
                nom, buf = l, []
            continue
        if nom: buf += [p for p in l.split(' / ') if p.strip()]
    if nom and buf: bloques.append((nom, buf))
    out = []
    for nom, lin in bloques:
        lin = [l for l in lin if not re.match(r'^\(?(tel|telf)', l, re.I) and 'cancelad' not in l.lower()]
        h, ver, ok, resto = interpreta(lin)
        if not ok: continue
        nn = titulo(nom); loc = 'Formentera' if nn.startswith('Formentera') else 'Ibiza'
        nn = re.sub(r'^Formentera\s+', '', nn)
        out.append(registro('ib', nom, nn, loc, 'Baleares', 'Ibiza', 'Obispado de Ibiza', URL, h, verano=ver, texto=' / '.join(lin), obs=' '.join(resto)))
    return out, []

if __name__ == '__main__':
    o, f = run(); print(len(o))
    for x in o: print(x['nombre'], '|', x['h']['inv']['lab'][1], x['h']['inv']['visp'], x['h']['inv']['fest'], '| ver', x['h']['ver']['fest'])
