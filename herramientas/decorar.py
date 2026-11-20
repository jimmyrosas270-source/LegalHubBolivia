"""Retoques finales en todas las páginas de salida/ (también las de sitio_base).

Lo ejecuta construir.py antes del buscador:
  - añade «Temas» al menú (escritorio y celular) donde falte;
  - enlaza assets/materias.css y assets/tarjetas.js (no en el visor ni en las páginas «leer»);
  - marca <body data-m="materia"> según la ruta, para el color de la materia;
  - marca con data-mc los recuadros de materia (a.materia) según su enlace.
"""
for nombre in ('materias.css', 'tarjetas.js'):
    shutil.copy(os.path.join(HERR, 'base', nombre), os.path.join(OUT, 'assets', nombre))

MAT_SLUGS = {slug(m) for m in ORDEN_MATERIAS}
DOC_MAT = {d['slug']: slug(d['materia']) for d in DOCS}
TEMA_MAT = {t['slug']: t['m'] for t in TEMAS}
SECC_MAT = ('leyes', 'guias', 'preguntas', 'biblioteca')


def materia_de_ruta(partes):
    if not partes:
        return ''
    if partes[0] == 'temas' and len(partes) > 1:
        return TEMA_MAT.get(partes[1], '')
    if partes[0] == 'estudiantes' and len(partes) > 2 and partes[1] == 'cuestionarios':
        return partes[2] if partes[2] in MAT_SLUGS else ''
    if partes[0] in SECC_MAT and len(partes) > 1:
        if partes[1] in MAT_SLUGS:
            return partes[1]
        if partes[0] == 'biblioteca':
            return DOC_MAT.get(partes[1], '')
    return ''


def _mc(m):
    href = m.group(2)
    p = [x for x in href.split('/') if x]
    mat = p[1] if len(p) == 2 and p[0] in ('leyes', 'biblioteca') and p[1] in MAT_SLUGS else ''
    return f'{m.group(1)} data-mc="{mat}"' if mat else m.group(1)


ETQ_MAT = re.compile(r'<span class="etq">(' + '|'.join(re.escape(E(m)) for m in ORDEN_MATERIAS) + r')</span>')
n_dec = 0
for dp, _, fs in os.walk(OUT):
    rel_dir = os.path.relpath(dp, OUT).replace(os.sep, '/')
    if rel_dir == 'visor' or rel_dir.startswith('visor/'):
        continue
    for fn in fs:
        if not fn.endswith('.html'):
            continue
        p = os.path.join(dp, fn)
        partes = [] if rel_dir == '.' else rel_dir.split('/')
        doc = open(p, encoding='utf-8').read()
        if '<header class="cab">' not in doc:
            continue
        antes = doc
        en_temas = bool(partes) and partes[0] == 'temas'
        # 1. «Temas» en el menú
        for clase in ('<nav class="nav" aria-label="Principal">', '<nav id="menu" class="menu-movil" aria-label="Menú" hidden>'):
            i = doc.find(clase)
            if i < 0:
                continue
            fin = doc.find('</nav>', i)
            if 'href="/temas/"' in doc[i:fin]:
                continue
            doc = doc[:i + len(clase)] + f'<a href="/temas/"{" aria-current=\"true\"" if en_temas else ""}>Temas</a>' + doc[i + len(clase):]
        # 2. hojas y script (no en las páginas «leer», que son el visor a pantalla completa)
        if 'leer' not in partes:
            if '/assets/materias.css' not in doc:
                doc = doc.replace('<link rel="icon"', '<link rel="stylesheet" href="/assets/materias.css">\n<link rel="icon"', 1)
            if '/assets/tarjetas.js' not in doc:
                doc = doc.replace('</body>', '<script src="/assets/tarjetas.js" defer></script>\n</body>', 1)
        # 3. color de la materia de la página
        mat = materia_de_ruta(partes)
        if mat and 'data-m=' not in doc[doc.find('<body'):doc.find('<body') + 120]:
            doc = re.sub(r'<body( class="[^"]*")?>', lambda m: f'<body{m.group(1) or ""} data-m="{mat}">', doc, count=1)
        # 4. recuadros y etiquetas de materia
        doc = ETQ_MAT.sub(lambda m: f'<span class="etq" data-mc="{slug(html.unescape(m.group(1)))}">{m.group(1)}</span>', doc)
        doc = re.sub(r'(<a class="materia[^"]*" href="([^"]+)")(?! data-mc)', _mc, doc)
        if doc != antes:
            open(p, 'w', encoding='utf-8').write(doc)
            n_dec += 1
print(f'Colores por materia, menú «Temas» y tarjetas: {n_dec} página(s) retocadas.')
