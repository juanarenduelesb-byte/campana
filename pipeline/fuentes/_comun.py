"""Utilidades compartidas por las fuentes nuevas."""
import re, html, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from temporadas import DEFECTO
from norm import titulo

def txt(s):
    return re.sub(r'[ \t]+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s or ''))).strip()

def lineas(fragmento):
    """HTML -> líneas de texto (respeta <br>, <p>, <li>)."""
    s = re.sub(r'<(br|/p|/li|/div|/h\d|/tr)[^>]*>', '\n', fragmento or '', flags=re.I)
    s = html.unescape(re.sub(r'<[^>]+>', ' ', s))
    return [re.sub(r'\s+', ' ', l).strip() for l in s.splitlines() if l.strip()]

def slug(s):
    import unicodedata
    s = ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')[:60]

def registro(pref, clave, nombre, localidad, prov, diocesis, fuente, url, h, **kw):
    r = {'id': pref + '-' + slug(clave), 'nombre': nombre, 'localidad': localidad, 'calle': '', 'num': '', 'cp': '', 'prov': prov, 'tel': '',
         'parroco': '', 'rol': '', 'arciprestazgo': '', 'diocesis': diocesis, 'url': url, 'h': h, 'obs': '', 'texto': '', 'verano': DEFECTO,
         'fuente': fuente, 'actualizado': '', 'idiomas': ['es']}
    r.update({k: v for k, v in kw.items() if v is not None})
    return r

def dentro(lat, lon, bbox):
    return bbox[0] < lat < bbox[2] and bbox[1] < lon < bbox[3]
