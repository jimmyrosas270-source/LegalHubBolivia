"""Construye el sitio de LegalHubBolivia en la carpeta salida/.

1. Copia sitio_base/ (las normas publicadas por artículos) tal como está.
2. Genera la Biblioteca PDF a partir de biblioteca/pdf/ y biblioteca/catalogo.csv:
   portada, ficha, visor con buscador interno y descarga.
3. Añade el enlace «Biblioteca» al menú de las páginas de sitio_base/.
4. Inserta las notas editoriales de contenido/notas_editoriales.json.

Uso: python3 herramientas/construir.py   (desde la raíz del repositorio)
Requiere: Python 3.9+ y poppler-utils (pdfinfo, pdftoppm, pdftotext).
"""
import csv, html, json, os, re, shutil, subprocess, sys, unicodedata
from datetime import datetime, timezone, timedelta

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(RAIZ, 'salida')
BASE = os.path.join(RAIZ, 'sitio_base')
HERR = os.path.join(RAIZ, 'herramientas')
BIB = os.path.join(RAIZ, 'biblioteca')
E = html.escape
MAX_MB = 25  # tope por archivo de Cloudflare (y de la subida web de GitHub)
FUENTE = 'Texto no oficial, tomado del archivo del editor. Verifique en la publicación oficial.'
VERIF = '[VERIFICAR CON FUENTE OFICIAL]'
AVISOS, ERRORES = [], []

CONF = json.load(open(os.path.join(RAIZ, 'contenido', 'sitio.json'), encoding='utf-8'))
HOY = datetime.now(timezone(timedelta(hours=-4))).strftime('%d/%m/%Y')


def slug(t):
    t = unicodedata.normalize('NFD', t.lower())
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-') or 'documento'


# ---------------------------------------------------------------- plantilla
def ico(n, s=22):
    P = {'search': '<circle cx="11" cy="11" r="7"/><path d="M16.5 16.5L21 21"/>', 'menu': '<path d="M4 7h16M4 12h16M4 17h16"/>',
         'chev': '<path d="M9 6l6 6-6 6"/>', 'chevl': '<path d="M15 6l-6 6 6 6"/>', 'info': '<circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16.5v.5"/>',
         'up': '<path d="M6 15l6-6 6 6"/>', 'down': '<path d="M6 9l6 6 6-6"/>', 'plus': '<path d="M12 5v14M5 12h14"/>', 'minus': '<path d="M5 12h14"/>',
         'dl': '<path d="M12 4v11M7 10l5 5 5-5M5 20h14"/>', 'book': '<path d="M5 5.5A1.5 1.5 0 016.5 4H19v14H6.5A1.5 1.5 0 005 19.5zM5 19.5A1.5 1.5 0 006.5 21H19"/>',
         'x': '<path d="M6 6l12 12M18 6L6 18"/>'}
    return f'<svg width="{s}" height="{s}" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{P[n]}</svg>'


MARCA = '<svg width="36" height="36" viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="14" fill="#1F5B44"/><path d="M40 0h10v24l-5-5-5 5z" fill="#E0B04A"/><path d="M14 24h18M14 34h36M14 44h26" stroke="#fff" stroke-width="4" stroke-linecap="round" fill="none"/></svg>'
NAV = [('Normativa', '/leyes/'), ('Biblioteca', '/biblioteca/'), ('Guías', '/guias/'), ('Estudiantes', '/estudiantes/'), ('Profesionales', '/profesionales/'), ('Glosario', '/glosario/')]
PIE = [('Aviso legal', '/legal/aviso-legal/'), ('Privacidad', '/legal/privacidad/'), ('Términos', '/legal/terminos/'), ('Cookies', '/legal/cookies/'), ('Contacto', '/contacto/'), ('Historial de cambios', '/cambios/')]
ESTADOS = {'vigente': ('Vigente', 'vig'), 'con modificaciones': ('Con modificaciones', 'mod'), 'vigente con modificaciones': ('Con modificaciones', 'mod'),
           'verificar': ('Verificar', 'ver'), 'desactualizada': ('Desactualizada', 'des'), 'derogada': ('Derogada', 'der'), 'abrogada': ('Abrogada', 'abr')}
ROBOTS = '' if CONF.get('abierto_a_buscadores') else '<meta name="robots" content="noindex, nofollow">\n'


def tag(estado):
    n, c = ESTADOS[estado]
    return f'<span class="tag {c}">{n}</span>'


def alerta(t='Información general. No sustituye asesoría profesional.'):
    return f'<div class="alerta">{ico("info")}<div>{t}</div></div>'


def migas(items):
    out = []
    for k, (n, h) in enumerate(items):
        out.append(f'<span aria-current="page">{E(n)}</span>' if k == len(items) - 1 else f'<a href="{h}">{E(n)}</a><span aria-hidden="true">›</span>')
    return f'<nav class="migas" aria-label="Migas de pan">{"".join(out)}</nav>'


def pagina(titulo, desc, cuerpo, activo='', cuerpo_clase='', extra_head='', scripts=''):
    nav = ''.join(f'<a href="{h}"{" aria-current=\"true\"" if n == activo else ""}>{n}</a>' for n, h in NAV)
    pie = ''.join(f'<a href="{h}">{n}</a>' for n, h in PIE)
    return f'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(titulo)} · LegalHubBolivia</title>
<meta name="description" content="{E(desc)}">
{ROBOTS}<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&amp;family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&amp;display=swap">
<link rel="stylesheet" href="/assets/estilos.css">
<link rel="stylesheet" href="/assets/biblioteca.css">
{extra_head}<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
</head>
<body{f' class="{cuerpo_clase}"' if cuerpo_clase else ''}>
<a class="salto" href="#contenido">Saltar al contenido</a>
<div class="franja" aria-hidden="true"><i></i><i></i><i></i></div>
<div class="prueba">Versión de prueba · contenido pendiente de revisión legal humana</div>
<header class="cab"><div class="cont">
<a class="logo" href="/" aria-label="LegalHubBolivia, inicio">{MARCA}<span><b>LegalHub</b><span>Bolivia</span></span></a>
<nav class="nav" aria-label="Principal">{nav}</nav>
<div class="acciones"><a class="ico-btn" href="/buscar/" aria-label="Buscar">{ico("search")}</a><button class="ico-btn solo-movil" type="button" aria-label="Abrir menú" aria-expanded="false" aria-controls="menu" data-menu>{ico("menu")}</button></div>
</div></header>
<nav id="menu" class="menu-movil" aria-label="Menú" hidden>{nav}</nav>
<main id="contenido">
{cuerpo}
</main>
<footer class="pie"><div class="cont">
<div class="pie-a"><a class="logo claro" href="/">{MARCA}<span><b>LegalHub</b><span>Bolivia</span></span></a>
<p>Información general. No sustituye asesoría profesional. Los textos del sitio no son oficiales; verifica en la publicación oficial.</p></div>
<nav class="pie-b" aria-label="Pie de página">{pie}</nav>
</div></footer>
<script src="/assets/sitio.js" defer></script>
{scripts}</body>
</html>
'''


def escribe(rel, txt):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(txt)


def html_de(ruta):
    return ruta.strip('/') + '/index.html' if ruta.strip('/') else 'index.html'


# ---------------------------------------------------------------- 1. base
if os.path.isdir(OUT):
    shutil.rmtree(OUT)
shutil.copytree(BASE, OUT, ignore=shutil.ignore_patterns('LEEME*', 'README*', '.*', '*.zip'))
# Si la base se subió como un .zip (p. ej. la vista previa v2), se descomprime aquí.
import zipfile
for zf in sorted(f for f in os.listdir(BASE) if f.lower().endswith('.zip')):
    with zipfile.ZipFile(os.path.join(BASE, zf)) as z:
        nombres = [n for n in z.namelist() if not n.endswith('/') and '__MACOSX' not in n]
        indices = [n for n in nombres if n.endswith('index.html')]
        prefijo = min(indices, key=len)[:-len('index.html')] if indices else ''
        for n in nombres:
            if not n.startswith(prefijo):
                continue
            rel = os.path.normpath(n[len(prefijo):])
            if rel.startswith('..') or os.path.isabs(rel):
                continue
            destino = os.path.join(OUT, rel)
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            with z.open(n) as a, open(destino, 'wb') as b:
                shutil.copyfileobj(a, b)
    print(f'Base descomprimida desde sitio_base/{zf}')
hay_base = os.path.isfile(os.path.join(OUT, 'index.html'))
for nombre in ('estilos.css', 'sitio.js', 'favicon.svg'):
    if not os.path.isfile(os.path.join(OUT, 'assets', nombre)):
        os.makedirs(os.path.join(OUT, 'assets'), exist_ok=True)
        shutil.copy(os.path.join(HERR, 'base', nombre), os.path.join(OUT, 'assets', nombre))
for nombre in ('biblioteca.css', 'biblioteca.js', 'lector.js'):
    shutil.copy(os.path.join(HERR, 'base', nombre), os.path.join(OUT, 'assets', nombre))
shutil.copytree(os.path.join(HERR, 'visor'), os.path.join(OUT, 'visor'), ignore=shutil.ignore_patterns('LICENSE*', 'VERSION*'))
if not hay_base:
    AVISOS.append('sitio_base/ está vacío: se publica solo la Biblioteca con una portada provisional.')

# ---------------------------------------------------------------- 2. biblioteca
def herramienta(*args):
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout


def leer_catalogo():
    ruta = os.path.join(BIB, 'catalogo.csv')
    if not os.path.isfile(ruta):
        return []
    texto = open(ruta, encoding='utf-8-sig').read()
    sep = ';' if texto.split('\n', 1)[0].count(';') > texto.split('\n', 1)[0].count(',') else ','
    filas = []
    for i, f in enumerate(csv.DictReader(texto.splitlines(), delimiter=sep), start=2):
        f = {(k or '').strip().lower(): (v or '').strip() for k, v in f.items()}
        if not f.get('archivo') or f['archivo'].startswith('#'):
            continue
        f['_linea'] = i
        filas.append(f)
    return filas


pdfs = sorted(f for f in os.listdir(os.path.join(BIB, 'pdf')) if f.lower().endswith('.pdf'))
catalogo = {f['archivo']: f for f in leer_catalogo()}
for archivo, f in catalogo.items():
    if archivo not in pdfs:
        AVISOS.append(f'catalogo.csv, línea {f["_linea"]}: «{archivo}» no está en biblioteca/pdf/; no se publica hasta que se suba.')

DOCS, usados = [], set()
for archivo in pdfs:
    f = catalogo.get(archivo, {})
    if not f:
        AVISOS.append(f'«{archivo}» no tiene fila en catalogo.csv: se publica con el nombre del archivo y estado «Verificar».')
    ruta = os.path.join(BIB, 'pdf', archivo)
    mb = os.path.getsize(ruta) / 1048576
    if mb > MAX_MB:
        ERRORES.append(f'«{archivo}» pesa {mb:.1f} MB; el máximo es {MAX_MB} MB. Comprímelo o divídelo.')
        continue
    try:
        info = herramienta('pdfinfo', ruta)
        paginas = int(re.search(r'^Pages:\s+(\d+)', info, re.M).group(1))
        texto = herramienta('pdftotext', '-l', '5', ruta, '-')
    except Exception as e:
        ERRORES.append(f'«{archivo}» no se pudo leer como PDF ({e.__class__.__name__}). Revisa que no esté dañado ni protegido.')
        continue
    titulo = f.get('titulo') or os.path.splitext(archivo)[0].replace('_', ' ').replace('-', ' ').strip()
    s = slug(f.get('slug') or titulo)
    while s in usados:
        s += '-2'
    usados.add(s)
    est = (f.get('estado') or 'verificar').lower()
    if est not in ESTADOS:
        AVISOS.append(f'«{archivo}»: estado «{f.get("estado")}» no reconocido; se usa «Verificar».')
        est = 'verificar'
    DOCS.append({'archivo': archivo, 'slug': s, 'titulo': titulo, 'tipo': f.get('tipo', ''), 'numero': f.get('numero', ''),
                 'fecha': f.get('fecha', ''), 'materia': f.get('materia') or 'Otras', 'estado': est,
                 'descripcion': f.get('descripcion', ''), 'revisado': f.get('revisado') or HOY, 'version': f.get('version') or '1',
                 'paginas': paginas, 'mb': mb, 'con_texto': len(re.sub(r'\s+', '', texto)) > 200})
    os.makedirs(os.path.join(OUT, 'biblioteca', 'archivos'), exist_ok=True)
    os.makedirs(os.path.join(OUT, 'biblioteca', 'portadas'), exist_ok=True)
    shutil.copy(ruta, os.path.join(OUT, 'biblioteca', 'archivos', s + '.pdf'))
    subprocess.run(['pdftoppm', '-f', '1', '-l', '1', '-singlefile', '-scale-to', '520', '-jpeg', '-jpegopt', 'quality=82',
                    ruta, os.path.join(OUT, 'biblioteca', 'portadas', s)], check=True)

ORDEN_MATERIAS = ['Constitucional', 'Laboral', 'Civil', 'Procesal civil', 'Penal', 'Procesal penal', 'Familia', 'Administrativa', 'Tributaria', 'Comercial', 'Otras']
DOCS.sort(key=lambda d: (ORDEN_MATERIAS.index(d['materia']) if d['materia'] in ORDEN_MATERIAS else 99, d['materia'], d['titulo'].lower()))


def subtitulo(d):
    partes = [x for x in (' '.join(p for p in (d['tipo'], f"N.º {d['numero']}" if d['numero'] else '') if p), d['fecha']) if x]
    return ' · '.join(partes)


def tam(mb):
    return f'{mb:.1f} MB'.replace('.', ',') if mb >= 1 else f'{max(1, round(mb * 1024))} KB'


def url(d, sub=''):
    return f'/biblioteca/{d["slug"]}/{sub}'


def pdf_url(d):
    return f'/biblioteca/archivos/{d["slug"]}.pdf'


def tarjeta(d):
    sub = subtitulo(d)
    return (f'<article class="libro" data-materia="{E(d["materia"])}" data-texto="{E((d["titulo"] + " " + sub + " " + d["materia"]).lower())}">'
            f'<a class="tapa" href="{url(d, "leer/")}" aria-label="Abrir {E(d["titulo"])} en el visor"><img src="/biblioteca/portadas/{d["slug"]}.jpg" alt="" loading="lazy" width="260" height="336"><span>{ico("book", 18)}Leer</span></a>'
            f'<div class="libro-d"><div class="entre"><span class="etq">{E(d["materia"])}</span>{tag(d["estado"])}</div>'
            f'<h2><a href="{url(d)}">{E(d["titulo"])}</a></h2>{f"<small>{E(sub)}</small>" if sub else ""}'
            f'<small>{d["paginas"]} páginas · PDF {tam(d["mb"])}</small>'
            f'<p class="libro-acc"><a href="{url(d, "leer/")}">Leer</a><a href="{pdf_url(d)}" download="{d["slug"]}.pdf">Descargar</a><a href="{url(d)}">Ficha</a></p></div></article>')


materias = []
for d in DOCS:
    if d['materia'] not in materias:
        materias.append(d['materia'])
chips = ''.join(f'<button type="button" class="chip-f" data-m="{E(m)}" aria-pressed="false">{E(m)}</button>' for m in materias)
if DOCS:
    lista = (f'<div class="filtros"><label class="filtro">{ico("search", 20)}<input type="search" id="filtro" placeholder="Filtrar por nombre, número o materia" aria-label="Filtrar documentos"></label>'
             f'<div class="chips" role="group" aria-label="Materias"><button type="button" class="chip-f" data-m="" aria-pressed="true">Todas</button>{chips}</div></div>'
             f'<p id="cuenta" class="sec" role="status" aria-live="polite">{len(DOCS)} {"documento" if len(DOCS) == 1 else "documentos"}</p>'
             f'<div class="estante">{"".join(tarjeta(d) for d in DOCS)}</div><div id="nada" class="vacio" hidden>Ningún documento coincide con el filtro.</div>')
else:
    lista = '<div class="vacio">Todavía no hay documentos en la Biblioteca. Aparecerán aquí cuando se suban.</div>'
escribe('biblioteca/index.html', pagina('Biblioteca', 'Normas bolivianas completas en PDF: léelas en línea, busca dentro del texto o descárgalas.',
        f'''<div class="cont pag">{migas([("Inicio", "/"), ("Biblioteca", "/biblioteca/")])}<h1>Biblioteca</h1>
<p class="entrada">Normas completas en PDF. Toca la portada para leerlas en línea, busca dentro del texto o descárgalas.</p>{lista}{alerta("Los documentos de la Biblioteca no son publicaciones oficiales. Verifica siempre en la Gaceta Oficial de Bolivia.")}</div>''',
        'Biblioteca', scripts='<script src="/assets/biblioteca.js" defer></script>\n'))

for d in DOCS:
    sub = subtitulo(d)
    filas = [('Estado', tag(d['estado'])), ('Materia', E(d['materia']))]
    if sub:
        filas.append(('Norma', E(sub)))
    filas += [('Páginas', str(d['paginas'])), ('Archivo', f'PDF, {tam(d["mb"])}'),
              ('Búsqueda dentro del texto', 'Disponible' if d['con_texto'] else 'No disponible: el PDF es una imagen escaneada'),
              ('Última revisión', E(d['revisado'])), ('Versión', E(d['version'])), ('Fuente', FUENTE)]
    sobre = '<section class="tarjeta sobre"><h2>Sobre este documento</h2><dl>' + ''.join(f'<dt>{k}</dt><dd>{v}</dd>' for k, v in filas) + '</dl></section>'
    desc = (f'<aside class="explica"><span class="etq">Descripción · no es texto legal</span><p>{E(d["descripcion"])}</p><small>Pendiente de revisión legal humana</small></aside>'
            if d['descripcion'] else '')
    escaneado = '' if d['con_texto'] else alerta('Este PDF es una imagen escaneada: se puede leer y descargar, pero el buscador interno no encuentra palabras.')
    escribe(f'biblioteca/{d["slug"]}/index.html', pagina(d['titulo'], f'{d["titulo"]}{" · " + sub if sub else ""}. Texto completo en PDF: leer en línea, buscar y descargar.',
            f'''<div class="cont pag">{migas([("Inicio", "/"), ("Biblioteca", "/biblioteca/"), (d["titulo"], "")])}
<div class="dos"><div>
<div class="entre"><span class="etq">{E(d["tipo"] or "Documento")} · PDF</span>{tag(d["estado"])}</div><h1>{E(d["titulo"])}</h1>{f'<p class="entrada">{E(sub)}</p>' if sub else ''}
<div class="ficha-pdf"><a class="tapa grande" href="{url(d, "leer/")}" aria-label="Abrir en el visor"><img src="/biblioteca/portadas/{d["slug"]}.jpg" alt="Primera página de {E(d["titulo"])}" width="260" height="336"><span>{ico("book", 18)}Leer</span></a>
<div class="ficha-acc"><p class="botones"><a class="btn" href="{url(d, "leer/")}">{ico("book", 20)}&nbsp;Leer en línea</a><a class="btn sec" href="{pdf_url(d)}" download="{d["slug"]}.pdf">{ico("dl", 20)}&nbsp;Descargar PDF ({tam(d["mb"])})</a></p>
<form class="buscador" action="{url(d, "leer/")}" method="get" role="search">{ico("search", 20)}<input type="search" name="buscar" placeholder="Buscar dentro de este documento" aria-label="Buscar dentro de este documento"{'' if d['con_texto'] else ' disabled'}><button type="submit"{'' if d['con_texto'] else ' disabled'}>Buscar</button></form>{escaneado}</div></div>
{desc}</div>
<aside>{sobre}{alerta()}</aside></div></div>''', 'Biblioteca'))
    escribe(f'biblioteca/{d["slug"]}/leer/index.html', f'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(d["titulo"])} (visor) · LegalHubBolivia</title>
<meta name="description" content="{E(d["titulo"])}: lectura en línea con buscador interno.">
{ROBOTS}<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600;700&amp;display=swap">
<link rel="stylesheet" href="/visor/pdf_viewer.css">
<link rel="stylesheet" href="/assets/estilos.css">
<link rel="stylesheet" href="/assets/biblioteca.css">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
</head>
<body class="lector-pag">
<div class="franja" aria-hidden="true"><i></i><i></i><i></i></div>
<header class="lector-barra">
<a class="ico-btn" href="{url(d)}" aria-label="Volver a la ficha">{ico("chevl")}</a>
<div class="lector-tit"><b>{E(d["titulo"])}</b><small>Texto no oficial · verifica en la publicación oficial</small></div>
<form class="lector-busca" id="busca" role="search"{'' if d['con_texto'] else ' hidden'}>{ico("search", 18)}<input type="search" id="q" placeholder="Buscar en el documento" aria-label="Buscar en el documento" autocomplete="off" enterkeyhint="search"><span id="conteo" class="conteo" role="status" aria-live="polite"></span><button type="button" class="ico-btn" id="ant" aria-label="Resultado anterior">{ico("up", 18)}</button><button type="button" class="ico-btn" id="sig" aria-label="Resultado siguiente">{ico("down", 18)}</button></form>
<div class="lector-herr">
<button type="button" class="ico-btn solo-movil" id="abre-busca" aria-label="Buscar en el documento"{'' if d['con_texto'] else ' hidden'}>{ico("search")}</button>
<label class="pagnum"><span class="sr">Página</span><input id="pag" type="number" min="1" max="{d["paginas"]}" value="1" inputmode="numeric"><span>/ {d["paginas"]}</span></label>
<button type="button" class="ico-btn" id="menos" aria-label="Reducir">{ico("minus")}</button><button type="button" class="ico-btn" id="mas" aria-label="Ampliar">{ico("plus")}</button>
<a class="ico-btn" href="{pdf_url(d)}" download="{d["slug"]}.pdf" aria-label="Descargar PDF">{ico("dl")}</a>
</div>
</header>
<main id="lector" data-pdf="{pdf_url(d)}">
<div id="visor-cont"><div id="viewer" class="pdfViewer"></div></div>
<div id="carga" class="carga" role="status">Cargando documento… <span id="avance"></span></div>
</main>
<script type="module" src="/assets/lector.js"></script>
</body>
</html>
''')

# índice para el buscador general del sitio (lo usa /buscar/ si se amplía)
escribe('biblioteca/indice.json', json.dumps([{'t': d['titulo'], 's': subtitulo(d), 'm': d['materia'], 'u': url(d)} for d in DOCS], ensure_ascii=False, separators=(',', ':')))

# ---------------------------------------------------------------- 3. menú en las páginas de base
ENLACE_NORM = re.compile(r'(<a href="/leyes/"[^>]*>Normativa</a>)')
n_menu = 0
nota_paginas = {}
for dp, _, fs in os.walk(OUT):
    if dp.startswith(os.path.join(OUT, 'biblioteca')) or dp.startswith(os.path.join(OUT, 'visor')):
        continue
    for fn in fs:
        if not fn.endswith('.html'):
            continue
        p = os.path.join(dp, fn)
        doc = open(p, encoding='utf-8').read()
        if 'href="/biblioteca/"' in doc:
            continue
        nuevo = ENLACE_NORM.sub(r'\1<a href="/biblioteca/">Biblioteca</a>', doc)
        if nuevo != doc:
            n_menu += 1
            open(p, 'w', encoding='utf-8').write(nuevo)

# ---------------------------------------------------------------- 4. notas editoriales
NOTAS = json.load(open(os.path.join(RAIZ, 'contenido', 'notas_editoriales.json'), encoding='utf-8'))['notas']
n_notas = 0
for n in NOTAS:
    if not n.get('publicar', True):
        continue
    p = os.path.join(OUT, html_de(n['ruta']))
    if not os.path.isfile(p):
        AVISOS.append(f'Nota editorial «{n["id"]}»: no existe la página {n["ruta"]} en sitio_base/; la nota queda guardada sin publicar.')
        continue
    doc = open(p, encoding='utf-8').read()
    marca = f'data-nota="{E(n["id"])}"'
    if marca in doc:
        continue
    parrafos = ''.join(f'<p>{E(t)}</p>' for t in n['texto'])
    bloque = (f'<aside class="nota" {marca}><span class="etq gris">Nota editorial · no forma parte de la ley</span>{parrafos}'
              f'<p><code>{VERIF}</code></p><small>{E(n.get("estado_revision", "Pendiente de revisión legal humana"))}</small></aside>')
    if '<nav class="vecinos"' in doc:
        doc = doc.replace('<nav class="vecinos"', bloque + '<nav class="vecinos"', 1)
    elif '</article>' in doc:
        doc = doc.replace('</article>', '</article>' + bloque, 1)
    else:
        AVISOS.append(f'Nota editorial «{n["id"]}»: no se encontró dónde insertarla en {n["ruta"]}.')
        continue
    open(p, 'w', encoding='utf-8').write(doc)
    n_notas += 1

# ---------------------------------------------------------------- 5. portada provisional, robots y cabeceras
if not hay_base:
    escribe('index.html', pagina('Leyes de Bolivia, al pie de la letra', 'Normas bolivianas en texto literal y en PDF.',
            f'''<section class="hero"><div class="cont"><h1>Leyes de Bolivia, al pie de la letra</h1><p>Normas completas para leer en línea, buscar dentro del texto y descargar.</p>
<p><a class="btn" href="/biblioteca/" style="background:var(--ocre);border-color:var(--ocre);color:var(--tinta)">Abrir la Biblioteca</a></p></div></section>
<div class="cont pag">{alerta()}</div>'''))
    escribe('404.html', pagina('Página no encontrada', 'La página que buscas no existe.',
            '<div class="cont pag estrecha"><h1>Página no encontrada</h1><p class="entrada">La dirección no existe o cambió.</p><p><a class="mas" href="/biblioteca/">Ir a la Biblioteca</a></p></div>'))
if CONF.get('abierto_a_buscadores'):
    escribe('robots.txt', 'User-agent: *\nAllow: /\n')
    cab_robots = ''
else:
    escribe('robots.txt', 'User-agent: *\nDisallow: /\n')
    cab_robots = '/*\n  X-Robots-Tag: noindex, nofollow\n'
escribe('_headers', cab_robots + '/visor/*\n  Cache-Control: public, max-age=604800\n/biblioteca/portadas/*\n  Cache-Control: public, max-age=86400\n')

# ---------------------------------------------------------------- informe
total = sum(len(fs) for _, _, fs in os.walk(OUT))
print(f'Biblioteca: {len(DOCS)} documento(s) publicados.')
for d in DOCS:
    print(f'  - {d["titulo"]} → /biblioteca/{d["slug"]}/ ({d["paginas"]} págs., {tam(d["mb"])}, texto buscable: {"sí" if d["con_texto"] else "NO"})')
print(f'Menú «Biblioteca» añadido a {n_menu} página(s) de sitio_base. Notas editoriales insertadas: {n_notas}.')
print(f'Archivos en salida/: {total}')
for a in AVISOS:
    print('AVISO:', a)
for e in ERRORES:
    print('ERROR:', e)
if total > 19000:
    ERRORES.append('Más de 19.000 archivos: cerca del tope de Cloudflare (20.000).')
if ERRORES:
    sys.exit(1)
