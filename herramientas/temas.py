"""Temas de interés, tarjetas «¿Sabías que?» y portada del sitio.

Lo ejecuta construir.py después de editorial.py (usa leer_md, md_html, en_linea, filas_articulos,
GUIAS, url_guia, REVISION) y de ilustraciones.py.

Fuentes:
  contenido/temas/<nombre>.md  -> /temas/<nombre>/
  Encabezado: titulo, materia, imagen (clave de ilustraciones.py), orden, actualizada, resumen,
  tarjetas (- texto | título exacto de una sección ## | norma y artículo),
  normas (- /ruta | nombre | detalle) y guias (- /ruta | título).

Salidas:
  /temas/ y /temas/<nombre>/
  /assets/tarjetas.json: tarjetas de los temas + los «¿Sabías que?» (líneas '> ') de las guías.
  /index.html: portada nueva (temas, tarjetas, materias por color y accesos).
"""
import random as _random

exec(open(os.path.join(HERR, 'ilustraciones.py'), encoding='utf-8').read())

TEMAS = []
dir_t = os.path.join(CONT, 'temas')


def _plano_md(t):
    t = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', r'\1', t)
    return t.replace('**', '').replace('[VERIFICAR]', '').strip()


def _ids_h2(cuerpo_html):
    """Pone id a cada <h2> (slug del texto) y devuelve el HTML y la lista (id, texto)."""
    indice = []

    def pon(m):
        txt = html.unescape(re.sub(r'<[^>]+>', '', m.group(1)))
        i = slug(txt)
        indice.append((i, txt))
        return f'<h2 id="{i}">{m.group(1)}</h2>'
    return re.sub(r'<h2>(.*?)</h2>', pon, cuerpo_html), indice


if os.path.isdir(dir_t):
    for fn in sorted(os.listdir(dir_t)):
        if not fn.endswith('.md'):
            continue
        meta, cuerpo = leer_md(os.path.join(dir_t, fn))
        if meta.get('publicar', 'si').lower() in ('no', 'false'):
            continue
        mat = meta.get('materia', 'Constitucional')
        if mat not in COLOR_MATERIA:
            AVISOS.append(f'Tema «{fn}»: la materia «{mat}» no tiene color asignado; se usa el verde.')
        secciones = [s.strip() for s in re.findall(r'^## +(.+)$', cuerpo, flags=re.M)]
        tarjetas = []
        for linea in meta.get('tarjetas', []) if isinstance(meta.get('tarjetas'), list) else []:
            partes = [p.strip() for p in linea.split('|')]
            texto, secc, fuente = (partes + ['', '', ''])[:3]
            if secc and secc not in secciones:
                AVISOS.append(f'Tema «{fn}»: la tarjeta «{texto[:40]}…» apunta a la sección «{secc}», que no existe; enlaza al inicio del tema.')
                secc = ''
            tarjetas.append({'t': texto, 'f': fuente, 'a': slug(secc) if secc else ''})
        TEMAS.append({'slug': fn[:-3], 'meta': meta, 'cuerpo': cuerpo, 'titulo': meta.get('titulo', fn[:-3]), 'materia': mat,
                      'm': slug(mat), 'imagen': meta.get('imagen', 'defensa'), 'resumen': meta.get('resumen', ''),
                      'orden': int(meta.get('orden', '99') or 99), 'tarjetas': tarjetas})
TEMAS.sort(key=lambda t: (t['orden'], t['titulo']))


def url_tema(t):
    return f'/temas/{t["slug"]}/'


def tarjeta_tema(t, nivel='h3'):
    return (f'<a class="tema-card" href="{url_tema(t)}" data-mc="{t["m"]}"><span class="tema-card-i">{ilustracion(t["imagen"], t["materia"])}</span>'
            f'<span class="tema-card-t"><small>{E(t["materia"])}</small><{nivel}>{E(t["titulo"])}</{nivel}><span>{E(t["resumen"])}</span></span></a>')


# ------------------------------------------------ tarjetas «¿Sabías que?»
TARJETAS = []
for t in TEMAS:
    for k in t['tarjetas']:
        TARJETAS.append({'t': k['t'], 'f': k['f'], 'tema': t['titulo'], 'u': url_tema(t) + (f'#{k["a"]}' if k['a'] else ''), 'm': t['m'], 'mat': t['materia']})
for g in GUIAS:
    for linea in re.findall(r'^> +(.+)$', g['cuerpo'], flags=re.M):
        txt = _plano_md(linea)
        if len(txt) < 30:
            continue
        TARJETAS.append({'t': txt, 'f': 'Guía: ' + g['titulo'], 'tema': g['titulo'], 'u': url_guia(g), 'm': slug(g['materia']), 'mat': g['materia']})
escribe('assets/tarjetas.json', json.dumps([{k: x[k] for k in ('t', 'f', 'tema', 'u', 'm')} for x in TARJETAS], ensure_ascii=False, separators=(',', ':')))


def dato_html(x):
    return (f'<article class="dato" data-mc="{x["m"]}"><span class="dato-m">{E(x["mat"])}</span><p>{E(x["t"])}</p>'
            f'<footer><small>{E(x["f"])}</small><a href="{E(x["u"])}">Leer más: {E(x["tema"])}</a></footer></article>')


def carrusel(lista, titulo='¿Sabías que?', sub='Datos breves sacados de los temas y las guías del sitio. Toca una tarjeta para leer el tema completo.'):
    if not lista:
        return ''
    return (f'<section class="sabias" data-tarjetas aria-roledescription="carrusel" aria-label="{E(titulo)}">'
            f'<div class="sabias-cab"><div><h2>{E(titulo)}</h2><p class="entrada">{E(sub)}</p></div>'
            f'<div class="sabias-ctl"><button type="button" class="ico-btn" data-prev aria-label="Tarjeta anterior">{ico("chevl")}</button>'
            f'<button type="button" class="ico-btn" data-next aria-label="Tarjeta siguiente">{ico("chev")}</button></div></div>'
            f'<div class="sabias-pista" tabindex="0">{"".join(dato_html(x) for x in lista)}</div></section>')


def muestra(n, semilla=7):
    """Selección variada y estable: alterna temas y guías para el HTML inicial (el JS la baraja)."""
    por_fuente = {}
    for x in TARJETAS:
        por_fuente.setdefault(x['tema'], []).append(x)
    grupos = list(por_fuente.values())
    rnd = _random.Random(semilla)
    for g in grupos:
        rnd.shuffle(g)
    rnd.shuffle(grupos)
    out = []
    while len(out) < n and any(grupos):
        for g in grupos:
            if g and len(out) < n:
                out.append(g.pop())
    return out


# ------------------------------------------------ páginas de cada tema
# «Salir rápido»: en temas de violencia, un botón que abre otra página sin dejar esta en el historial (Esc dos veces también).
SALIDA = ('<button type="button" class="salida-rapida" data-salida>Salir rápido de esta página</button>'
          '<p class="sec">Si alguien puede ver tu pantalla, el botón «Salir rápido» abre otra página. Recuerda borrar el historial del navegador.</p>')
CAJA_REV = alerta('Información general. No sustituye asesoría profesional. ' + REVISION + '. Los datos marcados [VERIFICAR CON FUENTE OFICIAL] deben confirmarse en la publicación oficial.'.replace('[VERIFICAR CON FUENTE OFICIAL]', f'<code>{VERIF}</code>'))
for t in TEMAS:
    m = t['meta']
    cuerpo, indice = _ids_h2(md_html(t['cuerpo']))
    claves = ''.join(f'<a class="clave" href="#{k["a"] or "contenido"}"><p>{E(k["t"])}</p><small>{E(k["f"])}</small></a>' for k in t['tarjetas'])
    normas = m.get('normas') if isinstance(m.get('normas'), list) else []
    guias = m.get('guias') if isinstance(m.get('guias'), list) else []
    filas_g = ''.join(f'<a class="fila" href="{E(g.split("|")[0].strip())}"><span><b>{E(g.split("|")[1].strip() if "|" in g else g)}</b><small>Guía</small></span>{ico("chev")}</a>' for g in guias)
    toc = ([('lo-mas-importante', 'Lo más importante')] if claves else []) + indice + ([('normas', 'Normas que lo respaldan')] if normas else []) + ([('guias', 'Guías relacionadas')] if guias else [])
    otros = [o for o in TEMAS if o is not t]
    otros = [o for o in otros if o['m'] == t['m']] + [o for o in otros if o['m'] != t['m']]
    escribe(f'temas/{t["slug"]}/index.html', pagina(
        t['titulo'], t['resumen'] or t['titulo'],
        f'''<div class="tema-hero"><div class="cont">{migas([("Inicio", "/"), ("Temas de interés", "/temas/"), (t["titulo"], "")])}
<div class="tema-hero-in"><div class="tema-hero-t"><span class="chip">{E(t["materia"])}</span><h1>{E(t["titulo"])}</h1><p class="entrada">{en_linea(t["resumen"])}</p>
<p class="sec">Actualizado: {E(m.get("actualizada", HOY))} · {REVISION}</p></div><div class="tema-hero-i">{ilustracion(t["imagen"], t["materia"], t["titulo"])}</div></div></div></div>
<div class="cont pag tema"><div class="tema-cols"><article class="tema-cuerpo guia">
{f'<section class="claves" aria-labelledby="lo-mas-importante"><h2 id="lo-mas-importante">Lo más importante</h2><div class="claves-r">{claves}</div></section>' if claves else ''}
{cuerpo}
{f'<section><h2 id="normas">Normas que lo respaldan</h2>{filas_articulos(normas)}</section>' if normas else ''}
{f'<section><h2 id="guias">Guías relacionadas</h2>{filas_g}</section>' if guias else ''}
{CAJA_REV}
</article><aside class="tema-indice"><nav aria-label="En esta página"><b>En esta página</b>{"".join(f'<a href="#{i}">{E(x)}</a>' for i, x in toc)}</nav></aside></div>
{SALIDA if m.get('salida_rapida', '').lower() in ('si', 'sí') else ''}<section class="otros"><h2>Otros temas</h2><div class="temas-r">{"".join(tarjeta_tema(o) for o in otros[:3])}</div><p><a class="mas" href="/temas/">Ver todos los temas</a></p></section>
</div>''', 'Temas'))

# Enlace «Explicado en un tema» en los artículos de la Constitución y de las leyes por artículos que cita cada tema
n_rel = 0
for t in TEMAS:
    rutas = set(re.findall(r'\]\((/leyes/[^)#\s]+)\)', t['cuerpo']))
    rutas |= {x.split('|')[0].strip() for x in (t['meta'].get('normas') or []) if x.strip().startswith('/leyes/')}
    for ruta in sorted(rutas):
        if insertar_en_articulo(ruta, f'data-tema="{t["slug"]}"',
                                f'<section class="tarjeta guia-rel" data-tema="{t["slug"]}" data-mc="{t["m"]}"><h2>Explicado en un tema</h2><a class="fila" href="{url_tema(t)}"><span><b>{E(t["titulo"])}</b><small>Tema de interés · {E(t["materia"])}</small></span>{ico("chev")}</a></section>',
                                f'Tema «{t["titulo"]}»'):
            n_rel += 1

# ------------------------------------------------ índice /temas/
if TEMAS:
    mats = []
    for t in TEMAS:
        if t['materia'] not in mats:
            mats.append(t['materia'])
    filtro = ('<div class="filtro-temas" role="group" aria-label="Filtrar por materia"><button type="button" aria-pressed="true" data-ft="">Todas</button>'
              + ''.join(f'<button type="button" aria-pressed="false" data-ft="{slug(x)}" data-mc="{slug(x)}">{E(x)}</button>' for x in mats) + '</div>')
    escribe('temas/index.html', pagina('Temas de interés', 'Lo esencial sobre derechos de la niñez, violencia contra la mujer, beneficios sociales, asistencia familiar, propiedad y otros temas, con la norma que lo respalda.',
        f'''<div class="cont pag">{migas([("Inicio", "/"), ("Temas de interés", "")])}<h1>Temas de interés</h1>
<p class="entrada">Lo esencial sobre los asuntos legales que más se consultan, en lenguaje claro y con la norma que lo respalda. {REVISION}.</p>
{filtro}<div class="temas-r" data-temas>{"".join(tarjeta_tema(t, "h2") for t in TEMAS)}</div>
{carrusel(muestra(14, 3))}
{alerta()}</div>''', 'Temas'))

# ------------------------------------------------ portada
def _n_docs(mat):
    return sum(1 for d in DOCS if d['materia'] == mat)


tiles = []
for mat in ORDEN_MATERIAS:
    k = _n_docs(mat)
    con_arts = os.path.isfile(os.path.join(OUT, 'leyes', slug(mat), 'index.html'))
    if not k and not con_arts:
        continue
    href = f'/leyes/{slug(mat)}/' if con_arts else f'/biblioteca/{slug(mat)}/'
    nt = sum(1 for t in TEMAS if t['materia'] == mat) + sum(1 for g in GUIAS if g['materia'] == mat)
    det = plural(k, 'documento', 'documentos') + (' · normas por artículos' if con_arts else '') + (f' · {plural(nt, "tema o guía", "temas y guías")}' if nt else '')
    tiles.append(f'<a class="mat-tile" data-mc="{slug(mat)}" href="{href}"><b>{E(mat)}</b><small>{det}</small></a>')
destacados = TEMAS[:6]
accesos = [('Biblioteca', '/biblioteca/', 'Normas completas en PDF, con visor y buscador'),
           ('Jurisprudencia', '/jurisprudencia/', 'Revistas, gacetas y autos supremos en PDF'),
           ('Guías', '/guias/', 'Trámites y derechos explicados paso a paso'),
           ('Cuestionarios', '/estudiantes/cuestionarios/', 'Para repasar y prepararse'),
           ('Glosario', '/glosario/', 'Términos jurídicos en lenguaje claro')]
if TEMAS:
    escribe('index.html', pagina('Leyes de Bolivia, al pie de la letra', 'Normas bolivianas en texto literal y en PDF, temas de interés y guías en lenguaje claro.',
        f'''<section class="hero portada"><div class="cont"><h1>Leyes de Bolivia, al pie de la letra</h1><p>El texto de las normas, explicado en lenguaje claro.</p>
<form class="buscador grande" role="search" action="/buscar/" method="get">{ico("search", 20)}<input type="search" name="q" aria-label="Buscar en todo el sitio" placeholder="Busca un tema, una norma o un artículo" autocomplete="off"><button type="submit">Buscar</button></form>
<p class="atajos">Consultas frecuentes: {" ".join(f'<a href="{url_tema(t)}">{E(t["titulo"].split(":")[0])}</a>' for t in TEMAS[:5])}</p></div></section>
<div class="cont pag portada-pag">
<section class="temas-portada"><div class="entre"><h2>Temas que más se consultan</h2><a class="mas" href="/temas/">Ver los {len(TEMAS)} temas</a></div>
<div class="temas-r">{"".join(tarjeta_tema(t) for t in destacados)}</div></section>
{carrusel(muestra(16))}
<section><h2>Explorar por materia</h2><p class="entrada">Cada materia tiene su color en todo el sitio.</p><div class="mat-r">{"".join(tiles)}</div></section>
<section><h2>Acceso rápido</h2><div class="rejilla r3">{"".join(f'<a class="fila" href="{h}"><span><b>{n}</b><small>{d}</small></span>{ico("chev")}</a>' for n, h, d in accesos)}<a class="fila" href="/buscar/"><span><b>Buscar</b><small>En normas, guías, temas y PDF</small></span>{ico("chev")}</a></div></section>
{alerta()}
</div>''', ''))
print(f'Temas: {len(TEMAS)} tema(s), enlazados desde {n_rel} artículo(s); {len(TARJETAS)} tarjeta(s) «¿Sabías que?» ({sum(len(t["tarjetas"]) for t in TEMAS)} de temas y {len(TARJETAS) - sum(len(t["tarjetas"]) for t in TEMAS)} de guías).')
