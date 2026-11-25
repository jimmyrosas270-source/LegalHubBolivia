"""Pasa una ley o código en PDF (con texto) al formato de contenido/normas/<materia>/*.txt
(=== norma, § sección, @ Artículo N, @ Disposición ...), para publicarla artículo por artículo.
No cambia el texto: quita solo encabezados y pies de página repetidos, números de página y lo que la configuración
de cada norma manda quitar (por ejemplo concordancias de una compilación). Al final comprueba que cada renglón
publicado esté, tal cual, en el texto del PDF.
Uso: python3 -I extraer.py <clave>   (las claves y su configuración están en NORMAS, abajo)
     python3 -I extraer.py todas"""
import subprocess, re, sys, os, unicodedata

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
ORD = ('PRIMERA|SEGUNDA|TERCERA|CUARTA|QUINTA|SEXTA|S[ÉE]PTIMA|OCTAVA|NOVENA|D[ÉE]CIMA(?:\\s+(?:PRIMERA|SEGUNDA|TERCERA|CUARTA|QUINTA|SEXTA|S[ÉE]PTIMA|OCTAVA|NOVENA))?'
       '|UND[ÉE]CIMA|DUOD[ÉE]CIMA|VIG[ÉE]SIMA(?:\\s+(?:PRIMERA|SEGUNDA|TERCERA|CUARTA|QUINTA|SEXTA|S[ÉE]PTIMA|OCTAVA|NOVENA))?|[ÚU]NICA')
SUF = r'(bis|ter|qu[aá]ter|quinquies|sexies|septies|octies|nonies)'
ART = re.compile(r"^(?:ART[IÍ]CULO|Art[ií]culo|ARTICULO|Arts?[\.,]?|Ar\.)\.?\s*"+r'(\d+)\s*[º°o]?\s*' + r'(?:\s*' + SUF + r'\b)?\s*(?:[\.\-–—:,]+\s*|\s+(?=[\(A-ZÁÉÍÓÚ"“])|$)', re.I)
NUMSOLO = re.compile(r'^(\d{2,4})()\s*[\.\-]+\s*(?=\()')  # «657.- (DONACION…)»: el rótulo «Art.» se perdió en la fuente
ESTR = re.compile(r'^(LIBRO|T[IÍ]TULO|CAP[IÍ]TULO|SECCI[OÓ]N|PARTE|SUBSECCI[OÓ]N)\s+([IVXLC]+|PRIMER[OA]?|SEGUND[OA]|TERCER[OA]?|CUART[OA]|QUINT[OA]|SEXT[OA]|S[ÉE]PTIM[OA]|OCTAV[OA]|NOVEN[OA]|D[ÉE]CIM[OA]|[ÚU]NIC[OA]|PRELIMINAR|\d+)\b\.?\s*(.*)$')
DISP = re.compile(r'^(DISPOSICI[OÓ]N(?:ES)?\s+(?:TRANSITORIAS?|FINAL(?:ES)?|ADICIONAL(?:ES)?|ABROGATORIAS?|DEROGATORIAS?|ABROGATORIAS?\s+Y\s+DEROGATORIAS?|DEROGATORIAS?\s+Y\s+ABROGATORIAS?|COMPLEMENTARIAS?)(?:\s+[ÚU]NICA)?)\s*\.?\s*$')
ITEM = re.compile(r'^(' + ORD + r')\s*[\.\-–:]+\s*(.*)$')
FIN = re.compile(r'^(Remítase al (Poder|Órgano) Ejecutivo|Es dado en (la|el)|Por tanto,? la promulgo|POR TANTO|Dado en el Palacio|Por tanto,? lo promulgo)', re.I)
ENUM = re.compile(r'^(\d+\.|\d+\)|[a-zñ]\)|[A-Z]\)|[IVXLC]+\.|[a-z]\.)(\s|$)')


def sin_num(l):
    """Renglón sin el número de página al comienzo o al final («240    Fiscalía General del Estado»)."""
    return re.sub(r'^\d{1,4}\s{2,}|\s{2,}\d{1,4}$', '', l)


def singular(clase):
    return ' '.join({'transitorias': 'transitoria', 'finales': 'final', 'adicionales': 'adicional', 'abrogatorias': 'abrogatoria', 'derogatorias': 'derogatoria',
                     'complementarias': 'complementaria'}.get(w, w) for w in clase.lower().split())


def norm(s):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', s)).strip()


def extraer(cfg):
    f = os.path.join(RAIZ, 'biblioteca', 'pdf', cfg['pdf'])
    a, b = cfg.get('paginas', (1, 9999))
    if cfg.get('mitades'):
        # PDF con dos páginas del libro en cada hoja (pliego): se lee la mitad izquierda y luego la derecha
        n_p = int(re.search(r'Pages:\s+(\d+)', subprocess.run(['pdfinfo', f], capture_output=True, text=True).stdout).group(1))
        w, h = cfg['mitades']
        pags = []
        for k in range(a, min(b, n_p) + 1):
            for x0 in (0, w):
                pags.append(subprocess.run(['pdftotext', '-layout', '-f', str(k), '-l', str(k), '-x', str(x0), '-y', '0', '-W', str(w), '-H', str(h), f, '-'],
                                           capture_output=True, text=True).stdout)
    else:
        pags = subprocess.run(['pdftotext'] + ([] if cfg.get('sin_layout') else ['-layout']) + ['-f', str(a), '-l', str(b), f, '-'], capture_output=True, text=True).stdout.split('\f')
    # limpieza previa de cada página, antes de juntar espacios (números de página al margen, etc.)
    for x, y in cfg.get('pre', []):
        pags = [re.sub(x, y, p, flags=re.M) for p in pags]
    # renglones repetidos en muchas páginas (encabezados y pies), salvo enumeradores
    from collections import Counter
    cuenta = Counter()
    for p in pags:
        for l in set(sin_num(x.strip()) for x in p.splitlines()):
            if l:
                cuenta[l] += 1
    ruido = {l for l, n in cuenta.items() if n >= max(3, len(pags) * 0.25) and not ENUM.match(l) and not ART.match(l) and not ESTR.match(l) and len(l) < 120}
    ruido |= set(cfg.get('ruido', []))
    ruido_re = [re.compile(x) for x in cfg.get('ruido_re', [])] + [re.compile(r'^\d{1,4}$'), re.compile(r'^P[áa]gina\s+\d+(\s+de\s+\d+)?$', re.I), re.compile(r'^-\s*\d+\s*-$')]
    lineas = []
    for p in pags:
        for l in p.splitlines():
            l = l.strip()
            if not l or l in ruido or sin_num(l) in ruido or any(r.match(l) for r in ruido_re):
                continue
            lineas.append(re.sub(r'\s{2,}', ' ', l))  # espacios de justificado o de sangría
    texto = '\n'.join(lineas)
    if '--ruido' in sys.argv:
        print('  ruido quitado:', sorted(ruido)[:40])
    for x, y in cfg.get('reemplazos', []):
        texto = re.sub(x, y, texto, flags=re.M)
    lineas = [x.strip() for x in texto.split('\n') if x.strip()]
    texto = '\n'.join(lineas)
    # desde el comienzo indicado
    if cfg.get('desde'):
        k = next(i for i, l in enumerate(lineas) if re.match(cfg['desde'], l))
        lineas = lineas[k:]
    salto = re.compile(cfg['saltar']) if cfg.get('saltar') else None  # renglones del compilador (concordancias, notas)
    out, cur, items, prev, secc_disp, pendiente = [], None, [], 0, None, None
    prev_n_base = 0
    informe = []
    fin = False

    def cierra():
        if cur is not None:
            items.append(cur)

    i = 0
    while i < len(lineas) and not fin:
        l = lineas[i]
        if salto and salto.match(l):
            i += 1
            # el bloque saltado sigue en los renglones que no abren artículo, sección ni disposición
            while i < len(lineas) and cfg.get('saltar_bloque') and not (ART.match(lineas[i]) or ESTR.match(lineas[i]) or DISP.match(lineas[i]) or re.match(cfg['saltar_bloque'], lineas[i])):
                i += 1
            continue
        m = ART.match(l) or (cfg.get('num_solo') and NUMSOLO.match(l))
        if m:
            n = int(m.group(1)); suf = (m.group(2) or '').lower()
            if suf and not l[m.end():].lstrip().startswith('('):
                suf = 'NO'  # «Artículo 91 bis y 344 bis del Código…»: es una cita, no un encabezado
            ok = False if suf == 'NO' else (n == prev + 1 and not suf) or (suf and n == prev) or (suf and n == prev_n_base) if prev else n == 1 or cfg.get('primero', 1) == n
            if not ok and prev and 1 < n - prev <= cfg.get('salto_max', 60) and not suf and suf != 'NO':
                # se acepta un salto (artículos derogados o que faltan) solo si ninguno de los números intermedios
                # aparece más adelante como encabezado: así no se toma por artículo una cita a otra ley
                faltan = set(range(prev + 1, n))
                adelante = (ART.match(x) for x in lineas[i + 1:i + 600])
                if not any(mm and int(mm.group(1)) in faltan for mm in adelante):
                    ok = True
                    informe.append(f'salto {prev} → {n}')
            if ok:
                cierra()
                prev_n_base = n
                prev = n if not suf else prev
                etiqueta = f'Artículo {n}' + (f' {suf}' if suf else '')
                cur = {'tipo': 'art', 'label': etiqueta, 'txt': [l[m.end():].strip()] if l[m.end():].strip() else []}
                secc_disp = None
                i += 1
                continue
        e = ESTR.match(l) or (cfg.get('estructura_mixta') and len(l) < 60 and not l.endswith('.') and ESTR.match(l.upper()))
        if e and (l == l.upper() or cfg.get('estructura_mixta')):
            cierra(); cur = None
            tit = l
            # el nombre del título o capítulo puede seguir en el renglón siguiente (en mayúsculas)
            j = i + 1
            while j < len(lineas) and lineas[j] == lineas[j].upper() and re.search('[A-ZÁÉÍÓÚÑ]{3}', lineas[j]) and not (ART.match(lineas[j]) or ESTR.match(lineas[j]) or DISP.match(lineas[j]) or ITEM.match(lineas[j])) and len(tit) < 160:
                tit += ' · ' + lineas[j]; j += 1
            # nombre en minúsculas en el renglón siguiente («Del comienzo y fin de la personalidad»)
            if (cfg.get('estructura_mixta') and j < len(lineas) and len(lineas[j]) < 90 and not re.search(r'[.:;]$', lineas[j])
                    and not (ART.match(lineas[j]) or ESTR.match(lineas[j].upper())) and j + 1 < len(lineas)
                    and (ART.match(lineas[j + 1]) or ESTR.match(lineas[j + 1].upper()))):
                tit += ' · ' + lineas[j]; j += 1
            if not re.search(r'\.{4,}|…{2,}', tit):  # renglones del índice (con puntos suspensivos y número de página)
                items.append({'tipo': 'sec', 'label': tit})
            i = j
            secc_disp = None
            continue
        d = DISP.match(l.upper()) if len(l) < 90 else None
        if d and l == l.upper():
            cierra(); cur = None
            items.append({'tipo': 'sec', 'label': l})
            secc_disp = re.sub(r'\s+', ' ', l).strip()
            i += 1
            continue
        if secc_disp:
            it = ITEM.match(l)
            if it:
                cierra()
                clase = re.sub(r'^DISPOSICI[OÓ]N(ES)?\s+', '', secc_disp, flags=re.I).lower()
                clase = re.sub(r'\s+[úu]nica$', '', clase)
                clase = singular(clase)
                cur = {'tipo': 'disp', 'label': f'Disposición {clase} {it.group(1).lower()}', 'txt': [it.group(2)] if it.group(2) else []}
                i += 1
                continue
            if cur is None and re.match(r'^[ÚU]nica\s*[\.\-]', l):
                pass
        if (FIN.match(l) or (cfg.get('fin') and re.match(cfg['fin'], l))) and prev >= cfg.get('min_arts', 1):
            fin = True
            break
        if cur is None and secc_disp:
            # disposición única sin rótulo PRIMERA/ÚNICA
            clase = re.sub(r'^DISPOSICI[OÓ]N(ES)?\s+', '', secc_disp, flags=re.I).lower()
            cur = {'tipo': 'disp', 'label': f'Disposición {singular(clase.replace(" única", ""))} única', 'txt': []}
        if cur is not None:
            cur['txt'].append(l)
        i += 1
    cierra()
    # índice al comienzo: si un rótulo de sección se repite antes del artículo 1, lo anterior a su última aparición es el índice
    k1 = next((k for k, it in enumerate(items) if it['tipo'] != 'sec'), len(items))
    if k1:
        primeros = [it['label'] for it in items[:k1]]
        ult = max(k for k, x in enumerate(primeros) if x == primeros[0])
        if ult:
            items = items[ult:]
    if not fin:
        informe.append('AVISO: no se encontró la fórmula final («Remítase…» o «Es dado…»)')
    # párrafos
    res = [f'=== {cfg["titulo"]}', f'slug: {cfg["slug"]}', f'tipo: {cfg["tipo"]}', f'fecha: {cfg["fecha"]}', f'epigrafe: {cfg["epigrafe"]}', '']
    n_art = n_disp = 0
    vistos = set()
    for it in items:
        if it['tipo'] == 'sec':
            res += ['§ ' + it['label'], '']
            continue
        lab = it['label']
        if lab in vistos:
            k = 2
            while f'{lab} ({k})' in vistos:
                k += 1
            informe.append(f'rótulo repetido: {lab}')
            lab = f'{lab} ({k})'
        vistos.add(lab)
        pars, act = [], ''
        for l in it['txt']:
            if act and ENUM.match(l):
                pars.append(act); act = l
            else:
                act = (act + ' ' + l) if act else l
            if re.search(r'[.:;]$', l) and not re.search(r'\b(Art|Arts|arts|art|inc|Nº|N°|No|núm|pág|Dr|Sr|S\.A|Ley|D\.S|Cía|Ltda|etc)\.$', l):
                pars.append(act); act = ''
        if act:
            pars.append(act)
        if not pars:
            informe.append(f'{lab}: sin texto')
        res += [f'@ {lab}', '\n\n'.join(pars), '']
        if it['tipo'] == 'art':
            n_art += 1
        else:
            n_disp += 1
    salida = '\n'.join(res).rstrip() + '\n'
    # comprobación: cada renglón publicado está en el texto del PDF
    # (contra el texto ya sin encabezados ni pies de página: así se comprueba que no se cambió ninguna palabra)
    fuente = norm(texto)
    malos = []
    for blq in salida.split('\n'):
        if not blq or blq[:1] in '=@§' or re.match(r'^(slug|tipo|fecha|epigrafe):', blq):
            continue
        if norm(blq) not in fuente:
            # puede faltar porque un pie de página quedaba en medio del párrafo
            partes = [p for p in re.split(r'(?<=[a-záéíóúñ,;])\s', norm(blq))]
            malos.append(blq[:100])
    return salida, n_art, n_disp, informe, malos


NORMAS = {}
exec(open(os.path.join(os.path.dirname(__file__), 'normas_cfg.py'), encoding='utf-8').read())

if __name__ == '__main__':
    claves = list(NORMAS) if sys.argv[1] == 'todas' else sys.argv[1:]
    for k in claves:
        cfg = NORMAS[k]
        salida, n_art, n_disp, informe, malos = extraer(cfg)
        dest = os.path.join(RAIZ, 'contenido', 'normas', cfg['materia'], cfg['slug'] + '.txt')
        if '--escribir' in sys.argv:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            open(dest, 'w', encoding='utf-8').write(salida)
        else:
            open(f'/tmp/arts/{k}.txt', 'w', encoding='utf-8').write(salida)
        print(f'{k}: {n_art} artículos, {n_disp} disposiciones, {salida.count(chr(10) + "§ ")} secciones; renglones que no están en el PDF: {len(malos)}')
        for x in informe[:40]:
            print('   ', x)
        for x in malos[:3]:
            print('    NO ESTÁ:', x)
