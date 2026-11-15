"""Contenido editorial: guías, preguntas frecuentes y glosario.

Lo ejecuta construir.py (comparte sus funciones: pagina, escribe, migas, alerta, tag, ico, slug, E, OUT...).

Fuentes (en contenido/):
  guias/<materia>/<nombre>.md   -> /guias/<materia>/<nombre>/
  preguntas/<materia>.md        -> /preguntas/<materia>/
  glosario.json                 -> /glosario/

Formato de los .md: encabezado entre líneas '---' (clave: valor; listas con '- '),
y cuerpo con '## Título', párrafos, listas '- ' o '1. ', '> ' para «¿Sabías que?»,
'!! ' para una advertencia, **negrita** y [texto](/enlace).
En preguntas, cada pregunta empieza con '### '.
"""
CONT = os.path.join(RAIZ, 'contenido')
REVISION = 'Pendiente de revisión legal humana'


def leer_md(ruta):
    lineas = open(ruta, encoding='utf-8').read().replace('\r\n', '\n').split('\n')
    meta, i = {}, 0
    if lineas and lineas[0].strip() == '---':
        i, clave = 1, None
        while i < len(lineas) and lineas[i].strip() != '---':
            l = lineas[i]
            if l.startswith('- ') and clave:
                meta.setdefault(clave, [])
                if not isinstance(meta[clave], list):
                    meta[clave] = []
                meta[clave].append(l[2:].strip())
            elif ':' in l:
                clave, v = l.split(':', 1)
                clave = clave.strip().lower()
                meta[clave] = v.strip()
            i += 1
        i += 1
    return meta, '\n'.join(lineas[i:])


def en_linea(t):
    t = E(t, quote=False)
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', t)
    return t.replace('[VERIFICAR]', f'<code>{VERIF}</code>')


def md_html(texto):
    out, lista, parr = [], None, []

    def cierra():
        nonlocal lista, parr
        if parr:
            out.append('<p>' + en_linea(' '.join(parr)) + '</p>')
            parr = []
        if lista:
            out.append(f'</{lista}>')
            lista = None

    for l in texto.split('\n'):
        s = l.strip()
        if not s:
            cierra()
            continue
        m_ol = re.match(r'^\d+[.)]\s+(.*)', s)
        if s.startswith('## '):
            cierra(); out.append(f'<h2>{en_linea(s[3:])}</h2>')
        elif s.startswith('### '):
            cierra(); out.append(f'<h3>{en_linea(s[4:])}</h3>')
        elif s.startswith('> '):
            cierra(); out.append(f'<aside class="curiosidad"><span class="etq">¿Sabías que?</span><p>{en_linea(s[2:])}</p></aside>')
        elif s.startswith('!! '):
            cierra(); out.append(alerta(en_linea(s[3:])))
        elif s.startswith('- ') or m_ol:
            tipo = 'ul' if s.startswith('- ') else 'ol'
            if parr:
                out.append('<p>' + en_linea(' '.join(parr)) + '</p>'); parr = []
            if lista != tipo:
                if lista:
                    out.append(f'</{lista}>')
                out.append(f'<{tipo} class="lista">'); lista = tipo
            out.append('<li>' + en_linea(s[2:] if tipo == 'ul' else m_ol.group(1)) + '</li>')
        else:
            if lista:
                out.append(f'</{lista}>'); lista = None
            parr.append(s)
    cierra()
    return '\n'.join(out)


def filas_articulos(lista):
    out = []
    for item in lista or []:
        partes = [p.strip() for p in item.split('|')]
        ruta, nombre, norma = (partes + ['', '', ''])[:3]
        out.append(f'<a class="fila" href="{E(ruta)}"><span><b class="serif">{E(nombre)}</b><small>{E(norma)}</small></span>{ico("chev")}</a>')
    return ''.join(out)


def insertar_en_articulo(ruta, marca, bloque, aviso):
    p = os.path.join(OUT, html_de(ruta))
    if not os.path.isfile(p):
        AVISOS.append(f'{aviso}: no existe la página {ruta}.')
        return False
    doc = open(p, encoding='utf-8').read()
    if marca in doc:
        return False
    if '<aside class="lateral">' in doc:
        doc = doc.replace('<aside class="lateral">', '<aside class="lateral">' + bloque, 1)
    elif '<nav class="vecinos"' in doc:
        doc = doc.replace('<nav class="vecinos"', bloque + '<nav class="vecinos"', 1)
    else:
        AVISOS.append(f'{aviso}: no se encontró dónde insertar el enlace en {ruta}.')
        return False
    open(p, 'w', encoding='utf-8').write(doc)
    return True


# ------------------------------------------------ guías
GUIAS = []
dir_g = os.path.join(CONT, 'guias')
if os.path.isdir(dir_g):
    for mat in sorted(os.listdir(dir_g)):
        dm = os.path.join(dir_g, mat)
        if not os.path.isdir(dm):
            continue
        for fn in sorted(os.listdir(dm)):
            if not fn.endswith('.md'):
                continue
            meta, cuerpo = leer_md(os.path.join(dm, fn))
            if meta.get('publicar', 'si').lower() in ('no', 'false'):
                continue
            GUIAS.append({'materia_slug': mat, 'slug': fn[:-3], 'meta': meta, 'cuerpo': cuerpo,
                          'materia': meta.get('materia') or mat.capitalize(), 'titulo': meta.get('titulo') or fn[:-3]})

# Guías que ya trae sitio_base (se conservan en el índice)
guias_base = []
dir_out_g = os.path.join(OUT, 'guias')
if os.path.isdir(dir_out_g):
    propias = {(g['materia_slug'], g['slug']) for g in GUIAS}
    for dp, _, fs in os.walk(dir_out_g):
        rel = os.path.relpath(dp, dir_out_g).split(os.sep)
        if 'index.html' in fs and len(rel) == 2 and tuple(rel) not in propias:
            s = open(os.path.join(dp, 'index.html'), encoding='utf-8').read()
            h1 = re.search(r'<h1>(.*?)</h1>', s)
            chip = re.search(r'<span class="chip">(.*?)</span>', s)
            if h1:
                guias_base.append({'url': f'/guias/{rel[0]}/{rel[1]}/', 'titulo': html.unescape(h1.group(1)), 'materia': html.unescape(chip.group(1)) if chip else rel[0]})


def url_guia(g):
    return f'/guias/{g["materia_slug"]}/{g["slug"]}/'


for g in GUIAS:
    m = g['meta']
    arts = m.get('articulos') if isinstance(m.get('articulos'), list) else []
    ley = f'<section><h2>Dónde está la ley</h2>{filas_articulos(arts)}</section>' if arts else ''
    resumen = f'<section class="tarjeta"><h2>En pocas palabras</h2><p>{en_linea(m["resumen"])}</p></section>' if m.get('resumen') else ''
    publico = f'<p class="sec">Para: {E(m["publico"])}</p>' if m.get('publico') else ''
    escribe(f'guias/{g["materia_slug"]}/{g["slug"]}/index.html', pagina(
        g['titulo'], m.get('resumen', g['titulo']),
        f'''<div class="cont pag estrecha guia">{migas([("Inicio", "/"), ("Guías", "/guias/"), (g["materia"], f"/guias/{g['materia_slug']}/"), (g["titulo"], "")])}<span class="chip">{E(g["materia"])}</span><h1>{E(g["titulo"])}</h1>
<p class="sec">Actualizada: {E(m.get("actualizada", HOY))} · {REVISION}</p>{publico}
{resumen}
{md_html(g["cuerpo"])}
{ley}
{alerta("Información general. No sustituye asesoría profesional. Los datos marcados [VERIFICAR CON FUENTE OFICIAL] deben confirmarse en la publicación oficial.")}</div>''', 'Guías'))
    for item in arts:
        ruta = item.split('|')[0].strip()
        insertar_en_articulo(ruta, f'data-guia="{g["slug"]}"',
                             f'<section class="tarjeta guia-rel" data-guia="{g["slug"]}"><h2>Explicado en lenguaje claro</h2><a class="fila" href="{url_guia(g)}"><span><b>{E(g["titulo"])}</b><small>Guía · {E(g["materia"])}</small></span>{ico("chev")}</a></section>',
                             f'Guía «{g["titulo"]}»')

# ------------------------------------------------ preguntas frecuentes
PREG = []
dir_p = os.path.join(CONT, 'preguntas')
if os.path.isdir(dir_p):
    for fn in sorted(os.listdir(dir_p)):
        if not fn.endswith('.md'):
            continue
        meta, cuerpo = leer_md(os.path.join(dir_p, fn))
        bloques = re.split(r'^### ', cuerpo, flags=re.M)[1:]
        items = []
        for b in bloques:
            preg, _, resp = b.partition('\n')
            items.append((preg.strip(), resp.strip()))
        mat = fn[:-3]
        titulo = meta.get('titulo') or f'Preguntas frecuentes: {mat}'
        PREG.append({'materia_slug': mat, 'materia': meta.get('materia') or mat.capitalize(), 'titulo': titulo, 'n': len(items)})
        det = ''.join(f'<details class="preg" id="p{k}"><summary>{en_linea(p)}</summary><div>{md_html(r)}</div></details>' for k, (p, r) in enumerate(items, 1))
        escribe(f'preguntas/{mat}/index.html', pagina(titulo, meta.get('resumen', titulo),
            f'''<div class="cont pag estrecha">{migas([("Inicio", "/"), ("Guías", "/guias/"), (titulo, "")])}<span class="chip">{E(meta.get("materia") or mat)}</span><h1>{E(titulo)}</h1>
<p class="entrada">{en_linea(meta.get("resumen", "Respuestas breves en lenguaje claro."))}</p><p class="sec">{REVISION}</p>{det}
{alerta("Información general. No sustituye asesoría profesional. Los datos marcados [VERIFICAR CON FUENTE OFICIAL] deben confirmarse en la publicación oficial.")}</div>''', 'Guías'))

# ------------------------------------------------ índices de guías
materias_g = {}
for g in GUIAS:
    materias_g.setdefault((g['materia_slug'], g['materia']), []).append(g)
if GUIAS or PREG:
    bloques = []
    for (ms, mn), gs in materias_g.items():
        pr = [p for p in PREG if p['materia_slug'] == ms]
        filas = ''.join(f'<a class="fila" href="{url_guia(g)}"><span><b>{E(g["titulo"])}</b><small>{E(g["meta"].get("publico", mn))}</small></span>{ico("chev")}</a>' for g in gs)
        filas += ''.join(f'<a class="fila" href="/preguntas/{p["materia_slug"]}/"><span><b>{E(p["titulo"])}</b><small>{p["n"]} preguntas</small></span>{ico("chev")}</a>' for p in pr)
        bloques.append(f'<section><h2><a href="/guias/{ms}/">{E(mn)}</a></h2>{filas}</section>')
        escribe(f'guias/{ms}/index.html', pagina(f'Guías de {mn.lower()}', f'Guías en lenguaje claro sobre {mn.lower()}.',
            f'<div class="cont pag estrecha">{migas([("Inicio", "/"), ("Guías", "/guias/"), (mn, "")])}<h1>Guías: {E(mn)}</h1><p class="entrada">Explicaciones en lenguaje claro. {REVISION}.</p>{filas}{alerta()}</div>', 'Guías'))
    for p in PREG:
        if not any(ms == p['materia_slug'] for ms, _ in materias_g):
            bloques.append(f'<section><h2>{E(p["materia"])}</h2><a class="fila" href="/preguntas/{p["materia_slug"]}/"><span><b>{E(p["titulo"])}</b><small>{p["n"]} preguntas</small></span>{ico("chev")}</a></section>')
    if guias_base:
        bloques.append('<section><h2>Uso del sitio</h2>' + ''.join(f'<a class="fila" href="{g["url"]}"><span><b>{E(g["titulo"])}</b><small>{E(g["materia"])}</small></span>{ico("chev")}</a>' for g in guias_base) + '</section>')
    escribe('guias/index.html', pagina('Guías', 'Explicaciones paso a paso en lenguaje claro, por materia.',
        f'<div class="cont pag estrecha">{migas([("Inicio", "/"), ("Guías", "")])}<h1>Guías</h1><p class="entrada">Explicaciones paso a paso en lenguaje claro. Se irán sumando por materia.</p>{"".join(bloques)}{alerta()}</div>', 'Guías'))

# ------------------------------------------------ glosario
ruta_glo = os.path.join(CONT, 'glosario.json')
N_GLOSARIO = 0
if os.path.isfile(ruta_glo):
    terminos = json.load(open(ruta_glo, encoding='utf-8'))['terminos']
    N_GLOSARIO = len(terminos)

    def letra(t):
        c = unicodedata.normalize('NFD', t[0].upper())[0]
        return c

    terminos.sort(key=lambda t: slug(t['termino']))
    letras = []
    for t in terminos:
        if letra(t['termino']) not in letras:
            letras.append(letra(t['termino']))
    secs = []
    for L in letras:
        arts = ''
        for t in terminos:
            if letra(t['termino']) != L:
                continue
            ver = ''.join(f'<a href="{E(r.split("|")[0].strip())}">{E(r.split("|")[1].strip() if "|" in r else "Ver")}</a> ' for r in t.get('ver', []))
            arts += (f'<article class="tarjeta" id="{slug(t["termino"])}"><h3>{E(t["termino"])}</h3><p>{en_linea(t["definicion"])}</p>'
                     f'<small>{E(t.get("grupo", ""))}</small>{f"<p class=\"ver\">{ver}</p>" if ver else ""}</article>')
        secs.append(f'<section id="letra-{L}"><h2 class="letra">{L}</h2>{arts}</section>')
    abc = ''.join(f'<a href="#letra-{L}">{L}</a>' for L in letras)
    escribe('glosario/index.html', pagina('Glosario legal', 'Términos jurídicos explicados en lenguaje claro.',
        f'<div class="cont pag estrecha">{migas([("Inicio", "/"), ("Glosario", "")])}<h1>Glosario legal</h1><p class="entrada">Términos en lenguaje claro. Definiciones {REVISION.lower()}.</p><nav class="abc" aria-label="Índice alfabético">{abc}</nav>{"".join(secs)}{alerta()}</div>', 'Glosario'))

print(f'Editorial: {len(GUIAS)} guía(s), {sum(p["n"] for p in PREG)} pregunta(s) frecuente(s), {N_GLOSARIO} término(s) de glosario.')

# ------------------------------------------------ páginas sueltas (legales, contacto)
dir_pag = os.path.join(CONT, 'paginas')
N_PAG = 0
if os.path.isdir(dir_pag):
    for fn in sorted(os.listdir(dir_pag)):
        if not fn.endswith('.md'):
            continue
        meta, cuerpo = leer_md(os.path.join(dir_pag, fn))
        ruta = meta.get('ruta') or f'/{fn[:-3]}/'
        tit = meta.get('titulo') or fn[:-3]
        act = f'<p class="sec">Última actualización: {E(meta["actualizada"])}</p>' if meta.get('actualizada') else ''
        escribe(html_de(ruta), pagina(tit, meta.get('descripcion', tit),
            f'<div class="cont pag estrecha guia">{migas([("Inicio", "/"), (tit, "")])}<h1>{E(tit)}</h1>{act}\n{md_html(cuerpo)}</div>'))
        N_PAG += 1
    print(f'Páginas sueltas: {N_PAG}.')
