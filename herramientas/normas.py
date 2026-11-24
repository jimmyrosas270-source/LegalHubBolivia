# Normas por artículos que no vienen en sitio_base/: se leen de contenido/normas/<materia>/*.txt
# Se ejecuta desde construir.py (comparte sus funciones: pagina, escribe, ico, E, slug, OUT...) ANTES de las guías,
# para que las guías puedan citar estos artículos y recibir su recuadro «Explicado en lenguaje claro».
#
# Formato del archivo .txt (una colección de normas, cada una separada y en orden):
#   === Título de la norma
#   slug: opcional           (si no se pone, sale del título)
#   tipo: Ley
#   fecha: 1944-12-18        (AAAA-MM-DD)
#   epigrafe: texto opcional
#   <párrafos antes del primer artículo = preámbulo; separados por línea en blanco>
#   § Título o capítulo      (encabezado de sección del índice)
#   @ Artículo 1°            (empieza un artículo; sus párrafos van debajo, separados por línea en blanco)
#   Un párrafo que empieza con «Comuníquese» al final de la norma se muestra como fórmula de cierre.
import json as _json

COLECCIONES = [{
    'archivo': 'normas-que-modifican-la-lgt.txt',
    'materia': 'laboral',
    'slug': 'normas-que-modifican-la-lgt',
    'codigo': 'cmp',
    'titulo': 'Normas que modifican o complementan la Ley General del Trabajo',
    'rango': '1924 a 1945',
    'intro': ('Leyes y decretos de 1924 a 1945 que complementan o modifican la Ley General del Trabajo, publicados uno por uno y en el orden del archivo del editor. '
              'Cada norma tiene su propia página y cada artículo puede buscarse y enlazarse.'),
    'pdf_titulo': 'Compilación de normas que modifican la Ley General del Trabajo',
}, {
    'archivo': 'normas-transcritas.txt',
    'materia': 'laboral',
    'slug': 'normas-transcritas',
    'codigo': 'trn',
    'titulo': 'Normas transcritas de copias escaneadas',
    'rango': 'desde 2015',
    'intro': ('Normas que el editor tiene solo como copia escaneada, transcritas palabra por palabra y revisadas contra la imagen. '
              'Se conservan las erratas del original. Cada artículo puede buscarse y enlazarse; la copia escaneada está en la Biblioteca.'),
    'pdf_titulo': 'Resolución Bi-Ministerial 002/15',
}, {
    # 'unica': la colección es una sola norma; su página es la de la colección (/leyes/comercial/codigo-de-comercio/)
    'archivo': 'codigo-de-comercio.txt',
    'materia': 'comercial',
    'materia_nombre': 'Comercial',
    'materia_url': '/biblioteca/comercial/',
    'unica': True,
    'slug': 'codigo-de-comercio',
    'codigo': 'cco',
    'titulo': 'Código de Comercio',
    'rango': '1977',
    'alias': 'Código de Comercio|CCo|CCom|C. Com.|Código mercantil|Decreto Ley 14379|DL 14379',
    'intro': '',
    'pdf_titulo': '',
    'fuente': ('Texto de los artículos tomado de una edición anotada no oficial (se publican solo los artículos, sin las notas, concordancias ni comentarios de esa edición). '
               'Puede no incluir todas las modificaciones posteriores. Verifique en la Gaceta Oficial de Bolivia.'),
}]


def _leer_coleccion(ruta):
    txt = open(ruta, encoding='utf-8').read().replace('\r\n', '\n')
    normas = []
    for bloque in txt.split('=== ')[1:]:
        lineas = bloque.split('\n')
        n = {'titulo': lineas[0].strip(), 'slug': '', 'tipo': '', 'fecha': '', 'epigrafe': '', 'pre': [], 'items': [], 'cierre': []}
        i = 1
        while i < len(lineas) and re.match(r'^(slug|tipo|fecha|epigrafe):', lineas[i]):
            k, v = lineas[i].split(':', 1)
            n[k] = v.strip()
            i += 1
        cuerpo = '\n'.join(lineas[i:]).strip('\n')
        actual = None
        for par in re.split(r'\n\s*\n', cuerpo):
            par = par.strip()
            if not par:
                continue
            ls = par.split('\n')
            while ls and (ls[0].startswith('§ ') or ls[0].startswith('@ ')):
                cab = ls.pop(0)
                if cab.startswith('§ '):
                    n['items'].append({'sec': cab[2:].strip()})
                    actual = None
                else:
                    actual = {'label': cab[2:].strip().rstrip('.'), 'paras': []}
                    n['items'].append(actual)
            resto = ' '.join(x.strip() for x in ls).strip()
            if not resto:
                continue
            if actual is None:
                n['pre'].append(resto)
            else:
                actual['paras'].append(resto)
        # fórmula de cierre
        arts = [it for it in n['items'] if 'label' in it]
        if arts and arts[-1]['paras'] and arts[-1]['paras'][-1].startswith('Comun'):
            n['cierre'].append(arts[-1]['paras'].pop())
        n['slug'] = n['slug'] or slug(n['titulo'])
        for it in n['items']:
            if 'label' in it:
                m = re.search(r'(\d+|[úu]nico)', it['label'], re.I)
                it['num'] = m.group(1).lower().replace('ú', 'u') if m else str(len(arts))
                if m and m.group(1).isdigit() and not it['label'].lower().startswith('art'):
                    it['num'] = slug(it['label'])  # «Disposición transitoria 1» → disposicion-transitoria-1 (no choca con articulo-1)
        normas.append(n)
    return normas


def _fecha_larga(iso):
    m = re.match(r'(\d{4})-(\d\d)-(\d\d)', iso or '')
    if not m:
        return ''
    meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
    return f'{int(m.group(3))} de {meses[int(m.group(2)) - 1]} de {m.group(1)}'


BARRA_ART = ('<div class="barra"><a class="b" href="{idx}#indice">' + ico('book', 18).replace('<svg', '<svg', 1) + 'Índice</a>'
             '<button class="b" type="button" data-lectura aria-pressed="false">' + ico('book', 18) + 'Lectura</button>'
             '<button class="b" type="button" data-copiar aria-label="Copiar enlace">' + ico('plus', 18).replace('<path d="M12 5v14M5 12h14"/>', '<path d="M10 14a4 4 0 005.7 0l3-3a4 4 0 00-5.7-5.7l-1 1M14 10a4 4 0 00-5.7 0l-3 3a4 4 0 005.7 5.7l1-1"/>') + 'Copiar</button></div>')


def _sobre(estado_extra=''):
    return (f'<section class="tarjeta sobre"><h2>Sobre esta norma</h2><dl><dt>Estado</dt><dd><span class="tag ver">Verificar</span></dd>'
            f'<dt>Última revisión</dt><dd>{HOY}</dd><dt>Versión</dt><dd>1</dd><dt>Fuente</dt><dd>{E(FUENTE)}</dd></dl></section>{estado_extra}{alerta()}')


def construir_normas():
    indice = []
    total_arts = 0
    resumen = []
    for C in COLECCIONES:
        ruta_txt = os.path.join(RAIZ, 'contenido', 'normas', C['materia'], C['archivo'])
        if not os.path.isfile(ruta_txt):
            AVISOS.append(f'Colección de normas {C["archivo"]}: no se encontró el archivo.')
            continue
        normas = _leer_coleccion(ruta_txt)
        base = f'/leyes/{C["materia"]}/{C["slug"]}/'
        unica = C.get('unica', False)
        mat_n, mat_u = C.get('materia_nombre', 'Laboral'), C.get('materia_url', f'/leyes/{C["materia"]}/')
        pdf_slug = slug(C['pdf_titulo'])
        hay_pdf = bool(C['pdf_titulo']) and any(d['slug'] == pdf_slug for d in DOCS)
        enlace_pdf = (f'<p class="botones"><a class="btn sec" href="/biblioteca/{pdf_slug}/">Ver el archivo original (PDF)</a></p>' if hay_pdf else '')
        vistos = set()
        # ---- portada de la colección
        tarjetas = []
        for n in normas:
            if n['slug'] in vistos:
                ERRORES.append(f'Colección {C["archivo"]}: slug repetido «{n["slug"]}».')
            vistos.add(n['slug'])
            arts = [it for it in n['items'] if 'label' in it]
            cuenta = (f'{len(arts)} artículo' + ('' if len(arts) == 1 else 's')) if arts else 'Texto completo'
            epi = f'<p>{E(n["epigrafe"])}</p>' if n['epigrafe'] else ''
            tarjetas.append(f'<article class="tarjeta"><div class="entre"><span class="etq">{E(n["tipo"])}</span><span class="tag ver">Verificar</span></div>'
                            f'<h2 class="h-norma"><a href="{base}{n["slug"]}/">{E(n["titulo"])}</a></h2>{epi}<p>{cuenta}</p>'
                            f'<p><a class="btn" href="{base}{n["slug"]}/">{"Ver artículos" if arts else "Leer"}</a></p></article>')
        n_arts = sum(1 for n in normas for it in n['items'] if 'label' in it)
        migas_c = migas([('Inicio', '/'), ('Normativa', '/leyes/'), (mat_n, mat_u), (C['titulo'], base)])
        cuerpo = (f'<div class="cont pag estrecha">{migas_c}<h1>{E(C["titulo"])}</h1>'
                  f'<p class="entrada">{len(normas)} normas, de {C["rango"]} · {n_arts} artículos</p><p>{E(C["intro"])}</p>{enlace_pdf}'
                  f'<div class="alerta">{ico("info")}<div>El texto sigue el archivo del editor y puede traer errores de transcripción de la fuente. Las normas más antiguas pueden estar derogadas o modificadas: '
                  f'no se afirma su vigencia. Antes de citar, verifica en la publicación oficial.</div></div>{"".join(tarjetas)}</div>')
        if not unica:
          escribe(html_de(base), pagina(C['titulo'], f'{len(normas)} leyes y decretos de {C["rango"]} que modifican o complementan la Ley General del Trabajo, por artículos.', cuerpo, 'Normativa'))
        # ---- cada norma
        for n in normas:
            ruta_n = base if unica else f'{base}{n["slug"]}/'
            arts = [it for it in n['items'] if 'label' in it]
            total_arts += len(arts)
            fecha_txt = _fecha_larga(n['fecha'])
            ruta_migas = [('Inicio', '/'), ('Normativa', '/leyes/'), (mat_n, mat_u)] + ([] if unica else [(C['titulo'], base)]) + [(n['titulo'], ruta_n)]
            epi = E(n['epigrafe']) if n['epigrafe'] else ''
            pre = ''.join(f'<p>{E(p)}</p>' for p in n['pre'])
            if not arts:  # norma sin artículos: el texto va en la propia página
                texto = pre + ''.join(f'<p>{E(p)}</p>' for p in n['cierre'])
                cuerpo_n = (f'<div class="cont pag"><nav class="migas" aria-label="Migas de pan">{"".join(("<a href=" + chr(34) + h + chr(34) + ">" + E(t) + "</a><span aria-hidden=" + chr(34) + "true" + chr(34) + ">›</span>") for t, h in ruta_migas[:-1])}<span aria-current="page">{E(n["titulo"])}</span></nav>'
                            f'<div class="dos"><div><span class="etq">{E(n["tipo"])}</span><h1>{E(n["titulo"])}</h1>{f"<p class=" + chr(34) + "entrada" + chr(34) + ">" + epi + "</p>" if epi else ""}'
                            f'<article class="legal"><div class="entre"><span class="etq">Texto literal</span><span class="tag ver">Verificar</span></div>{texto}<footer>{E(FUENTE)}</footer></article>'
                            f'<p class="botones"><a class="btn sec" href="{base}">Volver a la colección</a></p></div><aside>{_sobre()}</aside></div></div>')
                escribe(html_de(ruta_n), pagina(n['titulo'], (n['epigrafe'] or n['titulo'])[:155], cuerpo_n, 'Normativa'))
                indice.append({'n': 1, 'u': ruta_n, 't': ' '.join(n['pre'] + n['cierre']), 'k': n['titulo'], 'c': C['codigo'], 'r': 'Texto completo', 'x': 1})
                continue
            miga_html = ''.join(f'<a href="{h}">{E(t)}</a><span aria-hidden="true">›</span>' for t, h in ruta_migas[:-1]) + f'<span aria-current="page">{E(n["titulo"])}</span>'
            # índice con secciones
            idx_html = []
            lote = []
            def vuelca():
                if lote:
                    idx_html.append('<div class="arts">' + ''.join(lote) + '</div>')
                    lote.clear()
            for it in n['items']:
                if 'sec' in it:
                    vuelca()
                    idx_html.append(f'<div class="idx n1"><b>{E(it["sec"])}</b></div>')
                else:
                    lote.append(f'<a href="{ruta_n}articulo-{it["num"]}/">{E(it["label"])}</a>')
            vuelca()
            enc = ''
            if pre:
                enc = f'<article class="legal enc"><div class="entre"><span class="etq">Texto literal</span></div>{pre}</article>'
            cierre = ''.join(f'<p>{E(p)}</p>' for p in n['cierre'])
            cierre_html = f'<article class="legal enc"><div class="entre"><span class="etq">Fórmula de cierre · texto literal</span></div>{cierre}</article>' if cierre else ''
            fecha_p = f'<p class="entrada">{E(epi) if epi else E(fecha_txt)}</p>'
            cuerpo_n = (f'<div class="cont pag"><nav class="migas" aria-label="Migas de pan">{miga_html}</nav>'
                        f'<div class="dos"><div><span class="etq">{E(n["tipo"])}</span><h1>{E(n["titulo"])}</h1>{fecha_p}'
                        f'<p class="botones"><a class="btn" href="{ruta_n}articulo-{arts[0]["num"]}/">Empezar por el {E(arts[0]["label"].lower()) if arts[0]["label"].lower().startswith("art") else "primer artículo"}</a>'
                        + ('' if unica else f'<a class="btn sec" href="{base}">Volver a la colección</a>') + f'</p>{enc}'
                        + (f'<div class="alerta">{ico("info")}<div>{E(C["fuente"])}</div></div>' if C.get('fuente') else '') +
                        f'<section id="indice" class="tarjeta indice-norma"><h2>Índice</h2>{"".join(idx_html)}</section>{cierre_html}</div>'
                        f'<aside>{_sobre()}</aside></div></div>')
            escribe(html_de(ruta_n), pagina(n['titulo'], (n['epigrafe'] or f'{n["titulo"]}: índice de artículos.')[:155], cuerpo_n, 'Normativa'))
            # artículos
            for k, it in enumerate(arts):
                prev = arts[k - 1] if k else None
                sig = arts[k + 1] if k + 1 < len(arts) else None
                vec = ''
                if prev:
                    vec += f'<a href="{ruta_n}articulo-{prev["num"]}/">{ico("chevl", 18)}{E(prev["label"])}</a>'
                if sig:
                    vec += f'<a href="{ruta_n}articulo-{sig["num"]}/">{E(sig["label"])}{ico("chev", 18)}</a>'
                if not vec:
                    vec = f'<a href="{ruta_n}">{ico("chevl", 18)}Volver a la norma</a>'
                # sección a la que pertenece
                sec = ''
                for it2 in n['items']:
                    if it2 is it:
                        break
                    if 'sec' in it2:
                        sec = it2['sec']
                ruta_h = f'<div class="ruta"><span>{E(n["titulo"])}</span>' + (f'<b>{E(sec)}</b>' if sec else '') + '</div>'
                texto = ''.join(f'<p>{E(p)}</p>' for p in it['paras'])
                art_migas = miga_html.replace(f'<span aria-current="page">{E(n["titulo"])}</span>', f'<a href="{ruta_n}">{E(n["titulo"])}</a><span aria-hidden="true">›</span><span aria-current="page">{E(it["label"])}</span>')
                cuerpo_a = (f'<div class="cont pag"><nav class="migas" aria-label="Migas de pan">{art_migas}</nav>'
                            f'<div class="art"><div class="centro">{BARRA_ART.format(idx=ruta_n)}{ruta_h}'
                            f'<article class="legal"><div class="entre"><span class="etq">Texto legal literal</span><span class="tag ver">Verificar</span></div><h1>{E(it["label"])}</h1>{texto}<footer>{E(C.get("fuente") or FUENTE)}</footer></article>'
                            f'<nav class="vecinos" aria-label="Textos contiguos">{vec}</nav></div><aside class="lateral">{_sobre()}</aside></div></div>')
                desc = ' '.join(it['paras'])[:155]
                escribe(html_de(f'{ruta_n}articulo-{it["num"]}/'), pagina(f'{it["label"]} · {n["titulo"]}', desc, cuerpo_a, 'Normativa'))
                indice.append({'n': int(it['num']) if it['num'].isdigit() else 1, 'u': f'{ruta_n}articulo-{it["num"]}/', 't': ' '.join(it['paras']),
                               'k': n['titulo'], 'c': C['codigo'], 'r': it['label'], 'x': 1, **({'m': C['alias']} if C.get('alias') else {})})
        resumen.append((C, len(normas), n_arts, base))
        # tarjeta en la portada de la materia
        pm = os.path.join(OUT, 'leyes', C['materia'], 'index.html')
        if unica:
            pass
        elif os.path.isfile(pm):
            doc = open(pm, encoding='utf-8').read()
            tarj = (f'<article class="tarjeta"><div class="entre"><span class="etq">Normas históricas</span><span class="tag ver">Verificar</span></div>'
                    f'<h2 class="h-norma"><a href="{base}">{E(C["titulo"])}</a></h2><p class="sec">{len(normas)} normas · {C["rango"]}</p><p>{n_arts} artículos</p>'
                    f'<small>Revisada: {HOY} · Versión 1</small><p><a class="btn" href="{base}">Ver las normas</a></p></article>')
            if 'class="vacio"' in doc and base not in doc:
                doc = doc.replace('<div class="vacio">', tarj + '<div class="vacio">', 1)
                doc = doc.replace('3 normas cargadas', f'3 normas cargadas y 1 colección de {len(normas)} normas históricas')
                open(pm, 'w', encoding='utf-8').write(doc)
            else:
                AVISOS.append(f'Portada de /leyes/{C["materia"]}/: no se pudo insertar la tarjeta de «{C["titulo"]}».')
    # ---- índice de búsqueda, filtro y script
    if indice:
        pi = os.path.join(OUT, 'buscar', 'indice.json')
        datos = _json.load(open(pi, encoding='utf-8'))
        datos = [d for d in datos if d.get('c') not in {c['codigo'] for c in COLECCIONES}] + indice
        with open(pi, 'w', encoding='utf-8') as f:
            _json.dump(datos, f, ensure_ascii=False, separators=(',', ':'))
        pb = os.path.join(OUT, 'buscar', 'index.html')
        doc = open(pb, encoding='utf-8').read()
        for C, _, _, _ in resumen:
            op = f'<option value="{C["codigo"]}">{E(C["titulo"])} ({C["rango"].replace(" a ", "-")})</option>'
            if op not in doc:
                doc = doc.replace('</select>', op + '</select>', 1)
        open(pb, 'w', encoding='utf-8').write(doc)
        pj = os.path.join(OUT, 'assets', 'sitio.js')
        js = open(pj, encoding='utf-8').read()
        a1 = "'<b>Artículo '+a.n+'</b>"
        a2 = "return a.n===+num[1]}"
        if a1 in js:
            js = js.replace(a1, "'<b>'+(a.r||('Artículo '+a.n))+'</b>")
        else:
            AVISOS.append('sitio.js: no se pudo adaptar el rótulo de los resultados de búsqueda.')
        if a2 in js:
            js = js.replace(a2, "return a.n===+num[1]&&(!a.x||fn===a.c)}")
        else:
            AVISOS.append('sitio.js: no se pudo excluir las normas históricas de la búsqueda por número.')
        open(pj, 'w', encoding='utf-8').write(js)
        # conteos en las portadas
        for pp in ('leyes/index.html', 'index.html'):
            q = os.path.join(OUT, pp)
            if os.path.isfile(q):
                d2 = open(q, encoding='utf-8').read()
                d2 = d2.replace('<b>Laboral</b><small>3 normas</small>', '<b>Laboral</b><small>3 normas y 24 históricas</small>')
                open(q, 'w', encoding='utf-8').write(d2)
    return resumen, total_arts


NORMAS_RESUMEN, NORMAS_ARTS = construir_normas()
for _C, _n, _a, _b in NORMAS_RESUMEN:
    print(f'Normas por artículos: «{_C["titulo"]}» → {_b} ({_n} normas, {_a} artículos).')
