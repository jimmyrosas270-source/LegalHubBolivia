"""Construye el sitio de LegalHubBolivia en la carpeta salida/.

1. Copia sitio_base/ (las normas publicadas por artículos) tal como está.
2. Genera la Biblioteca PDF (biblioteca/pdf/ + catalogo.csv) y la sección Jurisprudencia
   (jurisprudencia/pdf/ + catalogo.csv, revistas por año):
   portada, ficha y visor con buscador interno (la descarga se activa con "descargas": true en contenido/sitio.json).
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
NAV = [('Temas', '/temas/'), ('Normativa', '/leyes/'), ('Biblioteca', '/biblioteca/'), ('Jurisprudencia', '/jurisprudencia/'), ('Guías', '/guias/'), ('Estudiantes', '/estudiantes/'), ('Profesionales', '/profesionales/'), ('Glosario', '/glosario/')]
PIE = [('Aviso legal', '/legal/aviso-legal/'), ('Privacidad', '/legal/privacidad/'), ('Términos', '/legal/terminos/'), ('Cookies', '/legal/cookies/'), ('Contacto', '/contacto/'), ('Historial de cambios', '/cambios/')]
ESTADOS = {'vigente': ('Vigente', 'vig'), 'con modificaciones': ('Con modificaciones', 'mod'), 'vigente con modificaciones': ('Con modificaciones', 'mod'),
           'verificar': ('Verificar', 'ver'), 'desactualizada': ('Desactualizada', 'des'), 'derogada': ('Derogada', 'der'), 'abrogada': ('Abrogada', 'abr')}
# Descarga de los PDF: apagada salvo que contenido/sitio.json traiga "descargas": true (pedido del titular, 17 nov 2026).
DESCARGAS = bool(CONF.get('descargas', False))
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

# ---------------------------------------------------------------- 2. secciones de PDF (Biblioteca y Jurisprudencia)
def herramienta(*args):
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout


def leer_catalogo(carpeta):
    ruta = os.path.join(carpeta, 'catalogo.csv')
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


ORDEN_MATERIAS = ['Constitucional', 'Laboral', 'Familia', 'Civil', 'Procesal civil', 'Penal', 'Procesal penal', 'Administrativa', 'Agraria', 'Tributario',
                  'Comercial', 'Personas con discapacidad', 'Otras']
# Carpetas que se muestran siempre en /biblioteca/ (vacías: «Próximamente» o enlace a Normativa)
MATERIAS_FIJAS = ['Constitucional', 'Laboral', 'Familia', 'Civil', 'Procesal civil', 'Penal', 'Procesal penal', 'Administrativa']
# Nombre de cada carpeta de biblioteca/pdf/ (la carpeta decide la materia)
MATERIA_DE_CARPETA = {slug(m): m for m in ORDEN_MATERIAS}

# Grupos por tipo de norma dentro de cada materia, en este orden
GRUPOS_TIPO = [('Códigos', ('constitucion', 'codigo')), ('Leyes', ('ley',)), ('Decretos leyes', ('decreto ley',)),
               ('Decretos supremos', ('decreto', 'fe de erratas')),
               ('Resoluciones', ('resolucion',)), ('Reglamentos y protocolos', ('reglamento', 'protocolo')),
               ('Sentencias constitucionales', ('sentencia constitucional',)), ('Autos supremos', ('auto supremo',)),
               ('Otras sentencias y autos', ('sentencia', 'auto'))]
NOMBRES_GRUPO = [g for g, _ in GRUPOS_TIPO] + ['Otros documentos']


def grupo_tipo(d):
    t = slug(d['tipo']).replace('-', ' ')
    if t == 'ley' and 'codigo' in slug(d['titulo']):
        return 'Códigos'
    for g, claves in GRUPOS_TIPO:
        if any(t.startswith(c) for c in claves):
            return g
    return 'Otros documentos'


def orden_doc(d):
    m = re.search(r'(?:1[89]|20)\d\d', d['fecha'])
    n = re.match(r'\d+', d['numero'] or '')
    return (NOMBRES_GRUPO.index(grupo_tipo(d)), int(m.group(0)) if m else 9999, int(n.group(0)) if n else 0, d['titulo'].lower())


def tam(mb):
    return f'{mb:.1f} MB'.replace('.', ',') if mb >= 1 else f'{max(1, round(mb * 1024))} KB'


def anio_de(d):
    m = re.search(r'(?:1[89]|20)\d\d', d['fecha'])
    return m.group(0) if m else 'Sin año'


JUR = os.path.join(RAIZ, 'jurisprudencia')
# Limpieza de PDF al publicar (hipervínculos, resaltados y marcas de páginas no oficiales)
exec(open(os.path.join(HERR, 'limpieza_pdf.py'), encoding='utf-8').read())

# Secciones por tipo de norma y autos supremos
exec(open(os.path.join(HERR, 'tipos.py'), encoding='utf-8').read())

# Portadas propias y normas principales (contenido/destacadas.json)
exec(open(os.path.join(HERR, 'portadas.py'), encoding='utf-8').read())

SECCIONES = [
    {'ruta': 'biblioteca', 'carpeta': BIB, 'nombre': 'Biblioteca', 'sing': 'documento', 'plur': 'documentos', 'con_estado': True, 'agrupa': 'materia',
     'desc': 'Normas bolivianas completas en PDF: léelas en línea, busca dentro del texto o descárgalas.',
     'entrada': 'Normas completas en PDF. Toca la portada para leerlas en línea, busca dentro del texto o descárgalas.',
     'vacio': 'Todavía no hay documentos en la Biblioteca. Aparecerán aquí cuando se suban.',
     'aviso': 'Los documentos de la Biblioteca no son publicaciones oficiales. Verifica siempre en la Gaceta Oficial de Bolivia.',
     'fuente': FUENTE, 'filtro': 'Filtrar por nombre, número o materia', 'tipo_def': 'Documento'},
    {'ruta': 'jurisprudencia', 'carpeta': JUR, 'nombre': 'Jurisprudencia', 'sing': 'revista', 'plur': 'revistas', 'con_estado': False, 'agrupa': 'anio',
     'desc': 'Revistas y compilaciones de jurisprudencia boliviana por año: léelas en línea, busca dentro del texto o descárgalas.',
     'entrada': 'Revistas jurisprudenciales con las sentencias y autos más relevantes de cada año. Toca la portada para leerlas en línea, busca dentro del texto (por ejemplo, el número de una sentencia) o descárgalas.',
     'vacio': 'Todavía no hay revistas de jurisprudencia. Aparecerán aquí cuando se suban.',
     'aviso': 'Las revistas se publican tal como las entrega el editor y no son publicaciones oficiales de este sitio. Verifica cada sentencia o auto en la fuente oficial antes de citarlo.',
     'fuente': 'Publicación jurisprudencial tomada del archivo del editor. Verifique en la publicación oficial.', 'filtro': 'Filtrar por nombre, año o número', 'tipo_def': 'Revista'},
]
SECC = {}


def construir_seccion(S):
    carpeta, ruta_s = S['carpeta'], S['ruta']
    pdf_dir = os.path.join(carpeta, 'pdf')
    # Los PDF pueden estar en subcarpetas (en la Biblioteca, una por materia: biblioteca/pdf/laboral/...).
    pdfs = []
    if os.path.isdir(pdf_dir):
        for dp, _, fs in os.walk(pdf_dir):
            pdfs += [os.path.relpath(os.path.join(dp, f), pdf_dir).replace(os.sep, '/') for f in fs if f.lower().endswith('.pdf')]
    pdfs.sort()
    nombres = {}
    for rel in pdfs:
        nombres.setdefault(os.path.basename(rel), []).append(rel)
    for n, rels in nombres.items():
        if len(rels) > 1:
            ERRORES.append(f'Hay dos PDF con el mismo nombre «{n}» ({", ".join(rels)}): cambia el nombre de uno.')
    catalogo = {os.path.basename(f['archivo']): f for f in leer_catalogo(carpeta)}
    for archivo, f in catalogo.items():
        if archivo not in nombres:
            AVISOS.append(f'{ruta_s}/catalogo.csv, línea {f["_linea"]}: «{archivo}» no está en {ruta_s}/pdf/; no se publica hasta que se suba.')

    DOCS, usados = [], set()
    for rel in pdfs:
        archivo = os.path.basename(rel)
        sub_carpeta = rel.split('/')[0] if '/' in rel else ''
        f = catalogo.get(archivo, {})
        if not f:
            AVISOS.append(f'«{rel}» no tiene fila en {ruta_s}/catalogo.csv: se publica con el nombre del archivo.')
        materia = f.get('materia') or ('Varias' if S['agrupa'] == 'anio' else 'Otras')
        if S['agrupa'] == 'materia':
            if sub_carpeta:
                m_carp = MATERIA_DE_CARPETA.get(slug(sub_carpeta)) or sub_carpeta.replace('-', ' ').replace('_', ' ').strip().capitalize()
                if f.get('materia') and slug(f['materia']) != slug(m_carp):
                    AVISOS.append(f'«{rel}»: el catálogo dice materia «{f["materia"]}», pero está en la carpeta «{sub_carpeta}»; manda la carpeta.')
                materia = m_carp
            else:
                AVISOS.append(f'«{archivo}» está suelto en {ruta_s}/pdf/: muévelo a la carpeta de su materia (se publica como «{materia}»).')
        ruta = os.path.join(pdf_dir, rel)
        mb = os.path.getsize(ruta) / 1048576
        if mb > MAX_MB:
            ERRORES.append(f'«{archivo}» pesa {mb:.1f} MB; el máximo es {MAX_MB} MB. Comprímelo o divídelo.')
            continue
        try:
            info = herramienta('pdfinfo', ruta)
            paginas = int(re.search(r'^Pages:\s+(\d+)', info, re.M).group(1))
            texto = herramienta('pdftotext', '-l', '20', ruta, '-')  # 20: las revistas abren con varias páginas en imagen
        except Exception as e:
            ERRORES.append(f'«{archivo}» no se pudo leer como PDF ({e.__class__.__name__}). Revisa que no esté dañado ni protegido.')
            continue
        titulo = f.get('titulo') or os.path.splitext(archivo)[0].replace('_', ' ').replace('-', ' ').strip()
        sl = slug(f.get('slug') or titulo)
        while sl in usados:
            sl += '-2'
        usados.add(sl)
        est = (f.get('estado') or 'verificar').lower()
        if est not in ESTADOS:
            AVISOS.append(f'«{archivo}»: estado «{f.get("estado")}» no reconocido; se usa «Verificar».')
            est = 'verificar'
        DOCS.append({'archivo': archivo, 'slug': sl, 'titulo': titulo, 'tipo': f.get('tipo', ''), 'numero': f.get('numero', ''),
                     'fecha': f.get('fecha', ''), 'materia': materia, 'estado': est,
                     'descripcion': f.get('descripcion', ''), 'revisado': f.get('revisado') or HOY, 'version': f.get('version') or '1',
                     'paginas': paginas, 'mb': mb, 'con_texto': len(re.sub(r'\s+', '', texto)) > 200})
        os.makedirs(os.path.join(OUT, ruta_s, 'archivos'), exist_ok=True)
        os.makedirs(os.path.join(OUT, ruta_s, 'portadas'), exist_ok=True)
        destino_pdf = os.path.join(OUT, ruta_s, 'archivos', sl + '.pdf')
        if not quitar_enlaces(ruta, destino_pdf):
            shutil.copy(ruta, destino_pdf)
        subprocess.run(['pdftoppm', '-f', '1', '-l', '1', '-singlefile', '-scale-to', '520', '-jpeg', '-jpegopt', 'quality=82',
                        ruta, os.path.join(OUT, ruta_s, 'portadas', sl)], check=True)

    for d in DOCS:
        d['grupo'] = d['materia'] if S['agrupa'] == 'materia' else anio_de(d)
    if S['agrupa'] == 'materia':
        DOCS.sort(key=lambda d: (ORDEN_MATERIAS.index(d['materia']) if d['materia'] in ORDEN_MATERIAS else 99, d['materia'], orden_doc(d)))
        for d in DOCS:
            d['tgrupo'] = grupo_tipo(d)
            d['mslug'] = slug(d['materia'])
            if d['mslug'] in usados:
                ERRORES.append(f'La materia «{d["materia"]}» y un documento comparten la dirección /{ruta_s}/{d["mslug"]}/: cambia el título del documento.')
    else:
        # años de más reciente a más antiguo; «Sin año» al final
        DOCS.sort(key=lambda d: (d['grupo'] == 'Sin año', -int(d['grupo']) if d['grupo'].isdigit() else 0, d['titulo'].lower()))

    def subtitulo(d):
        partes = [x for x in (' '.join(p for p in (d['tipo'], f"N.º {d['numero']}" if d['numero'] else '') if p), d['fecha']) if x]
        return ' · '.join(partes)

    def url(d, sub=''):
        return f'/{ruta_s}/{d["slug"]}/{sub}'

    def pdf_url(d):
        return f'/{ruta_s}/archivos/{d["slug"]}.pdf'

    def tarjeta(d, filtro=None, etq=None):
        sub = subtitulo(d)
        filtro = d['grupo'] if filtro is None else filtro
        etq = d['grupo'] if etq is None else etq
        return (f'<article class="libro" data-materia="{E(filtro)}" data-texto="{E((d["titulo"] + " " + sub + " " + d["materia"] + " " + d["grupo"] + " " + d.get("tgrupo", "")).lower())}">'
                f'<a class="tapa" href="{url(d, "leer/")}" aria-label="Abrir {E(d["titulo"])} en el visor">{tapa_doc(d) if ruta_s == "biblioteca" else f'<img src="/{ruta_s}/portadas/{d["slug"]}.jpg" alt="" loading="lazy" width="260" height="336">'}<span>{ico("book", 18)}Leer</span></a>'
                f'<div class="libro-d"><div class="entre"><span class="etq">{E(etq)}</span>{tag(d["estado"]) if S["con_estado"] else ""}</div>'
                f'<h2><a href="{url(d)}">{E(d["titulo"])}</a></h2>{f"<small>{E(sub)}</small>" if sub else ""}'
                f'<small>{d["paginas"]} páginas · PDF {tam(d["mb"])}</small>'
                f'<p class="libro-acc"><a href="{url(d, "leer/")}">Leer</a>{f'<a href="{pdf_url(d)}" download="{d["slug"]}.pdf">Descargar</a>' if DESCARGAS else ''}<a href="{url(d)}">Ficha</a></p></div></article>')

    if S['agrupa'] == 'materia':
        portada_por_materias(S, DOCS, tarjeta)
    else:
        portada_plana(S, DOCS, tarjeta)
    escribe_fichas(S, DOCS, subtitulo, url, pdf_url)
    # índice para el buscador general del sitio (lo usa /buscar/ si se amplía)
    escribe(f'{ruta_s}/indice.json', json.dumps([{'t': d['titulo'], 's': subtitulo(d), 'm': d['materia'], 'u': url(d)} for d in DOCS], ensure_ascii=False, separators=(',', ':')))
    SECC[ruta_s] = DOCS
    return DOCS


def plural(n, s, p):
    return f'{n} {s if n == 1 else p}'


def portada_por_materias(S, DOCS, tarjeta):
    """/biblioteca/: una carpeta por materia; /biblioteca/<materia>/: documentos por tipo de norma y fecha."""
    ruta_s = S['ruta']
    por_materia = {}
    for d in DOCS:
        por_materia.setdefault(d['materia'], []).append(d)
    orden = [m for m in ORDEN_MATERIAS if m in por_materia or m in MATERIAS_FIJAS] + [m for m in por_materia if m not in ORDEN_MATERIAS]
    con_docs = [m for m in orden if m in por_materia]
    carpetas = []
    for m in orden:
        if m not in por_materia:
            if os.path.isdir(os.path.join(OUT, 'leyes', slug(m))):
                carpetas.append(f'<a class="materia carpeta" href="/leyes/{slug(m)}/"><b>{E(m)}</b><small>Por artículos en Normativa</small></a>')
            else:
                carpetas.append(f'<div class="materia off"><b>{E(m)}</b><small>Próximamente</small></div>')
            continue
        docs = por_materia[m]
        tipos = []
        for g in NOMBRES_GRUPO:
            k = sum(1 for d in docs if d['tgrupo'] == g)
            if k:
                tipos.append(f'{g.lower()} {k}')
        carpetas.append(f'<a class="materia carpeta" href="/{ruta_s}/{slug(m)}/"><b>{E(m)}</b><small>{plural(len(docs), S["sing"], S["plur"])}</small>'
                        f'<small class="tipos">{E(" · ".join(tipos))}</small></a>')
    por_archivo = {d['archivo']: d for d in DOCS}
    bloque_tipos = paginas_por_tipo(S, DOCS, tarjeta, por_materia) if ruta_s == 'biblioteca' else ''
    dest_inicio = bloque_destacadas([dict(x, _materia=m) for m in ORDEN_MATERIAS for x in DESTACADAS.get(m, []) if x.get('inicio')], por_archivo, etq_materia=True) if ruta_s == 'biblioteca' else ''
    buscador = (f'<div class="filtros"><label class="filtro">{ico("search", 20)}<input type="search" id="filtro" placeholder="Buscar en toda la Biblioteca" aria-label="Buscar en toda la Biblioteca"></label></div>'
                f'<section id="todos" hidden><p id="cuenta" class="sec" role="status" aria-live="polite"></p>'
                f'<div class="estante">{"".join(tarjeta(d, etq=d["materia"]) for d in DOCS)}</div><div id="nada" class="vacio" hidden>Ninguna coincidencia.</div></section>') if DOCS else ''
    escribe(f'{ruta_s}/index.html', pagina(S['nombre'], S['desc'],
            f'''<div class="cont pag">{migas([("Inicio", "/"), (S["nombre"], f"/{ruta_s}/")])}<h1>{S["nombre"]}</h1>
<p class="entrada">Normas completas en PDF, ordenadas por materia. Abre una carpeta o busca en toda la Biblioteca.</p>{buscador}
{dest_inicio}<h2 class="grupo-tit">Materias</h2>
<div class="rejilla r4 carpetas" id="carpetas">{"".join(carpetas)}</div>{bloque_tipos}{alerta(S["aviso"])}</div>''',
            S['nombre'], scripts='<script src="/assets/biblioteca.js" defer></script>\n'))

    for m, docs in por_materia.items():
        grupos = [g for g in NOMBRES_GRUPO if any(d['tgrupo'] == g for d in docs)]
        chips = ''.join(f'<button type="button" class="chip-f" data-m="{E(g)}" aria-pressed="false">{E(g)}</button>' for g in grupos)
        secciones = ''.join(
            f'<section class="grupo-lib"><h2 class="grupo-tit">{E(g)} <small>({sum(1 for d in docs if d["tgrupo"] == g)})</small></h2>'
            f'<div class="estante">{"".join(tarjeta(d, filtro=g, etq=d["tipo"] or S["tipo_def"]) for d in docs if d["tgrupo"] == g)}</div></section>'
            for g in grupos)
        escribe(f'{ruta_s}/{slug(m)}/index.html', pagina(f'{m} · {S["nombre"]}', f'Normas de materia {m.lower()} en PDF: leer en línea y buscar.',
                f'''<div class="cont pag">{migas([("Inicio", "/"), (S["nombre"], f"/{ruta_s}/"), (m, "")])}<h1>{E(m)}</h1>
<p class="entrada">{plural(len(docs), S["sing"], S["plur"])}, {"primero las normas principales y después todos" if DESTACADAS.get(m) else "ordenados"} por tipo de norma y por fecha, del más antiguo al más reciente.</p>
<div class="filtros"><label class="filtro">{ico("search", 20)}<input type="search" id="filtro" placeholder="Filtrar por nombre, número o tema" aria-label="Filtrar {S["plur"]}"></label>
<div class="chips" role="group" aria-label="Tipos de norma"><button type="button" class="chip-f" data-m="" aria-pressed="true">Todos</button>{chips}</div></div>
{enlaces_tipo(m, docs) if ruta_s == "biblioteca" else ""}
<p id="cuenta" class="sec" role="status" aria-live="polite">{plural(len(docs), S["sing"], S["plur"])}</p>
{bloque_destacadas(DESTACADAS.get(m, []), por_archivo) if ruta_s == "biblioteca" else ""}{"<h2 class='grupo-tit sep'>Todas las normas, por tipo</h2>" if ruta_s == "biblioteca" and DESTACADAS.get(m) else ""}
{secciones}<div id="nada" class="vacio" hidden>Ninguna coincidencia con el filtro.</div>
<p><a class="mas" href="/{ruta_s}/">Volver a todas las materias</a></p>{alerta(S["aviso"])}</div>''',
                S['nombre'], scripts='<script src="/assets/biblioteca.js" defer></script>\n'))


def portada_plana(S, DOCS, tarjeta):
    ruta_s = S['ruta']
    grupos = []
    for d in DOCS:
        if d['grupo'] not in grupos:
            grupos.append(d['grupo'])
    chips = ''.join(f'<button type="button" class="chip-f" data-m="{E(m)}" aria-pressed="false">{E(m)}</button>' for m in grupos)
    etq_grupos = 'Materias' if S['agrupa'] == 'materia' else 'Años'
    if DOCS:
        lista = (f'<div class="filtros"><label class="filtro">{ico("search", 20)}<input type="search" id="filtro" placeholder="{S["filtro"]}" aria-label="Filtrar {S["plur"]}"></label>'
                 f'<div class="chips" role="group" aria-label="{etq_grupos}"><button type="button" class="chip-f" data-m="" aria-pressed="true">Todas</button>{chips}</div></div>'
                 f'<p id="cuenta" class="sec" role="status" aria-live="polite">{len(DOCS)} {S["sing"] if len(DOCS) == 1 else S["plur"]}</p>'
                 f'<div class="estante">{"".join(tarjeta(d) for d in DOCS)}</div><div id="nada" class="vacio" hidden>Ninguna coincidencia con el filtro.</div>')
    else:
        lista = f'<div class="vacio">{S["vacio"]}</div>'
    escribe(f'{ruta_s}/index.html', pagina(S['nombre'], S['desc'],
            f'''<div class="cont pag">{migas([("Inicio", "/"), (S["nombre"], f"/{ruta_s}/")])}<h1>{S["nombre"]}</h1>
<p class="entrada">{S["entrada"]}</p>{lista}{alerta(S["aviso"])}</div>''',
            S['nombre'], scripts='<script src="/assets/biblioteca.js" defer></script>\n'))


def escribe_fichas(S, DOCS, subtitulo, url, pdf_url):
    ruta_s = S['ruta']
    for d in DOCS:
        sub = subtitulo(d)
        filas = []
        if S['con_estado']:
            filas.append(('Estado', tag(d['estado'])))
        filas.append(('Materia', f'<a href="/{ruta_s}/{d["mslug"]}/">{E(d["materia"])}</a>' if d.get('mslug') else E(d['materia'])))
        if S['agrupa'] == 'anio':
            filas.append(('Año', E(d['grupo'])))
        if sub:
            filas.append(('Publicación' if S['agrupa'] == 'anio' else 'Norma', E(sub)))
        filas += [('Páginas', str(d['paginas'])), ('Archivo', f'PDF, {tam(d["mb"])}'),
                  ('Búsqueda dentro del texto', 'Disponible' if d['con_texto'] else 'No disponible: el PDF es una imagen escaneada'),
                  ('Última revisión', E(d['revisado'])), ('Versión', E(d['version'])), ('Fuente', S['fuente'])]
        sobre = '<section class="tarjeta sobre"><h2>Sobre este documento</h2><dl>' + ''.join(f'<dt>{k}</dt><dd>{v}</dd>' for k, v in filas) + '</dl></section>'
        desc = (f'<aside class="explica"><span class="etq">Descripción · no es texto legal</span><p>{E(d["descripcion"])}</p><small>Pendiente de revisión legal humana</small></aside>'
                if d['descripcion'] else '')
        escaneado = '' if d['con_texto'] else alerta(f'Este PDF es una imagen escaneada: se puede leer{" y descargar" if DESCARGAS else ""}, pero el buscador interno no encuentra palabras.')
        escribe(f'{ruta_s}/{d["slug"]}/index.html', pagina(d['titulo'], f'{d["titulo"]}{" · " + sub if sub else ""}. Texto completo en PDF: leer en línea y buscar{" y descargar" if DESCARGAS else ""}.',
                f'''<div class="cont pag">{migas([("Inicio", "/"), (S["nombre"], f"/{ruta_s}/")] + ([(d["materia"], f"/{ruta_s}/{d['mslug']}/")] if d.get('mslug') else []) + [(d["titulo"], "")])}
<div class="dos"><div>
<div class="entre"><span class="etq">{E(d["tipo"] or S["tipo_def"])} · PDF</span>{tag(d["estado"]) if S["con_estado"] else ""}</div><h1>{E(d["titulo"])}</h1>{f'<p class="entrada">{E(sub)}</p>' if sub else ''}
<div class="ficha-pdf"><a class="tapa grande" href="{url(d, "leer/")}" aria-label="Abrir en el visor">{tapa_doc(d, "Primera página de " + d["titulo"]) if ruta_s == "biblioteca" else f'<img src="/{ruta_s}/portadas/{d["slug"]}.jpg" alt="Primera página de {E(d["titulo"])}" width="260" height="336">'}<span>{ico("book", 18)}Leer</span></a>
<div class="ficha-acc"><p class="botones"><a class="btn" href="{url(d, "leer/")}">{ico("book", 20)}&nbsp;Leer en línea</a>{f'<a class="btn sec" href="{pdf_url(d)}" download="{d["slug"]}.pdf">{ico("dl", 20)}&nbsp;Descargar PDF ({tam(d["mb"])})</a>' if DESCARGAS else ''}</p>
<form class="buscador" action="{url(d, "leer/")}" method="get" role="search">{ico("search", 20)}<input type="search" name="buscar" placeholder="Buscar dentro de este documento" aria-label="Buscar dentro de este documento"{'' if d['con_texto'] else ' disabled'}><button type="submit"{'' if d['con_texto'] else ' disabled'}>Buscar</button></form>{escaneado}</div></div>
{desc}</div>
<aside>{sobre}{alerta()}</aside></div></div>''', S['nombre']))
        escribe(f'{ruta_s}/{d["slug"]}/leer/index.html', f'''<!doctype html>
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
{f'<a class="ico-btn" href="{pdf_url(d)}" download="{d["slug"]}.pdf" aria-label="Descargar PDF">{ico("dl")}</a>' if DESCARGAS else ''}
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



for _s in SECCIONES:
    construir_seccion(_s)
DOCS = SECC['biblioteca']
DOCS_JUR = SECC['jurisprudencia']

# ---------------------------------------------------------------- 2a. normas por artículos propias (contenido/normas/)
exec(open(os.path.join(HERR, 'normas.py'), encoding='utf-8').read())

# ---------------------------------------------------------------- 2b. guías, preguntas y glosario
exec(open(os.path.join(HERR, 'editorial.py'), encoding='utf-8').read())

# ---------------------------------------------------------------- 2c. cuestionarios de estudio (Estudiantes)
exec(open(os.path.join(HERR, 'cuestionarios.py'), encoding='utf-8').read())

# ---------------------------------------------------------------- 2d. temas de interés, tarjetas y portada
exec(open(os.path.join(HERR, 'temas.py'), encoding='utf-8').read())

# ---------------------------------------------------------------- 3. menú en las páginas de base
ENLACE_NORM = re.compile(r'(<a href="/leyes/"[^>]*>Normativa</a>)')
n_menu = 0
nota_paginas = {}
for dp, _, fs in os.walk(OUT):
    if dp.startswith((os.path.join(OUT, 'biblioteca'), os.path.join(OUT, 'jurisprudencia'), os.path.join(OUT, 'visor'))):
        continue
    for fn in fs:
        if not fn.endswith('.html'):
            continue
        p = os.path.join(dp, fn)
        doc = open(p, encoding='utf-8').read()
        if 'href="/jurisprudencia/"' in doc:
            continue
        partes = re.split(r'(<nav class="migas".*?</nav>)', doc, flags=re.S)
        nuevo = ''.join(x if x.startswith('<nav class="migas"') else ENLACE_NORM.sub(r'\1<a href="/biblioteca/">Biblioteca</a><a href="/jurisprudencia/">Jurisprudencia</a>', x) for x in partes)
        if nuevo != doc:
            n_menu += 1
            open(p, 'w', encoding='utf-8').write(nuevo)

# ---------------------------------------------------------------- 3b. normas principales y portadas en /leyes/
# Arregla también las migas que versiones anteriores del generador ensuciaron con el menú.
MIGAS_SUCIAS = '<a href="/leyes/">Normativa</a><a href="/biblioteca/">Biblioteca</a><a href="/jurisprudencia/">Jurisprudencia</a><span aria-hidden="true">›</span>'
n_migas = 0
for dp, _, fs in os.walk(os.path.join(OUT, 'leyes')):
    for fn in fs:
        if fn.endswith('.html'):
            p = os.path.join(dp, fn)
            doc = open(p, encoding='utf-8').read()
            mig = re.search(r'<nav class="migas".*?</nav>', doc, re.S)
            if mig and MIGAS_SUCIAS in mig.group(0):
                doc = doc.replace(mig.group(0), mig.group(0).replace(MIGAS_SUCIAS, '<a href="/leyes/">Normativa</a><span aria-hidden="true">›</span>'))
                open(p, 'w', encoding='utf-8').write(doc)
                n_migas += 1
POR_ARCHIVO = {d['archivo']: d for d in DOCS}
n_tapas = 0
for m in ORDEN_MATERIAS:
    p = os.path.join(OUT, 'leyes', slug(m), 'index.html')
    if not os.path.isfile(p):
        continue
    doc = open(p, encoding='utf-8').read()
    rutas = [x['ruta'] for x in DESTACADAS.get(m, []) if x.get('ruta')]
    arts = re.findall(r'<article class="tarjeta">.*?</article>', doc, re.S)
    if not arts:
        continue

    def rango(a):
        r = re.search(r'href="([^"]+)"', a).group(1)
        return rutas.index(r) if r in rutas else len(rutas)

    nuevos = []
    for a in sorted(arts, key=rango):
        r = re.search(r'href="([^"]+)"', a).group(1)
        x = PORTADA_RUTA.get(r)
        if x:
            a = (f'<article class="tarjeta con-tapa"><a class="tapa" href="{r}" aria-label="Abrir {E(x["titulo"])}">{portada_svg(x["portada"], x["titulo"])}</a><div class="tarjeta-d">'
                 + a[len('<article class="tarjeta">'):-len('</article>')] + '</div></article>')
            n_tapas += 1
        nuevos.append(a)
    ini = doc.index(arts[0])
    fin = max(doc.index(a) + len(a) for a in arts)
    pdfs = [t for t in (tarjeta_destacada(x, POR_ARCHIVO) for x in DESTACADAS.get(m, []) if x.get('archivo')) if t]
    extra = (f'<section class="destacadas en-leyes"><h2 class="grupo-tit">También en la Biblioteca (PDF)</h2><div class="estante">{"".join(pdfs)}</div>'
             f'<p><a class="mas" href="/biblioteca/{slug(m)}/">Ver todas las normas de {E(m.lower())} en PDF</a></p></section>') if pdfs else ''
    doc = doc[:ini] + ''.join(nuevos) + extra + doc[fin:]
    if '/assets/biblioteca.css' not in doc:
        doc = doc.replace('<link rel="stylesheet" href="/assets/estilos.css">', '<link rel="stylesheet" href="/assets/estilos.css">\n<link rel="stylesheet" href="/assets/biblioteca.css">', 1)
    open(p, 'w', encoding='utf-8').write(doc)
# /leyes/: materias sin normas por artículos pero con PDF en la Biblioteca
p = os.path.join(OUT, 'leyes', 'index.html')
if os.path.isfile(p):
    doc = open(p, encoding='utf-8').read()
    for m in ORDEN_MATERIAS:
        k = sum(1 for d in DOCS if d['materia'] == m)
        off = f'<div class="materia off"><b>{E(m)}</b><small>Próximamente</small></div>'
        if k and off in doc:
            doc = doc.replace(off, f'<a class="materia" href="/biblioteca/{slug(m)}/"><b>{E(m)}</b><small>{plural(k, "documento", "documentos")} en PDF (Biblioteca)</small></a>')
    open(p, 'w', encoding='utf-8').write(doc)
print(f'Portadas propias en Normativa: {n_tapas}. Migas corregidas: {n_migas}.')

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
            f'''<section class="hero"><div class="cont"><h1>Leyes de Bolivia, al pie de la letra</h1><p>Normas completas para leer en línea, y buscar dentro del texto.</p>
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
escribe('_headers', cab_robots + '/visor/*\n  Cache-Control: public, max-age=604800\n/biblioteca/portadas/*\n  Cache-Control: public, max-age=86400\n/jurisprudencia/portadas/*\n  Cache-Control: public, max-age=86400\n')

# ---------------------------------------------------------------- aviso para reportar errores
# Si contenido/sitio.json trae "reportes_url" (p. ej. un formulario de Google), cada página lleva al final
# un recuadro para avisar de un dato erróneo o desactualizado. «{pagina}» en la dirección se cambia por la página actual.
URL_REPORTE = (CONF.get('reportes_url') or '').strip()
n_rep = 0
if URL_REPORTE:
    escribe('assets/reporte.js', "(function(){var a=document.querySelector('[data-reporte]');if(!a)return;"
            "a.href=a.getAttribute('data-reporte').split('{pagina}').join(encodeURIComponent(location.href))})();\n")
    caja = ('<div class="cont pag estrecha"><aside class="reportar" style="display:flex;flex-wrap:wrap;gap:12px 20px;align-items:center;justify-content:space-between;margin-top:28px;margin-bottom:28px;padding:16px 18px;background:#E4EFE8;border-radius:12px;font-size:15px"><div><b>¿Viste un dato erróneo o desactualizado?</b> '
            'Una norma derogada, una cifra que cambió o un error de texto: avísanos de forma anónima para corregirlo.</div>'
            f'<a class="btn-rep" style="display:inline-block;padding:9px 16px;border-radius:999px;background:#1F5B44;color:#fff;text-decoration:none;font-weight:600" data-reporte="{E(URL_REPORTE)}" href="{E(URL_REPORTE.replace("{pagina}", ""))}" target="_blank" rel="noopener">Reportar un error</a></aside></div>')
    for dp, _, fs in os.walk(OUT):
        if os.sep + 'visor' in dp:
            continue
        for fn in fs:
            if fn.endswith('.html'):
                p = os.path.join(dp, fn)
                doc = open(p, encoding='utf-8').read()
                if 'class="reportar' in doc or '</main>' not in doc or '/leer/' in p.replace(os.sep, '/'):
                    continue
                doc = doc.replace('</main>', caja + '</main>', 1).replace('</body>', '<script src="/assets/reporte.js" defer></script>\n</body>', 1)
                open(p, 'w', encoding='utf-8').write(doc)
                n_rep += 1
    print(f'Recuadro «Reportar un error» en {n_rep} páginas.')

# ---------------------------------------------------------------- colores por materia, menú «Temas» y tarjetas en todas las páginas
exec(open(os.path.join(HERR, 'decorar.py'), encoding='utf-8').read())

# ---------------------------------------------------------------- buscador ampliado
exec(open(os.path.join(HERR, 'buscador.py'), encoding='utf-8').read())

# ---------------------------------------------------------------- informe
total = sum(len(fs) for _, _, fs in os.walk(OUT))
print(f'Biblioteca: {len(DOCS)} documento(s) publicados.')
for d in DOCS:
    print(f'  - {d["titulo"]} → /biblioteca/{d["slug"]}/ ({d["paginas"]} págs., {tam(d["mb"])}, texto buscable: {"sí" if d["con_texto"] else "NO"})')
print(f'Jurisprudencia: {len(DOCS_JUR)} revista(s) publicadas.')
for d in DOCS_JUR:
    print(f'  - {d["titulo"]} → /jurisprudencia/{d["slug"]}/ ({d["paginas"]} págs., {tam(d["mb"])}, texto buscable: {"sí" if d["con_texto"] else "NO"})')
print(f'Menú «Biblioteca» y «Jurisprudencia» añadido a {n_menu} página(s) de sitio_base. Notas editoriales insertadas: {n_notas}.')
print(f'Archivos en salida/: {total}')
for a in AVISOS:
    print('AVISO:', a)
for e in ERRORES:
    print('ERROR:', e)
if total > 19000:
    ERRORES.append('Más de 19.000 archivos: cerca del tope de Cloudflare (20.000).')
if ERRORES:
    sys.exit(1)
