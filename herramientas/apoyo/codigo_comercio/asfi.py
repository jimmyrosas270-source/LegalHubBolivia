"""Código de Comercio (Decreto Ley 14379) desde el PDF publicado por la ASFI, al formato de contenido/normas/*.txt.
No cambia el texto: lo copia tal cual, con las concordancias entre paréntesis que trae esa edición
(«(Arts. 4º, 590 a 592 Código Civil ...)»), que la página explica en su nota de fuente.
Los rótulos de los artículos de la edición de la ASFI tienen erratas («Art., 94», «Art. 1056» por 1656):
cada artículo se ubica por su número y, si no coincide, por su epígrafe, siguiendo el orden del Código.
Uso: python3 -I asfi.py codigo-asfi.pdf codigo-actual.txt salida.txt informe.txt
(codigo-actual.txt da la lista de artículos y epígrafes esperados; salida.txt es el nuevo texto)."""
import re, sys, subprocess, unicodedata, difflib

src, actual, out, inf = sys.argv[1:5]


def llano(s):
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()


def norm(s):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', s)).strip()


# artículos esperados (número y epígrafe) según el texto que ya se publica
esper = []
for b in re.split(r'\n(?=@ )', open(actual, encoding='utf-8').read())[1:]:
    m = re.match(r'@ (Artículo (\d+)°|Disposición transitoria (\d))\n(?:\(([^)]*)\))?', b)
    if m:
        esper.append({'label': m.group(1), 'n': int(m.group(2) or m.group(3)), 'dt': bool(m.group(3)), 'epi': llano(m.group(4) or '')})

t = subprocess.run(['pdftotext', '-layout', src, '-'], capture_output=True, text=True).stdout
lineas = []
for l in t.replace('\f', '\n').split('\n'):
    l = l.strip()
    if not l or l == 'CODIGO DE COMERCIO':
        continue
    lineas.append(re.sub(r'\s{2,}', ' ', l))
# erratas tipográficas evidentes de la edición de la ASFI (un número en lugar de una letra); no cambian ninguna palabra.
# Se corrigen por pedido del titular (25 nov 2026) y la página de la norma lo advierte.
ERRATAS = [(r'\b1os\b', 'los'), (r'\b1a\b', 'la'), (r'\be1suplente\b', 'el suplente'), (r'\bcua1\b', 'cual'), (r'\bso1amente\b', 'solamente'),
           (r'\bdevo1ución\b', 'devolución'), (r'\baplicab1es\b', 'aplicables'), (r'\b1imitada\b', 'limitada'), (r'\bunif9rmes\b', 'uniformes'),
           (r'\btos pactos\b', 'los pactos'), (r'\bruede\b', 'puede'), (r'\btílulos\b', 'títulos'), (r'\bsortees\b', 'sorteos'), (r'\bea crédito\b', 'el crédito'), (r'\breembolso do las\b', 'reembolso de las'), (r'\bsilos socios\b', 'si los socios')]
corregidas = []
for k, l in enumerate(lineas):
    for x, y in ERRATAS:
        if re.search(x, l):
            corregidas.append(f'{re.search(x, l).group()} → {y}')
            l = re.sub(x, y, l)
    lineas[k] = l
# el Código empieza en «Título Preliminar» (antes: el Decreto Ley que lo aprueba)
k0 = next(i for i, l in enumerate(lineas) if l == 'Título Preliminar')
fuente_txt = norm('\n'.join(lineas))
lineas = lineas[k0:]

CAB = re.compile(r"^Arts?[\s\.,:\-]*((?=[\dl.]*\d)[\dl]{1,2}\.?[\dl]{0,3})\s*[º°o]?[\s\.,:\-–~]*(?=\(|[A-ZÁÉÍÓÚ\"“]|$)")
ESTR = re.compile(r'^(LIBRO|T[IÍ]TULO|CAP[IÍ]TULO|SECCI[OÓ]N)\b(\s+([IVXLC]+|PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|PRELIMINAR|[ÚU]NIC[OA]))?\s*$', re.I)
k_dt = next(i for i, l in enumerate(lineas) if l == 'DISPOSICIONES TRANSITORIAS')
cands = []
for i, l in enumerate(lineas[:k_dt]):
    m = CAB.match(l)
    if m:
        resto = l[m.end():] + ' ' + (lineas[i + 1] if i + 1 < len(lineas) else '')
        e = re.match(r'\(([^)]*)\)', resto)
        cands.append({'i': i, 'n': int(m.group(1).replace('.', '').replace('l', '1')), 'epi': llano(e.group(1)) if e else '', 'fin': m.end()})

informe = []
asig, p = [], 0
for x in [e for e in esper if not e['dt']]:
    elegido = None
    for j in range(p, min(p + 6, len(cands))):
        c = cands[j]
        sim = difflib.SequenceMatcher(None, c['epi'], x['epi']).ratio() if x['epi'] else 0
        if c['n'] == x['n'] and (not x['epi'] or sim > 0.5 or j == p):
            elegido = j; break
        if sim > 0.85:
            elegido = j
            informe.append(f'art. {x["n"]}: la edición de la ASFI lo rotula «{lineas[c["i"]][:30]}» (se ubicó por el epígrafe)')
            break
    if elegido is None:
        informe.append(f'art. {x["n"]}: NO SE ENCONTRÓ en la edición de la ASFI')
        continue
    asig.append((x, cands[elegido]))
    p = elegido + 1

# texto de cada artículo y encabezados de estructura entre artículos
salida = ['=== Código de Comercio', 'slug: codigo-de-comercio', 'tipo: Decreto Ley', 'fecha: 1977-02-25',
          'epigrafe: Decreto Ley 14379 de 25 de febrero de 1977', '']


def estructura(ls):
    """Encabezados (LIBRO, TÍTULO, CAPÍTULO, SECCIÓN y su nombre) al final de un tramo. El nombre puede venir
    en mayúsculas o en minúsculas («Disposiciones Generales») y con punto final."""
    es_estr = lambda l: bool(ESTR.match(l)) or l in ('Título Preliminar', 'Libro Primero')
    k = len(ls)
    while k > 0:
        l = ls[k - 1]
        letras = re.sub(r'[^A-Za-zÁÉÍÓÚÑáéíóúñ]', '', l)
        mayus = letras and l == l.upper() and not re.search(r'[;:,]$', l) and len(l) < 110
        nombre = k >= 2 and es_estr(ls[k - 2]) and len(l) < 80 and not re.search(r'[;:,]$', l)
        if letras and (es_estr(l) or mayus or nombre):
            k -= 1
        else:
            break
    while k < len(ls) and not es_estr(ls[k]):  # el bloque empieza siempre por LIBRO/TÍTULO/CAPÍTULO/SECCIÓN
        k += 1
    bloque = ls[k:]
    secs, cur = [], None
    for l in bloque:
        if es_estr(l):
            if cur and not ESTR.match(cur.split(' · ')[-1]):
                secs.append(cur); cur = l
            else:
                cur = (cur + ' ' + l) if cur else l  # «CAPITULO» + «II» en dos renglones
        else:
            cur = (cur + ' · ' + l) if cur else l
    if cur:
        secs.append(cur)
    return k, secs


def parrafos(ls):
    pars, act = [], ''
    for l in ls:
        if act and re.match(r'^(\d+\)|[a-z]\)|[IVX]+\.)', l):
            pars.append(act); act = l
        else:
            act = (act + ' ' + l) if act else l
        if re.search(r'[.:;]$', l) and not re.search(r'\b(Art|Arts|arts|art|inc|Nº|N°|No|núm|pág|Dr|Sr|S\.A|Ley|D\.S|D\.L|Cía|Ltda|etc|C)\.$', l):
            pars.append(act); act = ''
    if act:
        pars.append(act)
    return pars


k_ini, secs = estructura(lineas[:asig[0][1]['i']])
for s in secs:
    salida += ['§ ' + s, '']
textos = {}
for k, (x, c) in enumerate(asig):
    fin = asig[k + 1][1]['i'] if k + 1 < len(asig) else k_dt
    ls = [lineas[c['i']][c['fin']:].strip()] + lineas[c['i'] + 1:fin]
    ls = [l for l in ls if l]
    kk, secs = estructura(ls)
    cuerpo = ls[:kk]
    pars = parrafos(cuerpo)
    textos[x['n']] = pars
    salida += [f'@ {x["label"]}', '\n\n'.join(pars), '']
    for s in secs:
        salida += ['§ ' + s, '']
# disposiciones transitorias («Art. 1º.» a «Art. 5º.» después del Código)
salida += ['§ DISPOSICIONES TRANSITORIAS', '']
dts = lineas[k_dt + 1:]
bloques, cur = [], None
for l in dts:
    m = re.match(r'^Art\.\s*(\d)\s*[º°o]?\.\s*', l)
    if m:
        cur = [int(m.group(1)), [l[m.end():]]]; bloques.append(cur)
    elif cur:
        cur[1].append(l)
for n, ls in bloques:
    salida += [f'@ Disposición transitoria {n}', '\n\n'.join(parrafos(ls)), '']
texto = '\n'.join(salida).rstrip() + '\n'
# comprobación: cada párrafo está, tal cual, en el texto del PDF
malos = [b[:90] for b in texto.split('\n') if b and b[:1] not in '=@§' and not re.match(r'^(slug|tipo|fecha|epigrafe):', b) and norm(b) not in fuente_txt]
informe.append('erratas corregidas: ' + '; '.join(corregidas))
informe.append(f'artículos: {len(asig)} de {sum(1 for e in esper if not e["dt"])}; disposiciones transitorias: {len(bloques)}; '
               f'secciones: {texto.count(chr(10) + "§ ")}; párrafos que no están en el PDF: {len(malos)}')
informe += ['NO ESTÁ: ' + m for m in malos[:10]]
# correcciones de palabras que no cuadran (correcciones_asfi.json): se aplican después de la comprobación y se informan
import json as _json, os as _os
CORR = _json.load(open(_os.path.join(_os.path.dirname(__file__), 'correcciones_asfi.json'), encoding='utf-8'))
for art, cambios in CORR.items():
    if art.startswith('_'):
        continue
    m = re.search(r'(?ms)^@ Artículo ' + art + r'°\n.*?(?=^@ |\Z)', texto)
    bloque = m.group()
    for viejo, nuevo, _ in cambios:
        assert bloque.count(viejo) == 1, (art, viejo)
        bloque = bloque.replace(viejo, nuevo)
        informe.append(f'art. {art}: «{viejo}» → «{nuevo}»')
    texto = texto[:m.start()] + bloque + texto[m.end():]
open(out, 'w', encoding='utf-8').write(texto)
open(inf, 'w', encoding='utf-8').write('\n'.join(informe) + '\n')
print('\n'.join(informe[-15:]))
