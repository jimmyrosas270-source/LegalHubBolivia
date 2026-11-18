"""Cuestionarios de estudio (sección Estudiantes).

Lo ejecuta construir.py después de editorial.py (comparte pagina, escribe, migas, alerta, ico, E, OUT, CONT,
leer_md, en_linea, AVISOS...). Todo funciona en el navegador: no hay registro ni se envían datos;
solo se guarda en el propio navegador la mejor nota de cada cuestionario (localStorage).

Fuente: contenido/cuestionarios/<materia>/<tema>.md  ->  /estudiantes/cuestionarios/<materia>/<tema>/

Encabezado (entre líneas ---):
  titulo, materia (nombre visible), orden (número), resumen,
  mostrar (cuántas preguntas por intento; si el banco tiene más, se eligen al azar),
  repaso (lista '- ruta | texto': guías para repasar si la nota es baja).

Cada pregunta:
  ### V | Enunciado verdadero          (o  ### F | Enunciado falso)
  Explicación corta, en palabras propias (uno o más renglones).
  norma: /ruta/ | Norma, art. N        (una o varias; obligatoria)
  guia: /guias/... | Título de la guía (una o varias)

Las preguntas nuevas se añaden al final del archivo (el número de cada una es su orden).
No se usan contenidos marcados [VERIFICAR] ni cifras de años pasados.
Una materia nueva = una carpeta nueva con sus .md.
"""
DIR_CQ = os.path.join(CONT, 'cuestionarios')
CQ = []          # cuestionarios
CQ_ERRORES = []


def cq_enlace(linea):
    ruta, _, texto = linea.partition('|')
    return {'u': ruta.strip(), 't': texto.strip() or ruta.strip()}


def cq_leer(ruta, mat):
    meta, cuerpo = leer_md(ruta)
    nombre = os.path.basename(ruta)[:-3]
    preguntas = []
    for k, b in enumerate(re.split(r'^### ', cuerpo, flags=re.M)[1:], 1):
        cab, _, resto = b.partition('\n')
        m = re.match(r'\s*([VF])\s*\|\s*(.+)$', cab.strip())
        donde = f'Cuestionario {mat}/{nombre}, pregunta {k}'
        if not m:
            CQ_ERRORES.append(f'{donde}: el título debe empezar con «V |» o «F |».')
            continue
        expl, normas, guias = [], [], []
        for l in resto.split('\n'):
            s = l.strip()
            if s.lower().startswith('norma:'):
                normas.append(cq_enlace(s[6:]))
            elif s.lower().startswith(('guia:', 'guía:')):
                guias.append(cq_enlace(s.split(':', 1)[1]))
            elif s:
                expl.append(s)
        texto = ' '.join(expl)
        if 'VERIFICAR' in (m.group(2) + texto).upper():
            CQ_ERRORES.append(f'{donde}: contiene [VERIFICAR]; no se publica.')
            continue
        if not texto or not normas:
            CQ_ERRORES.append(f'{donde}: falta la explicación o la línea «norma:»; no se publica.')
            continue
        preguntas.append({'id': k, 'r': m.group(1) == 'V', 't': m.group(2).strip(), 'e': en_linea(texto),
                          'n': normas, 'g': guias})
    repaso = [cq_enlace(x) for x in meta.get('repaso', [])] if isinstance(meta.get('repaso'), list) else []
    try:
        mostrar = int(meta.get('mostrar', 10))
    except ValueError:
        mostrar = 10
    return {'materia_slug': mat, 'materia': meta.get('materia') or mat.capitalize(), 'slug': nombre,
            'titulo': meta.get('titulo') or nombre, 'resumen': meta.get('resumen', ''),
            'orden': float(meta.get('orden', 99) or 99), 'mostrar': max(1, min(mostrar, len(preguntas) or 1)),
            'repaso': repaso, 'preguntas': preguntas}


if os.path.isdir(DIR_CQ):
    for mat in sorted(os.listdir(DIR_CQ)):
        dm = os.path.join(DIR_CQ, mat)
        if not os.path.isdir(dm):
            continue
        for fn in sorted(os.listdir(dm)):
            if fn.endswith('.md') and not fn.startswith('_'):
                c = cq_leer(os.path.join(dm, fn), mat)
                if c['preguntas']:
                    CQ.append(c)
CQ.sort(key=lambda c: (c['materia_slug'], c['orden'], c['titulo']))
AVISOS.extend(CQ_ERRORES)


def cq_url(c):
    return f'/estudiantes/cuestionarios/{c["materia_slug"]}/{c["slug"]}/'


def cq_fila(c):
    return (f'<a class="fila" href="{cq_url(c)}" data-cq="{c["materia_slug"]}/{c["slug"]}"><span><b>{E(c["titulo"])}</b>'
            f'<small>{c["mostrar"]} preguntas por intento · <span class="cq-nota" data-cq-nota>Sin intentos</span></small></span>{ico("chev")}</a>')


CQ_HEAD = '<link rel="stylesheet" href="/assets/cuestionario.css">\n'
CQ_JS = '<script src="/assets/cuestionario.js" defer></script>\n'
CQ_BORRAR = ('<p class="cq-borrar"><button type="button" class="btn sec" data-cq-borrar>Borrar mis notas</button> '
             '<small>Las notas solo se guardan en este navegador.</small></p>')
CQ_TRAMOS = ('<details class="cq-tramos"><summary>Cómo se califica</summary><ul class="lista">'
             '<li><b>100:</b> ¡Felicidades, estás listo para litigar!</li><li><b>90 a 99:</b> muy bueno.</li>'
             '<li><b>70 a 89:</b> bueno.</li><li><b>51 a 69:</b> regular, con un repaso sugerido.</li>'
             '<li><b>0 a 50:</b> reprobado, con los temas que conviene repasar.</li></ul></details>')

materias_cq = {}
for c in CQ:
    materias_cq.setdefault((c['materia_slug'], c['materia']), []).append(c)

# ---- páginas de cada cuestionario
for c in CQ:
    datos = {'id': f'{c["materia_slug"]}/{c["slug"]}', 'titulo': c['titulo'], 'mostrar': c['mostrar'],
             'materia_url': f'/estudiantes/cuestionarios/{c["materia_slug"]}/', 'repaso': c['repaso'], 'preguntas': c['preguntas']}
    js = json.dumps(datos, ensure_ascii=False).replace('</', '<\\/')
    sin_js = ''.join(
        f'<li><p><b>{"Verdadero" if p["r"] else "Falso"}.</b> {E(p["t"])}</p><p>{p["e"]}</p><p class="sec">'
        + ' · '.join(f'<a href="{E(x["u"])}">{E(x["t"])}</a>' for x in p['n'] + p['g']) + '</p></li>'
        for p in c['preguntas'])
    repaso = ''.join(f'<a class="fila" href="{E(x["u"])}"><span><b>{E(x["t"])}</b><small>Guía</small></span>{ico("chev")}</a>' for x in c['repaso'])
    banco = len(c['preguntas'])
    detalle = f'{c["mostrar"]} preguntas de verdadero o falso' + (f', elegidas al azar de un banco de {banco}' if banco > c['mostrar'] else '') + ', en orden aleatorio'
    escribe(f'estudiantes/cuestionarios/{c["materia_slug"]}/{c["slug"]}/index.html', pagina(
        f'Cuestionario: {c["titulo"]}', f'Cuestionario de verdadero o falso sobre {c["titulo"].lower()} ({c["materia"].lower()}), con explicación y la norma de cada respuesta.',
        f'''<div class="cont pag estrecha cuest">{migas([("Inicio", "/"), ("Estudiantes", "/estudiantes/"), (f"Cuestionarios: {c['materia']}", f"/estudiantes/cuestionarios/{c['materia_slug']}/"), (c["titulo"], "")])}
<span class="chip">{E(c["materia"])} · Cuestionario</span><h1>{E(c["titulo"])}</h1>
<p class="entrada">{E(c["resumen"])}</p>
<p class="sec">{detalle}. Al responder verás si acertaste, por qué y en qué norma está. {REVISION}.</p>
<p class="sec cq-mejor" data-cq-mejor hidden></p>
<div id="cq" class="cq" data-cuestionario aria-live="polite"></div>
<noscript>{alerta("Para responder el cuestionario hace falta activar JavaScript. Debajo están las preguntas con sus respuestas y fuentes.")}<ol class="lista cq-sinjs">{sin_js}</ol></noscript>
<script type="application/json" id="cq-datos">{js}</script>
{CQ_TRAMOS}
<section><h2>Guías para repasar</h2>{repaso}</section>
{alerta("Material de estudio con información general. No sustituye asesoría profesional. Las preguntas salen de las normas y guías publicadas en el sitio y están pendientes de revisión legal humana.")}</div>''',
        'Estudiantes', extra_head=CQ_HEAD, scripts=CQ_JS))

# ---- página de cada materia
for (ms, mn), cs in materias_cq.items():
    escribe(f'estudiantes/cuestionarios/{ms}/index.html', pagina(
        f'Cuestionarios de estudio: {mn}', f'Cuestionarios de verdadero o falso sobre derecho {mn.lower()} boliviano.',
        f'''<div class="cont pag estrecha">{migas([("Inicio", "/"), ("Estudiantes", "/estudiantes/"), (f"Cuestionarios: {mn}", "")])}
<span class="chip">{E(mn)}</span><h1>Cuestionarios de estudio: {E(mn)}</h1>
<p class="entrada">Un cuestionario por tema, con preguntas de verdadero o falso. Cada respuesta trae una explicación corta, la norma y un enlace a la guía. {REVISION}.</p>
<section>{"".join(cq_fila(c) for c in cs)}</section>
{CQ_TRAMOS}{CQ_BORRAR}
{alerta("Material de estudio con información general. No sustituye asesoría profesional.")}</div>''',
        'Estudiantes', extra_head=CQ_HEAD, scripts=CQ_JS))

# ---- /estudiantes/cuestionarios/ y /estudiantes/
bloques_cq = ''.join(
    f'<section class="cq-materia"><h3><a href="/estudiantes/cuestionarios/{ms}/">{E(mn)}</a></h3>{"".join(cq_fila(c) for c in cs)}</section>'
    for (ms, mn), cs in materias_cq.items())
INTRO_CQ = ('<p>Pon a prueba lo que sabes con preguntas de verdadero o falso, organizadas por materia y por tema. '
            'Al responder cada una verás si acertaste, una explicación corta, la norma y el artículo, y un enlace para repasar. '
            'Al final recibes una nota sobre 100. No hace falta registrarse: todo funciona en tu navegador. Se irán sumando materias.</p>')
if CQ:
    escribe('estudiantes/cuestionarios/index.html', pagina(
        'Cuestionarios de estudio', 'Cuestionarios de verdadero o falso por materia, con explicación y norma en cada respuesta.',
        f'''<div class="cont pag estrecha">{migas([("Inicio", "/"), ("Estudiantes", "/estudiantes/"), ("Cuestionarios de estudio", "")])}
<h1>Cuestionarios de estudio</h1>{INTRO_CQ}{bloques_cq}{CQ_TRAMOS}{CQ_BORRAR}{alerta()}</div>''',
        'Estudiantes', extra_head=CQ_HEAD, scripts=CQ_JS))
    escribe('estudiantes/index.html', pagina(
        'Estudiantes', 'Cuestionarios de estudio por materia y, próximamente, rutas de aprendizaje y esquemas procesales.',
        f'''<div class="cont pag estrecha">{migas([("Inicio", "/"), ("Estudiantes", "")])}<h1>Estudiantes</h1>
<p class="entrada">Material para estudiar derecho boliviano. {REVISION}.</p>
<section><h2><a href="/estudiantes/cuestionarios/">Cuestionarios de estudio</a></h2>{INTRO_CQ}{bloques_cq}{CQ_BORRAR}</section>
<section class="tarjeta"><h2>Próximamente</h2><p>Rutas de aprendizaje, esquemas procesales y comparativas.</p></section>
{alerta()}</div>''',
        'Estudiantes', extra_head=CQ_HEAD, scripts=CQ_JS))

# ---- enlace «Pon a prueba lo que sabes» al pie de las guías que cada cuestionario usa para repasar
n_cq_guias = 0
por_guia = {}
for c in CQ:
    for x in c['repaso']:
        por_guia.setdefault(x['u'], []).append(c)
for ruta, cs in por_guia.items():
    p = os.path.join(OUT, html_de(ruta.split('#')[0]))
    if not ruta.startswith('/guias/') or not os.path.isfile(p):
        continue
    doc = open(p, encoding='utf-8').read()
    if 'data-cq-enlace' in doc:
        continue
    filas = ''.join(f'<a class="fila" href="{cq_url(c)}"><span><b>{E(c["titulo"])}</b><small>Cuestionario de verdadero o falso</small></span>{ico("chev")}</a>' for c in cs)
    bloque = f'<section class="tarjeta" data-cq-enlace><h2>Pon a prueba lo que sabes</h2>{filas}</section>\n'
    i = doc.rfind('<div class="alerta">')
    if i < 0:
        continue
    open(p, 'w', encoding='utf-8').write(doc[:i] + bloque + doc[i:])
    n_cq_guias += 1

for nombre in ('cuestionario.js', 'cuestionario.css'):
    shutil.copy(os.path.join(HERR, 'base', nombre), os.path.join(OUT, 'assets', nombre))
print(f'Cuestionarios: {len(CQ)} ({sum(len(c["preguntas"]) for c in CQ)} preguntas) en {len(materias_cq)} materia(s); enlazados desde {n_cq_guias} guía(s).')
