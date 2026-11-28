# -*- coding: utf-8 -*-
"""Portadas propias y normas principales (contenido/destacadas.json).

Se ejecuta dentro de construir.py (exec), después de definir E, slug e ico.
Las portadas son SVG en línea: usan las tipografías que ya carga la página.
"""

# Color de cada materia: temas, ilustraciones, buscador y portadas de las normas usan el mismo.
COLOR_MATERIA = {
    'Constitucional': '#24497F', 'Laboral': '#1F5B44', 'Familia': '#6B3A7D', 'Civil': '#1E6B73',
    'Procesal civil': '#154C52', 'Penal': '#A3241B', 'Procesal penal': '#741B14', 'Administrativa': '#4A5868',
    'Agraria': '#5A6B1F', 'Tributario': '#8A5A0F', 'Personas con discapacidad': '#3B4FA3', 'Comercial': '#5B4636', 'Otras': '#55615A',
}


def _mezcla(hexa, blanco=.72):
    c = [int(hexa[i:i + 2], 16) for i in (1, 3, 5)]
    return '#' + ''.join(f'{round(x + (255 - x) * blanco):02X}' for x in c)


COLORES = {  # fondo, texto, acento, texto secundario
    'tinta':   ('#16211C', '#F5F6F3', '#E0B04A', '#C9D3CC'),
    'verde':   ('#1F5B44', '#FFFFFF', '#E0B04A', '#D5E6DC'),
    'bosque':  ('#123B2C', '#F5F6F3', '#E0B04A', '#BFD3C7'),
    'menta':   ('#E4EFE8', '#16211C', '#1F5B44', '#55615A'),
    'kantuta': ('#A3241B', '#FFFFFF', '#E0B04A', '#F2D3CF'),
    'ocre':    ('#E0B04A', '#16211C', '#A3241B', '#4A3A12'),
    'papel':   ('#F5F6F3', '#16211C', '#A3241B', '#55615A'),
}


def _escalones(y, ancho, color, op, alto=4):
    """Franja de escalones de inspiración andina (motivo geométrico propio)."""
    d = [f'M0 {y + 3 * alto}']
    x = 0
    while x < ancho:
        d.append(f'h4v-{alto}h4v-{alto}h4v-{alto}h4v{alto}h4v{alto}h4v{alto}')
        x += 24
    d.append(f'V{y + 3 * alto + 3}H0Z')
    return f'<path d="{"".join(d)}" fill="{color}" opacity="{op}"/>'


def portada_svg(p, aria):
    if p.get('materia') in COLOR_MATERIA:  # la portada toma el color de la materia de la norma (pedido del titular, 27 nov)
        fondo, texto, acento, suave = COLOR_MATERIA[p['materia']], '#FFFFFF', '#E0B04A', _mezcla(COLOR_MATERIA[p['materia']])
    else:
        fondo, texto, acento, suave = COLORES.get(p.get('color', 'verde'), COLORES['verde'])
    lineas = p.get('lineas') or [aria]
    largo = max(len(x) for x in lineas)
    tam = min(31, round(222 / (largo * 0.54), 1), round(160 / (len(lineas) * 1.13), 1))
    alto_l = tam * 1.13
    y0 = 96 + tam
    tit = ''.join(f'<tspan x="22" y="{y0 + i * alto_l:.1f}">{E(t)}</tspan>' for i, t in enumerate(lineas))
    y_regla = y0 + (len(lineas) - 1) * alto_l + 18
    return (f'<svg class="tapa-svg" viewBox="0 0 260 336" role="img" aria-label="Portada: {E(aria)}" xmlns="http://www.w3.org/2000/svg">'
            f'<rect width="260" height="336" fill="{fondo}"/>'
            f'<rect x="9.5" y="9.5" width="241" height="317" rx="3" fill="none" stroke="{acento}" stroke-opacity=".55"/>'
            f'<text x="22" y="34" font-family="\'IBM Plex Sans\',Arial,sans-serif" font-size="8.2" letter-spacing="1.6" fill="{suave}">ESTADO PLURINACIONAL DE BOLIVIA</text>'
            f'{_escalones(42, 260, acento, ".9")}'
            f'<text x="22" y="84" font-family="\'IBM Plex Sans\',Arial,sans-serif" font-size="11" font-weight="700" letter-spacing=".8" fill="{acento}">{E(p.get("tipo", "").upper())}</text>'
            f'<text font-family="\'Source Serif 4\',Georgia,serif" font-size="{tam}" font-weight="600" fill="{texto}">{tit}</text>'
            f'<rect x="22" y="{y_regla:.1f}" width="46" height="3" fill="{acento}"/>'
            f'<text x="22" y="{y_regla + 22:.1f}" font-family="\'IBM Plex Sans\',Arial,sans-serif" font-size="11.5" fill="{suave}">{E(p.get("pie", ""))}</text>'
            f'{_escalones(283, 260, acento, ".35")}'
            f'<g transform="translate(140 300)"><rect width="16" height="16" rx="4" fill="{acento}"/>'
            f'<path d="M4 6h6M4 9h8M4 12h6" stroke="{fondo}" stroke-width="1.4" stroke-linecap="round"/></g>'
            f'<text x="238" y="312.5" text-anchor="end" font-family="\'IBM Plex Sans\',Arial,sans-serif" font-size="10" font-weight="600" fill="{texto}">LegalHubBolivia</text>'
            f'</svg>')


_dest = json.load(open(os.path.join(RAIZ, 'contenido', 'destacadas.json'), encoding='utf-8'))['materias']
DESTACADAS = {m: [x for x in lista if x.get('ruta') or x.get('archivo')] for m, lista in _dest.items()}
for _m, _lista in _dest.items():
    for _x in _lista:
        if _x.get('portada'):
            _x['portada'].setdefault('materia', _m)
PORTADA_PDF = {x['archivo']: x['portada'] for lista in DESTACADAS.values() for x in lista if x.get('archivo') and x.get('portada')}
PORTADA_RUTA = {x['ruta']: x for lista in DESTACADAS.values() for x in lista if x.get('ruta') and x.get('portada')}


def tapa_doc(d, alt=''):
    """Portada de un documento de la Biblioteca: la propia si existe; si no, la primera página."""
    p = PORTADA_PDF.get(d['archivo'])
    if p:
        return portada_svg(p, d['titulo'])
    return f'<img src="/biblioteca/portadas/{d["slug"]}.jpg" alt="{E(alt)}" loading="lazy" width="260" height="336">'


def tarjeta_destacada(x, docs_por_archivo, etq=None):
    """Tarjeta de una norma principal (por artículos o PDF). None si el PDF no está en el catálogo."""
    if x.get('ruta'):
        tapa = portada_svg(x['portada'], x['titulo']) if x.get('portada') else ''
        return (f'<article class="libro destacada"><a class="tapa" href="{x["ruta"]}" aria-label="Abrir {E(x["titulo"])}">{tapa}<span>{ico("book", 18)}Ver</span></a>'
                f'<div class="libro-d"><div class="entre"><span class="etq">{E(etq or "Por artículos")}</span></div>'
                f'<h2><a href="{x["ruta"]}">{E(x["titulo"])}</a></h2><small>{E(x.get("sub", ""))}</small><small>{E(x.get("detalle", ""))}</small>'
                f'<p class="libro-acc"><a href="{x["ruta"]}">Ver artículos</a><a href="/buscar/">Buscar</a></p></div></article>')
    d = docs_por_archivo.get(x['archivo'])
    if not d:
        AVISOS.append(f'destacadas.json: «{x["archivo"]}» no está en la Biblioteca; se omite.')
        return None
    base = f'/biblioteca/{d["slug"]}/'
    sub = ' · '.join(p for p in (d['tipo'], d['fecha']) if p)
    return (f'<article class="libro destacada"><a class="tapa" href="{base}leer/" aria-label="Abrir {E(d["titulo"])} en el visor">{tapa_doc(d)}<span>{ico("book", 18)}Leer</span></a>'
            f'<div class="libro-d"><div class="entre"><span class="etq">{E(etq or "PDF")}</span></div>'
            f'<h2><a href="{base}">{E(d["titulo"])}</a></h2><small>{E(sub)}</small><small>{d["paginas"]} páginas · PDF</small>'
            f'<p class="libro-acc"><a href="{base}leer/">Leer</a>{f'<a href="/biblioteca/archivos/{d["slug"]}.pdf" download="{d["slug"]}.pdf">Descargar</a>' if DESCARGAS else ''}<a href="{base}">Ficha</a></p></div></article>')


def bloque_destacadas(items, docs_por_archivo, titulo='Normas principales', etq_materia=False):
    tarjetas = [t for t in (tarjeta_destacada(x, docs_por_archivo, etq=x.get('_materia') if etq_materia else None) for x in items) if t]
    if not tarjetas:
        return ''
    return (f'<section id="destacadas" class="destacadas"><h2 class="grupo-tit">{E(titulo)} <small>(las más consultadas)</small></h2>'
            f'<div class="estante">{"".join(tarjetas)}</div></section>')
