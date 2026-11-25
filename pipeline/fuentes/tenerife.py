"""Diócesis de San Cristóbal de La Laguna (Tenerife, La Palma, La Gomera y El Hierro): tablas de horarios por arciprestazgo
(https://www.obispadodetenerife.com/horarios-misas-tenerife/). Columnas: laborables, sábados y vísperas, domingos y festivos.
Un asterisco marca el horario de verano."""
import re, sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from misas_lib import get, empty_season
from texto import horas, dias
from fuentes._comun import registro, txt

BASE = 'https://www.obispadodetenerife.com/horarios-misas-tenerife/'

MUNI = {'el-hierro': 'Valverde', 'granadilla': 'Granadilla de Abona', 'guia-de-isora': 'Guía de Isora', 'guimar': 'Güímar',
        'icod-de-los-vinos': 'Icod de los Vinos', 'la-cuesta': 'San Cristóbal de La Laguna', 'la-gomera': 'San Sebastián de La Gomera',
        'la-laguna': 'San Cristóbal de La Laguna', 'la-orotava': 'La Orotava', 'la-salud': 'Santa Cruz de Tenerife', 'los-llanos-de-aridane': 'Los Llanos de Aridane',
        'ofra': 'Santa Cruz de Tenerife', 'santa-cruz-de-la-palma': 'Santa Cruz de La Palma', 'taco': 'San Cristóbal de La Laguna', 'tacoronte': 'Tacoronte',
        'tegueste': 'Tegueste', 'santa-cruz-de-tenerife': 'Santa Cruz de Tenerife'}

def _min(t): return int(t[:2]) * 60 + int(t[3:])

def celda(c):
    """'19,00 – 19,30*' -> (invierno, verano)."""
    c = c.replace('—', ' ').replace('–', ' - ')
    est, nor = [], []
    for m in re.finditer(r'(?<![\d:.,])(2[0-3]|[01]?\d)\s*[:.,]\s*([0-5]\d)(\s*\*)?', c):
        t = '%02d:%s' % (int(m.group(1)), m.group(2))
        (est if m.group(3) else nor).append(t)
    inv = sorted(set(nor))
    ver = sorted(set(est + [t for t in nor if not any(abs(_min(t) - _min(e)) <= 90 for e in est)]))
    return inv, ver

def _poner(sea, k, ts, dd=None):
    for t in ts:
        if k == 'lab':
            for d in (dd or range(5)):
                if d < 5 and t not in sea['lab'][d]: sea['lab'][d].append(t)
        elif t not in sea[k]: sea[k].append(t)

def run(pausa=0.5):
    idx = get(BASE)
    pags = sorted(set(re.findall(r'href="(' + re.escape(BASE) + r'[a-z0-9-]+/)"', idx)))
    out, fallos = [], []
    for u in pags:
        try: t = get(u)
        except Exception as e: fallos.append(u); continue
        sl = u.rstrip('/').split('/')[-1].replace('horarios-de-misas-', '').replace('arciprestazgo-', '').replace('de-', '', 1) if False else u.rstrip('/').split('/')[-1]
        sl = re.sub(r'^(horarios-de-misas-)?arciprestazgo-(de-)?', '', sl)
        zona = MUNI.get(sl, 'Santa Cruz de Tenerife'); arc = 'Arciprestazgo de ' + sl.replace('-', ' ').title()
        for tabla in re.findall(r'<table.*?</table>', t, re.S):
            for fila in re.findall(r'<tr[^>]*>(.*?)</tr>', tabla, re.S):
                cs = [txt(re.sub(r'<br\s*/?>', ' ', x)) for x in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', fila, re.S)]
                if cs and re.match(r'zona', cs[0], re.I) and not any(cs[1:]):
                    zona = re.sub(r'^zona( de|:)?\s*', '', cs[0], flags=re.I).strip(); continue
                if len(cs) < 4 or re.match(r'parroquias?$', cs[0], re.I) or not cs[0]: continue
                nombre = cs[0]
                barrio = re.search(r'\(([^)]+)\)', nombre)
                h = {'inv': empty_season(), 'ver': empty_season()}
                d, lab, _, _ = dias(cs[1])
                dd = sorted(x for x in d if x < 5) or None
                for k, c in (('lab', cs[1]), ('visp', cs[2]), ('fest', cs[3])):
                    i, v = celda(c)
                    _poner(h['inv'], k, i, dd if k == 'lab' else None); _poner(h['ver'], k, v, dd if k == 'lab' else None)
                for s in h.values():
                    for l in s['lab']: l.sort()
                    s['visp'].sort(); s['fest'].sort()
                limpio = re.sub(r'\s*\([^)]*\)', '', nombre).strip(' –-')
                loc = zona or 'Tenerife'
                texto = f'Laborables: {cs[1]} / Sábados y vísperas: {cs[2]} / Domingos y festivos: {cs[3]}'
                out.append(registro('tf', loc + '-' + nombre, limpio, loc, 'Santa Cruz de Tenerife', 'Tenerife', 'Obispado de Tenerife', u, h,
                                    calle=barrio.group(1) if barrio else '', arciprestazgo=arc, texto=texto,
                                    obs='Horario de verano según los asteriscos de la tabla oficial.' if '*' in ''.join(cs[1:4]) else ''))
        time.sleep(pausa)
    return out, fallos

if __name__ == '__main__':
    o, f = run(); print(len(o), 'fallos', f)
    import collections; print(collections.Counter(x['localidad'] for x in o).most_common(30))
    for x in o[:6]: print(x['nombre'], '|', x['calle'], '|', x['localidad'], '|', x['h']['inv']['lab'], x['h']['inv']['visp'], x['h']['inv']['fest'], '| ver', x['h']['ver']['visp'])
