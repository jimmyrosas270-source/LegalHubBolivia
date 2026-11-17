# -*- coding: utf-8 -*-
"""Secciones por tipo de norma (se ejecuta dentro de construir.py con exec).

- /biblioteca/<materia>/<tipo>/: solo un tipo de norma de una materia (p. ej. Laboral › Sentencias constitucionales).
- /biblioteca/tipos/<tipo>/: un tipo de norma en todas las materias.
- Autos supremos: vienen de contenido/autos_supremos.json (están dentro de las revistas de Jurisprudencia).
"""

_aut = json.load(open(os.path.join(RAIZ, 'contenido', 'autos_supremos.json'), encoding='utf-8'))
AUTOS = _aut['autos']
REVISTA_AUTOS = _aut['revista']
GRUPO_AUTOS = 'Autos supremos'
import glob
GUIA_TITULO = {}
for _f in glob.glob(os.path.join(RAIZ, 'contenido', 'guias', '*', '*.md')):
    _m = re.search(r'^titulo: *(.+)$', open(_f, encoding='utf-8').read(), re.M)
    GUIA_TITULO[f'/guias/{os.path.basename(os.path.dirname(_f))}/{os.path.basename(_f)[:-3]}/'] = _m.group(1).strip() if _m else 'Guía'

DESC_TIPO = {
    'Códigos': 'Constituciones y códigos.',
    'Leyes': 'Leyes de la República y del Estado Plurinacional.',
    'Decretos leyes': 'Decretos leyes, dictados por gobiernos de facto con fuerza de ley.',
    'Decretos supremos': 'Decretos supremos del Órgano Ejecutivo y sus fe de erratas.',
    'Resoluciones': 'Resoluciones ministeriales y administrativas.',
    'Reglamentos y protocolos': 'Reglamentos y protocolos de aplicación.',
    'Sentencias constitucionales': 'Sentencias del Tribunal Constitucional Plurinacional: amparos y acciones de inconstitucionalidad.',
    GRUPO_AUTOS: 'Autos supremos del Tribunal Supremo de Justicia, publicados en las revistas de Jurisprudencia.',
    'Otros documentos': 'Compilaciones, guías y otros documentos de consulta.',
}


def autos_de(m=None):
    return [a for a in AUTOS if m is None or a['materia'] == m]


def tarjeta_auto(a, con_materia=False):
    u = f'/jurisprudencia/{REVISTA_AUTOS}/leer/#page={a["pagina"]}'
    guias = ''.join(f'<a href="{g}">Guía: {E(GUIA_TITULO.get(g, "relacionada"))}</a>' for g in a.get('guias', [])[:2])
    etq = f'<span class="etq">{E(a["materia"])}</span>' if con_materia else ''
    return (f'<article class="tarjeta auto">{etq}<h3><a href="{u}">Auto Supremo {E(a["numero"])}</a></h3>'
            f'<small>{E(a["fecha"])} · {E(a["sala"])}</small><p>{E(a["tema"])}</p>'
            f'<p class="libro-acc"><a href="{u}">Leer el resumen (pág. {a["pagina"]})</a>{guias}</p></article>')


def tipos_de_materia(docs, m):
    """[(grupo, cantidad)] presentes en una materia, en el orden fijo, con los autos al final."""
    salida = [(g, sum(1 for d in docs if d['tgrupo'] == g)) for g in NOMBRES_GRUPO]
    salida = [(g, k) for g, k in salida if k]
    k = len(autos_de(m))
    if k:
        if any(g == GRUPO_AUTOS for g, _ in salida):
            salida = [(g, n + k if g == GRUPO_AUTOS else n) for g, n in salida]
        else:
            i = next((n for n, (g, _) in enumerate(salida) if g in ('Otras sentencias y autos', 'Otros documentos')), len(salida))
            salida.insert(i, (GRUPO_AUTOS, k))
    return salida


def enlaces_tipo(m, docs):
    t = tipos_de_materia(docs, m)
    if not t:
        return ''
    return ('<nav class="por-tipo" aria-label="Ver por tipo de norma"><b>Ver por tipo:</b>'
            + ''.join(f'<a href="/biblioteca/{slug(m)}/{slug(g)}/">{E(g)} <small>({k})</small></a>' for g, k in t) + '</nav>')


def paginas_por_tipo(S, DOCS, tarjeta, por_materia):
    """Escribe /biblioteca/<materia>/<tipo>/ y /biblioteca/tipos/<tipo>/. Devuelve el bloque para /biblioteca/."""
    n_pag = 0
    materias = [m for m in ORDEN_MATERIAS if m in por_materia or autos_de(m)] + [m for m in por_materia if m not in ORDEN_MATERIAS]
    totales = {}
    for m in materias:
        docs = por_materia.get(m, [])
        for g, k in tipos_de_materia(docs, m):
            totales.setdefault(g, []).append((m, k))
            if g == GRUPO_AUTOS:
                cuerpo = (f'<div class="rejilla autos">{"".join(tarjeta_auto(a) for a in sorted(autos_de(m), key=lambda a: a["pagina"]))}</div>'
                          f'<div class="estante">{"".join(tarjeta(d, etq=d["tipo"]) for d in docs if d["tgrupo"] == g)}</div>'
                          f'<p class="sec">Los temas se describen con palabras propias a partir del resumen publicado por el Tribunal, sin nombres de las partes. '
                          f'Ver la revista completa en <a href="/jurisprudencia/">Jurisprudencia</a>.</p>')
            else:
                cuerpo = (f'<div class="filtros"><label class="filtro">{ico("search", 20)}<input type="search" id="filtro" placeholder="Filtrar por nombre, número o tema" aria-label="Filtrar"></label></div>'
                          f'<p id="cuenta" class="sec" role="status" aria-live="polite">{plural(k, "documento", "documentos")}</p>'
                          f'<div class="estante">{"".join(tarjeta(d, etq=d["tipo"]) for d in docs if d["tgrupo"] == g)}</div>'
                          f'<div id="nada" class="vacio" hidden>Ninguna coincidencia.</div>')
            escribe(f'biblioteca/{slug(m)}/{slug(g)}/index.html', pagina(
                f'{g} · {m}', f'{g} de materia {m.lower()}: {DESC_TIPO.get(g, "")}',
                f'''<div class="cont pag">{migas([("Inicio", "/"), ("Biblioteca", "/biblioteca/"), (m, f"/biblioteca/{slug(m)}/"), (g, "")])}<h1>{E(g)} <small class="sub-h1">· {E(m)}</small></h1>
<p class="entrada">{E(DESC_TIPO.get(g, ""))} {plural(k, "auto supremo", "autos supremos") if g == GRUPO_AUTOS else plural(k, "documento", "documentos")} de materia {E(m.lower())}.</p>
{enlaces_tipo(m, docs)}
{cuerpo}
<p><a class="mas" href="/biblioteca/{slug(m)}/">Ver todo {E(m.lower())}</a> · <a class="mas" href="/biblioteca/tipos/{slug(g)}/">{E(g)} de todas las materias</a></p>{alerta(S["aviso"])}</div>''',
                'Biblioteca', scripts='' if g == GRUPO_AUTOS else '<script src="/assets/biblioteca.js" defer></script>\n'))
            n_pag += 1
    orden_g = [g for g in NOMBRES_GRUPO if g in totales]
    for g in orden_g:
        secciones = []
        for m, k in totales[g]:
            if g == GRUPO_AUTOS:
                tarj = ''.join(tarjeta_auto(a) for a in sorted(autos_de(m), key=lambda a: a['pagina']))
                secciones.append(f'<section class="grupo-lib"><h2 class="grupo-tit">{E(m)} <small>({k})</small></h2><div class="rejilla autos">{tarj}</div>'
                                 f'<p><a class="mas" href="/biblioteca/{slug(m)}/{slug(g)}/">Solo {E(m.lower())}</a></p></section>')
            else:
                tarj = ''.join(tarjeta(d, etq=d['tipo']) for d in por_materia[m] if d['tgrupo'] == g)
                secciones.append(f'<section class="grupo-lib"><h2 class="grupo-tit">{E(m)} <small>({k})</small></h2><div class="estante">{tarj}</div>'
                                 f'<p><a class="mas" href="/biblioteca/{slug(m)}/{slug(g)}/">Solo {E(m.lower())}</a></p></section>')
        total = sum(k for _, k in totales[g])
        escribe(f'biblioteca/tipos/{slug(g)}/index.html', pagina(
            f'{g} · Biblioteca', f'{g}: {DESC_TIPO.get(g, "")}',
            f'''<div class="cont pag">{migas([("Inicio", "/"), ("Biblioteca", "/biblioteca/"), (g, "")])}<h1>{E(g)}</h1>
<p class="entrada">{E(DESC_TIPO.get(g, ""))} {plural(total, "documento", "documentos")}, por materia.</p>
{"".join(secciones)}{alerta(S["aviso"])}</div>''', 'Biblioteca'))
        n_pag += 1
    print(f'Páginas por tipo de norma: {n_pag}.')
    return ('<h2 class="grupo-tit">Por tipo de norma</h2><nav class="por-tipo grande" aria-label="Tipos de norma">'
            + ''.join(f'<a href="/biblioteca/tipos/{slug(g)}/">{E(g)} <small>({sum(k for _, k in totales[g])})</small></a>' for g in orden_g) + '</nav>')
