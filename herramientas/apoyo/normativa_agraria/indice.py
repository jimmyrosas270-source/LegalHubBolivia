"""Genera contenido/compilaciones/<archivo>.json: los artículos de cada norma de la compilación «Normativa Agraria»
del INRA, con la página del PDF donde empieza cada uno y su texto (para el buscador del sitio).
Uso: python3 -I indice.py biblioteca/pdf/agraria/compilacion-normativa-agraria-inra.pdf contenido/compilaciones/compilacion-normativa-agraria-inra.json   (las normas y sus páginas están en NORMAS)."""
import subprocess, re, sys, json

f, out = sys.argv[1], sys.argv[2]
pags = subprocess.run(['pdftotext', f, '-'], capture_output=True, text=True).stdout.split('\f')
CAB = 'Normativa Agraria en la Era de la Reconducción Comunitaria de la Reforma Agraria (2006-2010)'

# clave, título, tipo, número, fecha, página inicial y final del PDF, descripción breve propia, alias, ¿índice por artículos?
NORMAS = [
    ('1715', 'Ley 1715 del Servicio Nacional de Reforma Agraria (texto ordenado con la Ley 3545)', 'Ley', '1715', '18 de octubre de 1996', 7, 75,
     'Texto de la Ley 1715 con las modificaciones de la Ley 3545 intercaladas en recuadros.', ['Ley INRA', 'INRA', 'Ley 1715', 'Texto ordenado de la Ley 1715'], True),
    ('3545', 'Ley 3545 de Reconducción Comunitaria de la Reforma Agraria', 'Ley', '3545', '28 de noviembre de 2006', 9, 75,
     'Sus artículos están intercalados, en recuadros, dentro del texto ordenado de la Ley 1715.', ['Ley 3545', 'Reconducción comunitaria'], True),
    ('29215', 'Decreto Supremo 29215 · Reglamento de la Ley 1715 y de la Ley 3545', 'Decreto Supremo', '29215', '2 de agosto de 2007', 77, 251,
     'Reglamento agrario: saneamiento, distribución de tierras, reversión, expropiación y otros procedimientos del INRA.', ['DS 29215', 'Reglamento agrario', 'Reglamento de la Ley INRA'], True),
    ('29062', 'Decreto Supremo 29062 · Pausa y procedimiento especial de verificación de la FES por desastres naturales', 'Decreto Supremo', '29062', '15 de marzo de 2007', 253, 258,
     'Pausa y verificación especial de la función económico social en predios afectados por «El Niño 2006-2007».', ['DS 29062'], True),
    ('29452', 'Decreto Supremo 29452 · Pausa y verificación especial de la FES («La Niña 2007-2008»)', 'Decreto Supremo', '29452', '22 de febrero de 2008', 259, 262,
     'Pausa y verificación especial de la función económico social en predios afectados por «La Niña 2007-2008».', ['DS 29452'], True),
    ('0243', 'Decreto Supremo 0243 · Saneamiento de predios agrarios de las Fuerzas Armadas', 'Decreto Supremo', '0243', '7 de agosto de 2009', 263, 270,
     'Reglamenta el saneamiento de los predios agrarios de las Fuerzas Armadas.', ['DS 0243', 'DS 243'], True),
    ('0257', 'Decreto Supremo 0257 · Asentamientos humanos', 'Decreto Supremo', '0257', '19 de agosto de 2009', 271, 278,
     'Programas de asentamientos humanos.', ['DS 0257', 'DS 257'], True),
    ('29802', 'Decreto Supremo 29802 · Sistemas servidumbrales, trabajo forzoso y peonazgo por deudas en materia agraria', 'Decreto Supremo', '29802', '19 de noviembre de 2008', 279, 284,
     'Sistemas servidumbrales, trabajo forzoso, peonazgo por deudas y esclavitud de familias o personas cautivas en materia agraria.', ['DS 29802', 'Relaciones servidumbrales'], True),
    ('0388', 'Decreto Supremo 0388 · Aprueba el reglamento para verificar la existencia de relaciones servidumbrales', 'Decreto Supremo', '0388', '23 de diciembre de 2009', 285, 286,
     'Aprueba el reglamento con que el INRA verifica, comprueba y determina la existencia de sistemas servidumbrales.', ['DS 0388', 'DS 388'], True),
    ('0388r', 'Reglamento para la verificación de relaciones servidumbrales, trabajo forzoso y formas análogas (anexo del DS 0388)', 'Reglamento', '', '23 de diciembre de 2009', 287, 298,
     'Criterios, metodología y procedimiento del INRA para verificar relaciones servidumbrales en el saneamiento y la reversión.', ['Reglamento de relaciones servidumbrales'], True),
    ('29824', 'Decreto Supremo 29824 · Personalidades jurídicas otorgadas por el Presidente (negativa tácita)', 'Decreto Supremo', '29824', '28 de noviembre de 2008', 299, 304,
     'Personalidades jurídicas que otorga el Presidente en casos de negativa tácita.', ['DS 29824'], True),
    ('29354', 'Decreto Supremo 29354 · Expropiación por utilidad pública a favor del Pueblo Indígena Guaraní de Chuquisaca', 'Decreto Supremo', '29354', '28 de noviembre de 2007', 305, 312,
     'Causal de expropiación por reagrupamiento y redistribución de tierras con fines de dotación al Pueblo Guaraní de Chuquisaca.', ['DS 29354'], True),
    ('cpe', 'Constitución Política del Estado · artículos relacionados con la temática agraria', 'Constitución', '', '7 de febrero de 2009', 313, 318,
     'Selección de artículos de la Constitución sobre tierra y territorio.', [], False),
]

R = re.compile(r'^\s*ART[IÍ]CULO\s+(\d+)\s*([º°])?\s*([\.\-–]*)\s*(.*)$', re.I)


def limpia(t):
    t = re.sub(r'\|\s*\d+\s*\|', ' ', t.replace(CAB, ' '))
    t = re.sub(r'-\n(?=[a-záéíóúñ])', '', t)
    return re.sub(r'\s+', ' ', t).strip()


def cabeceras(ini, fin):
    """(página, número, ¿lleva º?, resto de la línea, índice de línea) de cada encabezado de artículo."""
    res = []
    for p in range(ini, fin + 1):
        lineas = pags[p - 1].splitlines()
        for j, l in enumerate(lineas):
            m = R.match(l)
            if not m or l.strip()[:8].upper() not in ('ARTICULO', 'ARTÍCULO'):
                continue
            resto = m.group(4)
            # encabezado de verdad: lleva el título entre paréntesis, «.-» o «º»; no una referencia partida en dos renglones
            if not (resto.startswith('(') or '-' in m.group(3) or m.group(2) or (m.group(3) == '.' and resto[:1].isupper())):
                continue
            res.append((p, int(m.group(1)), bool(m.group(2)), resto, j))
    return res


def texto_entre(a, b):
    """Texto desde el encabezado a hasta el encabezado b (o el final de la norma)."""
    (p1, j1), (p2, j2) = a, b
    partes = []
    for p in range(p1, p2 + 1):
        ls = pags[p - 1].splitlines()
        desde = j1 if p == p1 else 0
        hasta = j2 if p == p2 else len(ls)
        partes.append('\n'.join(ls[desde:hasta]))
    return limpia('\n'.join(partes))


salida = {'archivo': f.replace('\\', '/').split('/')[-1], 'LEEME': 'Normas que contiene la compilación y página del PDF donde empieza cada artículo. Generado por herramientas/apoyo/normativa_agraria/indice.py; '
          'el texto solo alimenta el buscador (el texto legal es el del PDF).', 'normas': []}
cab_1715 = cabeceras(7, 75)
asig = {'1715': [], '3545': []}
ult = {'1715': 0, '3545': 0}
for c in cab_1715:
    p, n, grado, resto, j = c
    if not resto.startswith('('):
        continue
    if grado and 0 < n - ult['1715'] <= 5:
        k = '1715'
    elif not grado and n == ult['3545'] + 1:
        k = '3545'
    elif 0 < n - ult['1715'] <= 3:
        k = '1715'
    elif 0 < n - ult['3545'] <= 3:
        k = '3545'
    else:
        print('omitido', c[:4])
        continue
    asig[k].append(c)
    ult[k] = n
todas = sorted(cab_1715, key=lambda c: (c[0], c[4]))

for clave, titulo, tipo, num, fecha, ini, fin, desc, alias, por_art in NORMAS:
    norma = {'clave': clave, 'titulo': titulo, 'tipo': tipo, 'numero': num, 'fecha': fecha, 'pagina': ini, 'hasta': fin,
             'descripcion': desc, 'alias': alias, 'articulos': []}
    if por_art:
        if clave in asig:
            cs, limites = asig[clave], todas
        else:
            cs = []
            ult_n = 0
            for c in cabeceras(ini, fin):
                if c[1] == ult_n + 1 or (ult_n == 0 and c[1] == 1):
                    cs.append(c); ult_n = c[1]
                else:
                    print(clave, 'omitido', c[:4])
            limites = cs
        for c in cs:
            # el texto llega hasta el siguiente encabezado de cualquier norma (o el final de la norma)
            sig = next(((x[0], x[4]) for x in limites if (x[0], x[4]) > (c[0], c[4])), None)
            if sig is None or sig[0] > fin:
                sig = (fin, 10 ** 6)
            norma['articulos'].append({'n': c[1], 'pagina': c[0], 'titulo': re.sub(r'^\(([^)]*)\).*', r'\1', c[3]).strip() if c[3].startswith('(') else '',
                                       'texto': texto_entre((c[0], c[4]), sig)[:600]})
        nums = [a['n'] for a in norma['articulos']]
        faltan = sorted(set(range(1, max(nums) + 1)) - set(nums)) if nums else []
        print(clave, len(nums), 'artículos; faltan', faltan[:20])
    salida['normas'].append(norma)
json.dump(salida, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
