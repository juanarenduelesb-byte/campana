"""Diócesis de Huesca: horarios de misas en Huesca capital (https://diocesisdehuesca.org/diocesis/horarios-misas).
Cada templo en mayúsculas, la dirección con «•» y debajo los horarios en texto."""
import re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from misas_lib import get
from texto import interpreta
from norm import titulo
from fuentes._comun import registro, lineas
from fuentes._porlocalidad import bloques

URL = 'https://diocesisdehuesca.org/diocesis/horarios-misas'

def run():
    t = get(URL)
    i = t.find('Horarios en Huesca capital')
    L = lineas(re.sub(r'<(script|style)[^>]*>.*?</\1>', '', t[i:], flags=re.S))
    fin = next((k for k, l in enumerate(L) if l.startswith('¡Síguenos')), len(L))
    out = []
    for nom, _, lin in bloques(L[1:fin]):
        calle = ''
        if lin and '•' in lin[0]:
            calle = re.sub(r'^RESIDENCIA\.\s*', '', lin[0].split('•')[0]).strip(); lin = lin[1:]
        lin = [l for l in lin if not re.match(r'(bautismos|confesiones|despacho)', l, re.I)]
        h, ver, ok, resto = interpreta(lin)
        out.append(registro('hu', nom, titulo(nom), 'Huesca', 'Huesca', 'Huesca', 'Diócesis de Huesca', URL, h, verano=ver, calle=calle,
                            texto=' / '.join(lin), obs=' '.join(resto)))
    return out, []

if __name__ == '__main__':
    o, f = run(); print(len(o))
    for x in o[:4]: print(x['nombre'], '|', x['calle'], '|', x['h']['inv']['lab'][0], x['h']['inv']['visp'], x['h']['inv']['fest'])
