"""Separa el TEXTO DE LA LEY del Código de Comercio (Decreto Ley 14379) de una edición anotada:
quita los precedentes y concordancias («Precd:», «Conc:») y los comentarios doctrinales que siguen a cada artículo,
y conserva solo los artículos y los encabezados de libro, título, capítulo y sección.
Uso: python3 -I extraer.py edicion-anotada.pdf salida.txt informe.txt
El resultado tiene el formato de contenido/normas/<materia>/*.txt (=== norma, § sección, @ Artículo)."""
import subprocess, re, sys

src, out, inf = sys.argv[1:4]
t = subprocess.run(['pdftotext', src, '-'], capture_output=True, text=True).stdout
t = t.replace('\f', '\n')
t = re.sub(r'\n?Descargado desde el sitio www\.bolivianland\.net\s*\nPágina \d+\s*\n', '\n', t)
assert 'bolivianland' not in t
t = t.replace('CAP╓TULO', 'CAPÍTULO')  # carácter dañado en un encabezado de la fuente
# encabezados de estructura pegados al final de un renglón de concordancias: se pasan a su propio renglón
t = re.sub(r'(?<=\S)[ \t]*((?:LIBRO|T[IÍ]TULO|CAP[IÍ]TULO|SECCI[OÓ]N)\s+(?:[IVXL]+|PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|PRELIMINAR|[ÚU]NIC[OA])\b)', r'\n\1', t)
CAB = re.compile(r'ART[IÍ]CULOS?\.?\s+((?:\d|l)\.\d{3}|\d{1,2}\.\d{3}|\d+)\s*[º°]?\s*(?:[\.\-–]\s*){1,3}(?=\(|[A-ZÁÉÍÓÚÑ¿"“])')
num = lambda x: int(x.group(1).replace('l', '1').replace('.', ''))
FIN = re.compile(r'(?:(?<=\s)|(?<=^))(Precd\s*[:.]?|Conc\s*[:.\-]|Conc\s+(?=c\.|C\.|Const|p\.\s?c|loj|L\.|D\.\s?S|DD|Rgto|Tdo)|Con:)')
ESTR = re.compile(r'^(LIBRO|T[IÍ]TULO|CAP[IÍ]TULO|SECCI[OÓ]N)\b')

# 1) encabezados de artículo en orden (el número debe seguir al anterior)
heads, prev, pos = [], 0, 0
while True:
    m = None
    for x in CAB.finditer(t, pos):
        n = num(x)
        if n == prev + 1 or (prev and 1 < n - prev <= 3 and not re.search(r'ART[IÍ]CULO\s+%s\b' % (prev + 1), t[pos:x.start()])):
            m = x
            break
    if not m:
        break
    heads.append(m)
    prev, pos = num(m), m.end()

informe = []
salida = ['=== Código de Comercio', 'slug: codigo-de-comercio', 'tipo: Decreto Ley', 'fecha: 1977-02-25',
          'epigrafe: Decreto Ley 14379 de 25 de febrero de 1977', '']
nums = [num(h) for h in heads]
falt = sorted(set(range(1, max(nums) + 1)) - set(nums))
informe.append(f'artículos: {len(nums)}; último {max(nums)}; faltan {falt}')


def estructura(segmento):
    """Encabezados (todas mayúsculas) al final del tramo de comentario, justo antes del artículo siguiente."""
    ls = [l.strip() for l in segmento.split('\n')]
    while ls and not ls[-1]:
        ls.pop()
    bloque = []
    while ls:
        l = ls[-1]
        if not l:
            ls.pop(); continue
        letras = re.sub(r'[^A-Za-zÁÉÍÓÚÑÜáéíóúñü]', '', l)
        if letras and letras == letras.upper() and len(l) < 120:
            bloque.insert(0, l); ls.pop()
        else:
            break
    # solo cuenta si empieza por LIBRO/TÍTULO/CAPÍTULO/SECCIÓN
    k = next((i for i, l in enumerate(bloque) if ESTR.match(l)), None)
    if k is None:
        # rubro sin número (en la fuente faltan, por ejemplo, «CAPÍTULO IV» y «CAPÍTULO VII» del mercado de valores)
        if bloque and len(' '.join(bloque)) < 120 and not any(l.endswith(('.', ':', ';', ',')) for l in bloque):
            return [' · '.join(bloque)]
        return []
    bloque = bloque[k:]
    secs, cur = [], None
    for l in bloque:
        if ESTR.match(l):
            if cur: secs.append(cur)
            cur = l
        else:
            cur = (cur + ' · ' + l) if cur else l
    if cur: secs.append(cur)
    return secs


# las disposiciones transitorias van después del art. 1693 y antes de la tabla de abreviaturas del editor
k_dt = t.index('DISPOSICIONES TRANSITORIAS', heads[-1].end())
k_ab = t.index('ABREVIATURAS', k_dt)
transitorias = t[k_dt + len('DISPOSICIONES TRANSITORIAS'):k_ab]
t = t[:k_dt]
inicio = t[:heads[0].start()]
for s in estructura(inicio):
    salida += ['§ ' + s, '']
for i, h in enumerate(heads):
    sig = heads[i + 1].start() if i + 1 < len(heads) else len(t)
    tramo = t[h.end():sig]
    f = FIN.search(tramo)
    if f:
        cuerpo, resto = tramo[:f.start()], tramo[f.start():]
    else:
        cuerpo, resto = tramo, tramo
        secs_ = estructura(tramo)
        if secs_:
            # el bloque de encabezados del final no es parte del artículo
            k_ = max(tramo.rfind(x.split(' · ')[0]) for x in secs_[:1])
            cuerpo = tramo[:k_]
        informe.append(f'art. {num(h)}: sin «Precd/Conc» ({len(tramo)} caracteres)')
    cuerpo = cuerpo.strip()
    # párrafos: un renglón que termina en punto, dos puntos o punto y coma cierra párrafo; el resto se une
    pars, actual = [], ''
    for l in cuerpo.split('\n'):
        l = l.strip()
        if not l:
            continue
        if actual and (re.match(r'^(\d+\)|[a-z]\)|[IVX]+\.|\d+\.)\s', l)):
            pars.append(actual); actual = l
        else:
            actual = (actual + ' ' + l) if actual else l
        if re.search(r'[.:;]$', l) and not re.search(r'\b(Art|arts|inc|Nº|N°|No|núm|pág|Dr|Sr|S\.A)\.$', l):
            pars.append(actual); actual = ''
    if actual:
        pars.append(actual)
    salida.append(f'@ Artículo {num(h)}°')
    salida.append('\n\n'.join(pars))
    salida.append('')
    if len(cuerpo) > 4000:
        informe.append(f'art. {num(h)}: texto largo ({len(cuerpo)})')
    for s in estructura(resto):
        salida += ['§ ' + s, '']
salida += ['§ DISPOSICIONES TRANSITORIAS', '']
dts = re.split(r'ART[IÍ]CULO\s+(\d)\s*\.\s*-\s*', transitorias)
assert dts[0].strip() == '' and len(dts) == 11, len(dts)
for k in range(1, len(dts), 2):
    salida += [f'@ Disposición transitoria {dts[k]}', re.sub(r'\s+', ' ', dts[k + 1]).strip(), '']
informe.append(f'disposiciones transitorias: {len(dts) // 2}')
open(out, 'w', encoding='utf-8').write('\n'.join(salida).rstrip() + '\n')
open(inf, 'w', encoding='utf-8').write('\n'.join(informe) + '\n')
print('\n'.join(informe[:40]))
