"""Archidiócesis de Granada: buscador de horarios (https://archidiocesisgranada.es/horarios-de-misas-en-granada/).
La página lleva incrustada la tabla completa (capital, área metropolitana y costa) con invierno y verano por laborables, vísperas y festivos."""
import re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from misas_lib import get
from texto import interpreta
from temporadas import temporada_verano, DEFECTO
from fuentes._comun import registro

URL = 'https://archidiocesisgranada.es/horarios-de-misas-en-granada/'
TIPO = {'P': 'Parroquia', 'T': 'Templo', 'M': 'Monasterio', 'H': 'Hospital'}

def _sea(lab, visp, fest):
    """Cada celda ya dice a qué tipo de día pertenece; 'L-V 12:00 · 19:30' puede limitar días."""
    L = ['Laborables: ' + lab if not re.match(r'\s*[LMXJVSD]\s*-', lab) else lab, 'Vísperas: ' + visp, 'Domingos y festivos: ' + fest]
    L = [re.sub(r'\s*·\s*', ', ', x) for x in L]
    L = [re.sub(r'(\d{1,2}:\d{2})', r'\1h', x) for x in L]
    return interpreta(L)[0]['inv']

def run():
    t = get(URL)
    d = t[t.index('>', t.index('id="hm-data"')) + 1:]; d = d[:d.index('</div>')]
    import html as H
    out = []
    for r in H.unescape(d).split('~'):
        f = r.split('|')
        if len(f) < 18: continue
        nombre, tipo, loc = f[0].strip(), f[1], f[3].strip()
        w = _sea(f[8], f[9], f[10]); s = _sea(f[14], f[15], f[16])
        if not any(w['lab']) and not w['visp'] and not w['fest']: w = s
        if not any(s['lab']) and not s['visp'] and not s['fest']: s = w
        ver = temporada_verano('verano (' + f[13] + ')') if f[13] else DEFECTO
        barrio = re.match(r'^([^(]+?)\s*\((.+)\)$', loc)
        calle = ''
        if barrio:
            loc, extra = barrio.group(1), barrio.group(2)
            if re.search(r'\d|calle|plaza', extra, re.I): calle = extra
        nom = nombre if tipo != 'P' or nombre.lower().startswith(('parroquia', 'santuario', 'basílica', 'catedral')) else nombre
        obs = ' '.join(x for x in (f[11].strip(), f[17].strip()) if x)
        out.append(registro('gr', f[4] or nombre + loc, nom, loc, 'Granada', 'Granada', 'Archidiócesis de Granada', URL + '?p=' + f[4],
                            {'inv': w, 'ver': s}, verano=ver or DEFECTO, obs=obs, calle=calle, rol=TIPO.get(tipo, '')))
    return out, []

if __name__ == '__main__':
    o, _ = run(); print(len(o))
    for x in o[:4] + o[60:62]: print(x['nombre'], '|', x['localidad'], '|', x['h']['inv']['lab'][0], x['h']['inv']['visp'], x['h']['inv']['fest'], '| ver', x['h']['ver']['fest'], x['verano'])
    print(sum(1 for x in o if not x['h']['inv']['fest']), 'sin domingo')
