"""Cuándo empieza el horario de verano en cada parroquia (se lee de sus observaciones; por defecto, del 1 de junio al 30 de septiembre)."""
import re
MESES = {'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8, 'septiembre': 9, 'setiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12}
DEFECTO = [6, 1, 9, 30]

def temporada_verano(texto):
    """Devuelve [mes_ini, dia_ini, mes_fin, dia_fin] o 'dst' (cambio oficial de hora)."""
    t = (texto or '').lower().replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
    if re.search(r'cambio (de hora|horario|oficial)', t):
        return 'dst'
    # "verano (del 1 de mayo al 30 de septiembre)"
    m = re.search(r'verano[^a-z0-9]{0,6}(?:del?|desde(?: el)?)\s*(\d{1,2})\s*(?:de\s*)?([a-z]+)\s*(?:al|hasta(?: el)?)\s*(\d{1,2})\s*(?:de\s*)?([a-z]+)', t)
    if m and m.group(2) in MESES and m.group(4) in MESES:
        return [MESES[m.group(2)], int(m.group(1)), MESES[m.group(4)], int(m.group(3))]
    # "verano (de junio a septiembre)" / "junio a septiembre" / "meses de junio, julio, agosto y septiembre"
    m = re.search(r'verano[^a-z0-9]{0,6}(?:de|desde|del)?\s*([a-z]+)\s*(?:a|hasta)\s*([a-z]+)', t)
    if m and m.group(1) in MESES and m.group(2) in MESES:
        return [MESES[m.group(1)], 1, MESES[m.group(2)], 30]
    m = re.search(r'verano[^.]*?meses de ([a-z, y]+)', t) or re.search(r'verano[^.]*?(?:comprendido entre los meses de|entre los meses de)\s*([a-z, y]+)', t)
    if m:
        ms = [MESES[x] for x in re.findall(r'[a-z]+', m.group(1)) if x in MESES]
        if ms: return [min(ms), 1, max(ms), 30]
    m = re.search(r'verano\s*\(([^)]{0,80})\)', t)
    if m:
        ms = [MESES[x] for x in re.findall(r'[a-z]+', m.group(1)) if x in MESES]
        if ms: return [min(ms), 1, max(ms), 30]
    m = re.search(r'junio a septiembre|octubre a mayo', t)
    if m: return DEFECTO
    if re.search(r'verano finaliza el (\d{1,2}) de ([a-z]+)', t):
        m = re.search(r'verano finaliza el (\d{1,2}) de ([a-z]+)', t)
        if m.group(2) in MESES: return [6, 1, MESES[m.group(2)], int(m.group(1))]
    return DEFECTO

if __name__ == '__main__':
    for x in ['El horario de Verano queda comprendido entre los meses de Julio, Agosto y Septiembre.', 'El horario de verano comprende los meses de mayo, junio, julio y agosto.', 'INVIERNO (del 1 de octubre al 30 de abril) VERANO (mayo, junio, julio, agosto y septiembre)', 'INVIERNO (Desde 1 de octubre a 30 de abril) VERANO (Desde el 1 de mayo al 30 de septiembre)', 'El cambio del horario de invierno y verano se hace con el cambio de hora correspondiente a', 'VERANO (de junio a septiembre)', 'El horario de verano finaliza el 15 de septiembre', 'INVIERNO: (Del 15 septiembre al 15 de mayo) VERANO: (Del 15 mayo al 15 septiembre)', '']:
        print(temporada_verano(x), '<-', x[:70])
