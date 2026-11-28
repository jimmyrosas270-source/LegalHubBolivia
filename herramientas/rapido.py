# -*- coding: utf-8 -*-
"""Buscador rápido para estudiantes (se ejecuta al final de buscador.py con exec).

- buscar/rapido.json: índice liviano (normas con sus siglas y portadas, números y títulos de los
  artículos de cada norma por artículos, fichas de la Biblioteca, temas, guías, glosario y preguntas).
  Se descarga solo cuando alguien empieza a escribir en un buscador.
- assets/portadas/<nombre>.svg: las portadas propias (contenido/destacadas.json) como imagen, para
  mostrarlas en las sugerencias y en los resultados.
- assets/sitio.js y assets/estilos.css: sugerencias mientras se escribe (en la portada, en /buscar/
  y en la lupa de la cabecera de todas las páginas) y mejoras en la página de resultados:
  «art 24 CPE», «artículo 22 del Código Civil», «CPE 24», «24 cpe» o «constitución» llevan directo
  a la norma o al artículo, con su portada y una vista previa del texto.
"""

# Siglas y nombres que usan docentes y estudiantes (se suman a los alias del catálogo y de normas.py).
_EXTRA_ALIAS = {
    '/leyes/constitucional/constitucion-politica-del-estado/': ['CPE', 'Constitución', 'Constitución Política', 'Constitución Política del Estado',
                                                              'Constitución boliviana', 'Constitución de Bolivia', 'Carta Magna', 'Nueva Constitución'],
    '/leyes/civil/codigo-civil/': ['Código Civil', 'CC', 'Código Civil boliviano', 'Decreto Ley 12760', 'DL 12760', 'Civil'],
    '/leyes/penal/codigo-penal/': ['Código Penal', 'CP', 'Código Penal boliviano', 'Decreto Ley 10426', 'Ley 1768', 'Penal'],
    '/leyes/procesal-penal/codigo-de-procedimiento-penal/': ['Código de Procedimiento Penal', 'CPP', 'Código Procesal Penal', 'Procedimiento Penal', 'Procesal Penal', 'Ley 1970', 'NCPP'],
    '/leyes/procesal-civil/codigo-procesal-civil/': ['Código Procesal Civil', 'CPC', 'Código de Procedimiento Civil', 'Procedimiento Civil', 'Procesal Civil', 'Ley 439', 'NCPC'],
    '/leyes/familia/codigo-de-las-familias/': ['Código de las Familias', 'Código de Familia', 'Código de Familias', 'Código de las Familias y del Proceso Familiar', 'Ley 603', 'CF', 'Familias'],
    '/leyes/familia/codigo-nina-nino-y-adolescente/': ['Código Niña, Niño y Adolescente', 'CNNA', 'Código del Niño', 'Código Niño Niña Adolescente', 'Ley 548'],
    '/leyes/laboral/ley-general-del-trabajo/': ['Ley General del Trabajo', 'LGT', 'Ley del Trabajo', 'Ley laboral'],
    '/leyes/laboral/reglamento-de-la-ley-general-del-trabajo/': ['Reglamento de la Ley General del Trabajo', 'Reglamento de la LGT', 'RLGT', 'DS 224', 'Decreto Supremo 224'],
    '/leyes/laboral/codigo-procesal-del-trabajo/': ['Código Procesal del Trabajo', 'CPT', 'Procesal del Trabajo', 'Procesal laboral', 'Decreto Ley 16896'],
    '/leyes/laboral/codigo-de-seguridad-social/': ['Código de Seguridad Social', 'CSS'],
    '/leyes/comercial/codigo-de-comercio/': ['Código de Comercio', 'CCo', 'CCom', 'Código mercantil', 'Decreto Ley 14379', 'DL 14379', 'Comercio'],
    '/leyes/comercial/ley-de-servicios-financieros/': ['Ley de Servicios Financieros', 'Ley 393', 'LSF', 'Ley de bancos'],
    '/leyes/constitucional/codigo-procesal-constitucional/': ['Código Procesal Constitucional', 'CPCo', 'Procesal Constitucional', 'Ley 254'],
    '/leyes/constitucional/ley-del-organo-judicial/': ['Ley del Órgano Judicial', 'LOJ', 'Ley 025', 'Ley 25'],
    '/leyes/penal/ley-348/': ['Ley 348', 'Ley integral para garantizar a las mujeres una vida libre de violencia', 'Vida libre de violencia'],
    '/leyes/civil/ley-de-conciliacion-y-arbitraje/': ['Ley de Conciliación y Arbitraje', 'Ley 708', 'Arbitraje'],
    '/leyes/administrativa/ley-de-procedimiento-administrativo/': ['Ley de Procedimiento Administrativo', 'Ley 2341', 'LPA', 'Procedimiento Administrativo'],
    '/leyes/administrativa/ley-safco/': ['Ley SAFCO', 'SAFCO', 'Ley 1178'],
    '/leyes/personas-con-discapacidad/ley-223/': ['Ley 223', 'Ley General para Personas con Discapacidad', 'Ley de discapacidad'],
}
# Orden en que se ofrecen las normas cuando alguien escribe solo un número («art 24») o hay empate.
_ORDEN_RAPIDO = ['constitucion-politica-del-estado', 'codigo-civil', 'codigo-penal', 'codigo-de-procedimiento-penal', 'codigo-procesal-civil',
                 'codigo-de-las-familias', 'ley-general-del-trabajo', 'codigo-de-comercio', 'codigo-nina-nino-y-adolescente',
                 'codigo-procesal-constitucional', 'codigo-procesal-del-trabajo', 'ley-348', 'ley-del-organo-judicial',
                 'reglamento-de-la-ley-general-del-trabajo', 'codigo-de-seguridad-social', 'ley-de-procedimiento-administrativo',
                 'ley-safco', 'ley-de-conciliacion-y-arbitraje', 'ley-de-servicios-financieros', 'ley-223']
_COD_ARTICULOS = ('cpe', 'lgt', 'rgl', 'cpt', 'cco', 'nar')


def _portada_archivo(nombre, p, aria):
    """Escribe assets/portadas/<nombre>.svg y devuelve su ruta pública."""
    escribe(f'assets/portadas/{nombre}.svg', portada_svg(p, aria).replace('<svg class="tapa-svg" ', '<svg ', 1))
    return f'/assets/portadas/{nombre}.svg'


def _sin_dup(xs):
    vistos, out = set(), []
    for x in xs:
        x = (x or '').strip()
        k = x.lower()
        if x and k not in vistos:
            vistos.add(k)
            out.append(x)
    return out


def indice_rapido():
    p = os.path.join(OUT, 'buscar', 'indice.json')
    idx = json.load(open(p, encoding='utf-8'))
    # 1. normas por artículos: se agrupan los artículos por norma
    por_base = {}
    for a in idx:
        if a.get('c') not in _COD_ARTICULOS:
            continue
        partes = a['u'].split('/')
        if len(partes) != 6 or not partes[4].startswith('articulo-'):
            continue
        base = '/'.join(partes[:4]) + '/'
        clave = partes[4][len('articulo-'):]
        nom = ''
        m = re.match(r'\s*\(\s*([^)]{3,90}?)\s*\)', a.get('t') or '')
        if m:
            nom = re.sub(r'\s+', ' ', m.group(1)).strip().rstrip('.')
        por_base.setdefault(base, []).append((clave, nom, a.get('k') or ''))
    info_ruta = {}
    for m_, lista_ in DESTACADAS.items():
        for x in lista_:
            if x.get('ruta'):
                info_ruta[x['ruta']] = dict(x, _materia=m_)
    cols = []
    for base, arts in por_base.items():
        sl = base.strip('/').split('/')[-1]
        x = info_ruta.get(base, {})
        tit = x.get('titulo') or (arts[0][2] if arts else sl)
        img = _portada_archivo(sl, x['portada'], tit) if x.get('portada') else ''
        alias = _sin_dup([tit, *_EXTRA_ALIAS.get(base, []), *_ALIAS.get(base, []), *_ALIAS_COL.get(base, [])])
        orden = _ORDEN_RAPIDO.index(sl) if sl in _ORDEN_RAPIDO else 99
        cols.append({'u': base, 'r': tit, 's': x.get('sub', ''), 'm': x.get('_materia', ''), 'a': alias, 'i': img, 'o': orden,
                     'A': ','.join(c for c, _, _ in arts), 'T': {c: n for c, n, _ in arts if n}})
    cols.sort(key=lambda c: (c['o'], c['r']))
    # 2. fichas de la Biblioteca y de Jurisprudencia
    docs = []
    for ruta_s, lista in (('biblioteca', DOCS), ('jurisprudencia', DOCS_JUR)):
        for d in lista:
            p_ = PORTADA_PDF.get(d['archivo'])
            img = _portada_archivo('pdf-' + d['slug'], p_, d['titulo']) if p_ else f'/{ruta_s}/portadas/{d["slug"]}.jpg'
            alias = _sin_dup([d['titulo'], _nombre_norma(d), f'{d.get("tipo", "")} {d.get("numero", "")}'.strip(), *_ALIAS.get(d['archivo'], [])])
            docs.append({'u': f'/{ruta_s}/{d["slug"]}/', 'l': f'/{ruta_s}/{d["slug"]}/leer/', 'r': d['titulo'], 'a': alias, 'i': img,
                         's': ' · '.join(x for x in ('Biblioteca' if ruta_s == 'biblioteca' else 'Jurisprudencia', d.get('tipo') or 'PDF',
                                                    d.get('materia', ''), d.get('fecha', '')) if x)})
    # 3. temas, guías, glosario, preguntas y materias (se reutiliza lo que ya está en el índice general)
    def corto(t, n):
        t = re.sub(r'\s+', ' ', t or '').strip()
        return t if len(t) <= n else t[:n].rsplit(' ', 1)[0] + '…'
    tem, gui, glo, pre, mat = [], [], [], [], []
    for a in idx:
        c = a.get('c')
        if c == 'tem':
            tem.append({'u': a['u'], 'r': a['r'].replace('Tema: ', '', 1), 's': a['k'].replace('Tema de interés · ', ''), 'd': corto(a['t'].split('. ', 1)[-1], 150)})
        elif c == 'gui':
            gui.append({'u': a['u'], 'r': a['r'].replace('Guía: ', '', 1), 's': a['k'].replace('Guía · ', ''), 'd': corto(a['t'].split('. ', 1)[-1], 150)})
        elif c == 'glo':
            glo.append({'u': a['u'], 'r': a['r'], 'd': corto(a['t'].split(': ', 1)[-1], 120)})
        elif c == 'pre':
            pre.append({'u': a['u'], 'r': a['r'], 's': a['k'].replace('Pregunta frecuente · ', '')})
        elif c == 'mat':
            mat.append({'u': a['u'], 'r': a['r'].split(':')[0], 'a': [x for x in (a.get('a') or '').split('|') if x]})
    datos = {'col': cols, 'doc': docs, 'tem': tem, 'gui': gui, 'glo': glo, 'pre': pre, 'mat': mat}
    texto = json.dumps(datos, ensure_ascii=False, separators=(',', ':'))
    escribe('buscar/rapido.json', texto)
    print(f'Buscador rápido: {len(cols)} normas por artículos ({sum(len(c["A"].split(",")) for c in cols)} artículos), {len(docs)} fichas, '
          f'{len(tem)} temas, {len(gui)} guías, {len(glo)} términos, {len(pre)} preguntas; rapido.json = {len(texto.encode("utf-8")) // 1024} KB.')


RAPIDO_JS = open(os.path.join(HERR, 'rapido.js'), encoding='utf-8').read()
RAPIDO_CSS = open(os.path.join(HERR, 'rapido.css'), encoding='utf-8').read()


def instalar_rapido():
    p = os.path.join(OUT, 'assets', 'sitio.js')
    t = open(p, encoding='utf-8').read()
    if 'window.LHB=' not in t:
        open(p, 'w', encoding='utf-8').write(RAPIDO_JS + '\n' + t)
    for pag in ('index.html', 'buscar/index.html'):
        f = os.path.join(OUT, pag)
        doc = open(f, encoding='utf-8').read()
        doc = doc.replace('placeholder="Busca un tema, una norma o un artículo"', 'placeholder="Ej.: art 24 CPE, código civil, despido"')
        open(f, 'w', encoding='utf-8').write(doc)
    p = os.path.join(OUT, 'assets', 'estilos.css')
    t = open(p, encoding='utf-8').read()
    if '.lhb-sug' not in t:
        open(p, 'w', encoding='utf-8').write(t + '\n' + RAPIDO_CSS)


indice_rapido()
instalar_rapido()
