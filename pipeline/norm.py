"""Normalización de nombres."""
import re
PEQ = {'de', 'del', 'la', 'las', 'los', 'el', 'y', 'e', 'en', 'a'}
ACENTOS = {'Linea': 'Línea', 'Concepcion': 'Concepción', 'Martin': 'Martín', 'Estacion': 'Estación', 'Espiritu': 'Espíritu', 'Pio': 'Pío',
           'Andalucia': 'Andalucía', 'Maria': 'María', 'Jose': 'José', 'Agustin': 'Agustín', 'Garcia': 'García', 'Santisima': 'Santísima',
           'Angel': 'Ángel', 'Roque': 'Roque', 'Fra.': 'Frontera', 'Ildefonso': 'Ildefonso', 'Alcantara': 'Alcántara', 'Rocio': 'Rocío',
           'Ojen': 'Ojén', 'Benahavis': 'Benahavís', 'Istan': 'Istán', 'Gaucin': 'Gaucín', 'Mayorga': 'Mayorga', 'Santisimo': 'Santísimo'}
def titulo(s):
    s = re.sub(r'\s+', ' ', s or '').strip().rstrip('.')
    s = re.sub(r'\s+-\s*', ' – ', s)
    out = []
    for i, w in enumerate(s.split(' ')):
        lw = w.lower()
        if i > 0 and lw in PEQ: out.append(lw); continue
        w2 = w[:1].upper() + w[1:].lower() if w.isupper() or w.islower() or w == w.title() else w
        out.append(ACENTOS.get(w2, w2))
    return ' '.join(out)

