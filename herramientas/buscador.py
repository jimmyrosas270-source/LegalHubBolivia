# -*- coding: utf-8 -*-
"""Buscador ampliado (se ejecuta al final de construir.py con exec).

- buscar/indice.json: además de los artículos, guías, preguntas, glosario, fichas de la
  Biblioteca y autos supremos.
- buscar/pdf.json: el texto de cada página de los PDF (Biblioteca y revistas), con enlace
  al visor en esa página. Se descarga solo cuando alguien busca.
"""
import glob as _glob
import subprocess as _sp


def _plano(md):
    md = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', md)
    md = re.sub(r'^(#+|>|!!|-|\d+\.)\s*', '', md, flags=re.M)
    md = md.replace('**', '').replace('[VERIFICAR]', '')
    return re.sub(r'\s+', ' ', md).strip()


def _frontmatter(t):
    meta, cuerpo = {}, t
    if t.startswith('---'):
        fin = t.index('\n---', 3)
        for l in t[3:fin].splitlines():
            if ':' in l and not l.startswith('-'):
                k, v = l.split(':', 1)
                meta[k.strip()] = v.strip()
        cuerpo = t[fin + 4:]
    return meta, cuerpo


# Siglas y nombres con que la gente busca cada norma (además del título, el tipo y el número del catálogo).
_ALIAS = {
    '/leyes/constitucional/constitucion-politica-del-estado/': ['CPE', 'Constitución', 'Constitución Política', 'Constitución de Bolivia', 'Carta Magna'],
    '/leyes/laboral/ley-general-del-trabajo/': ['LGT', 'Ley del Trabajo', 'Ley laboral'],
    '/leyes/laboral/reglamento-de-la-ley-general-del-trabajo/': ['Reglamento de la LGT', 'DS 224', 'Decreto Supremo 224'],
    '/leyes/laboral/codigo-procesal-del-trabajo/': ['CPT', 'Procesal del trabajo', 'Procesal laboral', 'Decreto Ley 16896'],
    'ley-439-codigo-procesal-civil.pdf': ['CPC', 'Procesal civil', 'Código de Procedimiento Civil'],
    'codigo-civil.pdf': ['CC', 'Código Civil boliviano'],
    'codigo-penal-2025.pdf': ['CP', 'Código Penal boliviano'],
    'ley-1970-codigo-de-procedimiento-penal-2025.pdf': ['CPP', 'Procesal penal', 'Procedimiento penal'],
    'ley-603-codigo-de-las-familias.pdf': ['Código de Familia', 'Código de las Familias', 'Familias', 'Proceso familiar'],
    'codigo-nina-nino-y-adolescente-ley-548.pdf': ['CNNA', 'Código del Niño', 'Código Niño Niña Adolescente'],
    'ley-254-codigo-procesal-constitucional.pdf': ['CPCo', 'Procesal constitucional'],
    'ley-843.pdf': ['Ley de impuestos', 'Reforma tributaria'],
    'ley-348.pdf': ['Ley de violencia contra la mujer', 'Ley integral contra la violencia'],
    'ley-1178.pdf': ['SAFCO', 'Ley SAFCO'],
    'ley-2341.pdf': ['Procedimiento administrativo'],
    'ley-483-notariado.pdf': ['Ley del notariado', 'Notariado'],
    'materia:Constitucional': ['Derecho constitucional', 'Constitución'],
    'materia:Laboral': ['Trabajo', 'Derecho del trabajo'],
    'materia:Familia': ['Familias', 'Derecho de familia', 'Niñez'],
    'materia:Tributario': ['Tributaria', 'Impuestos'],
    'materia:Penal': ['Delitos'],
    'materia:Procesal penal': ['Procedimiento penal'],
    'materia:Procesal civil': ['Procedimiento civil'],
}


def _nombre_norma(d):
    """El nombre de la norma, si la descripción del catálogo empieza con él («Ley del Notariado Plurinacional.»)."""
    desc = (d.get('descripcion') or '').strip()
    m = re.match(r'((?:Ley|Código|Decreto|Reglamento|Resolución|Protocolo)[^.:;]{3,140})[.:]', desc)
    return m.group(1).strip() if m else ''


def indice_ampliado():
    p = os.path.join(OUT, 'buscar', 'indice.json')
    if not os.path.isfile(p):
        AVISOS.append('No se encontró buscar/indice.json: no se amplió el buscador.')
        return
    idx = json.load(open(p, encoding='utf-8'))
    nuevos = []
    # temas de interés
    for t in globals().get('TEMAS', []):
        nuevos.append({'n': 0, 'u': f'/temas/{t["slug"]}/', 'r': 'Tema: ' + t['titulo'], 'k': 'Tema de interés · ' + t['materia'], 'c': 'tem',
                       't': f'{t["titulo"]}. {t["resumen"]} ' + ' '.join(k['t'] for k in t['tarjetas']) + ' ' + _plano(t['cuerpo'])})
    # guías
    for f in sorted(_glob.glob(os.path.join(RAIZ, 'contenido', 'guias', '*', '*.md'))):
        meta, cuerpo = _frontmatter(open(f, encoding='utf-8').read())
        mat = os.path.basename(os.path.dirname(f))
        tit = meta.get('titulo', os.path.basename(f)[:-3])
        nuevos.append({'n': 0, 'u': f'/guias/{mat}/{os.path.basename(f)[:-3]}/', 'r': 'Guía: ' + tit,
                       'k': 'Guía · ' + meta.get('materia', mat.capitalize()), 'c': 'gui',
                       't': f'{tit}. {meta.get("resumen", "")} {_plano(cuerpo)}'})
    # preguntas frecuentes
    for f in sorted(_glob.glob(os.path.join(RAIZ, 'contenido', 'preguntas', '*.md'))):
        mat = os.path.basename(f)[:-3]
        partes = re.split(r'^### +', open(f, encoding='utf-8').read(), flags=re.M)[1:]
        for k, bloque in enumerate(partes, 1):
            preg, _, resp = bloque.partition('\n')
            nuevos.append({'n': 0, 'u': f'/preguntas/{mat}/#p{k}', 'r': preg.strip(), 'k': 'Pregunta frecuente · ' + mat.capitalize(),
                           'c': 'pre', 't': preg.strip() + ' ' + _plano(resp)})
    # glosario
    g = json.load(open(os.path.join(RAIZ, 'contenido', 'glosario.json'), encoding='utf-8'))
    for x in g.get('terminos', []):
        nuevos.append({'n': 0, 'u': f'/glosario/#{slug(x["termino"])}', 'r': x['termino'], 'k': 'Glosario', 'c': 'glo',
                       't': f'{x["termino"]}: {_plano(x["definicion"])}'})
    # fichas de la Biblioteca y de Jurisprudencia: llevan el nombre de la norma, sus siglas ('a') y su prioridad ('p')
    # para que, si alguien escribe «procesal civil», «constitución» o «ley 348», salga primero la norma como tal
    prio = {}
    for m_, lista_ in DESTACADAS.items():
        for x in lista_:
            clave_ = x.get('archivo') or x.get('ruta')
            prio[clave_] = 2 if x.get('inicio') else 1
    for ruta_s, docs in (('biblioteca', DOCS), ('jurisprudencia', DOCS_JUR)):
        for d in docs:
            nombre = _nombre_norma(d)
            alias = '|'.join(x for x in [nombre, f'{d.get("tipo", "")} {d.get("numero", "")}'.strip(), *_ALIAS.get(d['archivo'], [])] if x)
            nuevos.append({'n': 0, 'u': f'/{ruta_s}/{d["slug"]}/', 'r': d['titulo'], 'c': 'bib', 'a': alias, 'p': prio.get(d['archivo'], 0),
                           'k': f'{"Biblioteca" if ruta_s == "biblioteca" else "Jurisprudencia"} · {d.get("tipo") or "PDF"} · {d.get("materia", "")}'.rstrip(' ·'),
                           't': f'{d["titulo"]}. {d.get("tipo", "")} {d.get("numero", "")}, {d.get("fecha", "")}. {d.get("descripcion", "")} {alias.replace("|", ". ")}'})
    # normas por artículos (Constitución, LGT, Reglamento, Código Procesal del Trabajo)
    for m_, lista_ in DESTACADAS.items():
        for x in lista_:
            if not x.get('ruta'):
                continue
            alias = '|'.join([x.get('titulo', ''), x.get('sub', ''), *_ALIAS.get(x['ruta'], [])])
            nuevos.append({'n': 0, 'u': x['ruta'], 'r': x.get('titulo', ''), 'c': 'ley', 'a': alias, 'p': prio.get(x['ruta'], 0) + 1,
                           'k': f'Norma por artículos · {m_} · {x.get("detalle", "")}'.rstrip(' ·'),
                           't': f'{x.get("titulo", "")}. {alias.replace("|", ". ")}'})
    # materias
    for m_ in ORDEN_MATERIAS:
        n_docs = sum(1 for d in DOCS if d['materia'] == m_)
        con_arts = os.path.isfile(os.path.join(OUT, 'leyes', slug(m_), 'index.html'))
        if not n_docs and not con_arts:
            continue
        alias = '|'.join([m_, f'derecho {m_.lower()}', *_ALIAS.get('materia:' + m_, [])])
        nuevos.append({'n': 0, 'u': f'/leyes/{slug(m_)}/' if con_arts else f'/biblioteca/{slug(m_)}/', 'r': f'{m_}: todas las normas de la materia',
                       'c': 'mat', 'a': alias, 'p': 0, 'k': f'Materia · {plural(n_docs, "documento", "documentos")} en la Biblioteca' + (' · normas por artículos' if con_arts else ''),
                       't': alias.replace('|', '. ')})
    # autos supremos
    for a in AUTOS:
        nuevos.append({'n': 0, 'u': f'/jurisprudencia/{REVISTA_AUTOS}/leer/#page={a["pagina"]}', 'r': f'Auto Supremo {a["numero"]}',
                       'k': f'Auto supremo · {a["materia"]} · {a["fecha"]}', 'c': 'aut',
                       't': f'Auto Supremo {a["numero"]} {a["fecha"]} {a["sala"]}. {a["tema"]}'})
    json.dump(idx + nuevos, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    # texto de los PDF, página por página
    paginas, extensos, nombres_ext = [], [], []
    for ruta_s, carpeta, docs in (('biblioteca', 'biblioteca', DOCS), ('jurisprudencia', 'jurisprudencia', DOCS_JUR)):
        for d in docs:
            ruta = d.get('ruta_pdf') or next(iter(_glob.glob(os.path.join(RAIZ, carpeta, 'pdf', '**', d['archivo']), recursive=True)), None)
            if not ruta:
                continue
            try:
                txt = _sp.run(['pdftotext', '-enc', 'UTF-8', ruta, '-'], capture_output=True, text=True, timeout=120).stdout
            except Exception as e:
                AVISOS.append(f'Buscador: no se pudo leer el texto de «{d["archivo"]}»: {e}')
                continue
            hojas = txt.split('\f')
            destino = paginas
            if len(hojas) > PAGINAS_EXTENSO or ruta_s == 'jurisprudencia':  # revistas: solo con el filtro de jurisprudencia o de PDF
                destino = extensos
                nombres_ext.append(d['titulo'])
            for n, pg in enumerate(hojas, 1):
                pg = re.sub(r'\s+', ' ', pg).strip()
                if len(pg) < 20:
                    continue
                destino.append({'n': 0, 'u': f'/{ruta_s}/{d["slug"]}/leer/#page={n}', 'r': f'{d["titulo"]} · pág. {n}',
                                'k': 'Texto del PDF · ' + ('Biblioteca' if ruta_s == 'biblioteca' else 'Jurisprudencia'),
                                'c': 'pdf' if ruta_s == 'biblioteca' else 'jur', 't': pg})
    escribe('buscar/pdf.json', json.dumps(paginas, ensure_ascii=False, separators=(',', ':')))
    # los documentos muy extensos van aparte: solo se descargan al filtrar por «Texto de los PDF» o «revistas»
    escribe('buscar/extensos.json', json.dumps(extensos, ensure_ascii=False, separators=(',', ':')))
    global HAY_EXTENSOS
    HAY_EXTENSOS = bool(nombres_ext)
    if nombres_ext:
        print(f'Buscador: {len(nombres_ext)} documento(s) en buscar/extensos.json (revistas y documentos extensos): {", ".join(nombres_ext)}.')
    # página de búsqueda: texto y filtro
    p = os.path.join(OUT, 'buscar', 'index.html')
    doc = open(p, encoding='utf-8').read()
    doc = doc.replace('Escribe un número de artículo o una o varias palabras. Se busca en el texto literal de las normas cargadas.',
                      'Escribe el nombre de una norma (por ejemplo «procesal civil», «Constitución» o «Ley 348»), un tema o un número de artículo. Primero aparece la norma; después, los artículos y lo demás.')
    extra = ('<option value="ley">Normas por artículos</option><option value="mat">Materias</option><option value="tem">Temas de interés</option><option value="gui">Guías</option><option value="pre">Preguntas frecuentes</option><option value="glo">Glosario</option>'
             '<option value="bib">Fichas de la Biblioteca y Jurisprudencia</option><option value="aut">Autos supremos</option>'
             '<option value="pdf">Texto de los PDF de la Biblioteca</option><option value="jur">Texto de las revistas de jurisprudencia</option>')
    if 'value="gui"' not in doc:
        doc = doc.replace('</select>', extra + '</select>', 1)
        doc = doc.replace('<option value="">Todas las normas</option>', '<option value="">Todo el sitio</option>', 1)
        doc = doc.replace('<span>Norma</span>', '<span>Buscar en</span>', 1)
    open(p, 'w', encoding='utf-8').write(doc)
    print(f'Buscador: {len(idx)} artículos + {len(nuevos)} guías, preguntas, términos, fichas y autos; {len(paginas)} páginas de PDF.')


# Documentos con más páginas que esto no entran en la búsqueda general (pesarían demasiado al buscar desde el celular):
# se buscan con el filtro «Texto de los PDF» o «Texto de las revistas», y dentro de su propio visor.
PAGINAS_EXTENSO = 500
HAY_EXTENSOS = False

JS_BUSQUEDA = r"""var NOMBRE={ley:'Normas por artículos',mat:'Materias',tem:'Temas de interés',glo:'Glosario',gui:'Guías',pre:'Preguntas',aut:'Autos supremos',cpe:'Constitución',lgt:'Ley General del Trabajo',rgl:'Reglamento de la LGT',cpt:'Código Procesal del Trabajo',cmp:'Normas modificatorias',trn:'Normas transcritas',bib:'Fichas de la Biblioteca',pdf:'Texto de los PDF',jur:'Revistas de jurisprudencia'};
var ORDEN=['ley','mat','cpe','lgt','rgl','cpt','cmp','trn','tem','gui','glo','pre','aut','bib','pdf','jur'];
function rango(c){var i=ORDEN.indexOf(c);return i<0?ORDEN.length:i}
function limpio(t){return ' '+norm(t||'').replace(/[^a-z0-9ñ]+/g,' ').trim()+' '}
function puntaje(a,s,ws){if(a.c!=='bib'&&a.c!=='ley'&&a.c!=='mat')return 0;var al=(a.a||'').split('|').map(function(x){return limpio(x).trim()}).filter(Boolean),tit=limpio(a.r).trim(),tn=limpio((a.r||'')+' '+(a.a||'').replace(/\|/g,' ')),q=limpio(s).trim(),p;
if(!q)return 0;var pre=function(w){return w.length>=4?tn.indexOf(' '+w)>=0:tn.indexOf(' '+w+' ')>=0};
if(tit===q||al.indexOf(q)>=0)p=6;else if(tn.indexOf(' '+q+' ')>=0)p=4;else if(pre(q))p=3;else if(ws.every(function(w){return pre(limpio(w).trim())}))p=2;else return 0;
if(a.c==='mat')return Math.min(p,4)+0.5;return p+(a.p||0)}
function pinta(lista,palabras){R.innerHTML='';var vistos=false,otros=false;lista.slice(0,60).forEach(function(a){
if(a._s>0&&!vistos){vistos=true;var h2=d.createElement('h2');h2.className='res-sec';h2.textContent='Normas';R.appendChild(h2)}
if(!(a._s>0)&&vistos&&!otros){otros=true;var h3=d.createElement('h2');h3.className='res-sec';h3.textContent='Artículos y otros resultados';R.appendChild(h3)}
var t=a.t,n=norm(t),p=0;for(var i=0;i<palabras.length;i++){var k=n.indexOf(palabras[i]);if(k>=0){p=k;break}}
var ini=Math.max(0,p-70),frag=(ini>0?'…':'')+t.slice(ini,ini+220)+(ini+220<t.length?'…':'');var h=esc(frag);
palabras.forEach(function(w){if(w.length<3)return;var nf=norm(frag),out='',pos=0,k;while((k=nf.indexOf(w,pos))>=0){out+=esc(frag.slice(pos,k))+'<mark>'+esc(frag.slice(k,k+w.length))+'</mark>';pos=k+w.length}if(out){h=out+esc(frag.slice(pos))}});
var e=d.createElement('a');e.className='res'+(a._s>0?' norma':'');e.href=a.u;e.innerHTML='<b>'+esc(a.r||('Artículo '+a.n))+'</b><small>'+esc(a.k)+'</small>'+(a._s>0&&a.c!=='bib'?'':'<span>'+h+'</span>');R.appendChild(e)})}
function resumen(lista){var cu={};lista.forEach(function(a){cu[a.c]=(cu[a.c]||0)+1});var ks=Object.keys(cu).sort(function(x,y){return rango(x)-rango(y)});if(ks.length<2)return;
var nav=d.createElement('nav');nav.className='por-tipo';nav.setAttribute('aria-label','Resultados por sección');nav.innerHTML='<b>Ver solo:</b>'+ks.map(function(c){return '<a href="/buscar/?q='+encodeURIComponent(q)+'&n='+c+'">'+esc(NOMBRE[c]||c)+' <small>('+cu[c]+')</small></a>'}).join('');var otros=R.querySelector('.res-sec + .res.norma ~ .res-sec');if(otros){R.insertBefore(nav,otros)}else{R.parentNode.insertBefore(nav,R)}}
function busca(datos){var s=norm(q.trim());if(!s){est.textContent='';return}if(fn){datos=datos.filter(function(a){return a.c===fn})}
var num=s.match(/^(?:art(?:iculo)?\.?\s*)?(\d{1,4})$/);var palabras=s.split(/\s+/).filter(Boolean);var lista;
if(num){var soloArt=/^art/.test(s);lista=datos.filter(function(a){return (a.n===+num[1]&&(!a.x||fn===a.c))||(!soloArt&&puntaje(a,s,[s])>0)});palabras=[]}else{lista=datos.filter(function(a){var n=norm(a.t+' '+(a.r||'')+' '+(a.a||''));return palabras.every(function(w){return n.indexOf(w)>=0})})}
lista.forEach(function(a){a._s=puntaje(a,s,palabras.length?palabras:[s])});
var ordena=function(l){return l.map(function(a,i){return [a,i]}).sort(function(x,y){return (y[0]._s>0)-(x[0]._s>0)||y[0]._s-x[0]._s||rango(x[0].c)-rango(y[0].c)||x[1]-y[1]}).map(function(x){return x[0]})};
lista=ordena(lista);var nn=0;lista.forEach(function(a){if(a._s>0){nn++;if(nn>6)a._s=0}});if(nn>6)lista=ordena(lista);
est.textContent=lista.length?(lista.length+(lista.length===1?' resultado':' resultados')+(lista.length>60?'; se muestran los primeros 60':'')):'Sin resultados. Prueba con otra palabra o con el número del artículo.';pinta(lista,palabras);if(!fn)resumen(lista)}
if(q){est.textContent='Buscando…';var quiere=!fn||fn==='pdf'||fn==='jur';
Promise.all([fetch('/buscar/indice.json').then(function(r){return r.json()}),quiere?fetch('/buscar/pdf.json').then(function(r){return r.json()}).catch(function(){return []}):Promise.resolve([]),fn==='pdf'||fn==='jur'?fetch('/buscar/extensos.json').then(function(r){return r.json()}).catch(function(){return []}):Promise.resolve([])]).then(function(x){busca(x[0].concat(x[1],x[2]));if(!fn){var nt=d.createElement('p');nt.className='sec';nt.innerHTML='La búsqueda general no incluye el texto de las revistas de jurisprudencia ni de los documentos muy extensos. Para buscar también ahí: <a href="/buscar/?q='+encodeURIComponent(q)+'&n=jur">texto de las revistas de jurisprudencia</a> o <a href="/buscar/?q='+encodeURIComponent(q)+'&n=pdf">texto de los PDF de la Biblioteca</a>.';R.parentNode.appendChild(nt)}}).catch(function(){est.textContent='No se pudo cargar el índice de búsqueda.'})}
"""


def parchar_sitio_js():
    """Sustituye la búsqueda de assets/sitio.js (viene de la base) por la búsqueda ampliada."""
    p = os.path.join(OUT, 'assets', 'sitio.js')
    t = open(p, encoding='utf-8').read()
    if 'var NOMBRE=' in t:
        return
    i = t.find('function pinta(lista,palabras)')
    j = t.rfind('}\n})();')
    if i < 0 or j < i:
        AVISOS.append('No se pudo ampliar la búsqueda en assets/sitio.js (cambió la base).')
        return
    js = JS_BUSQUEDA.replace('if(!fn){var nt', 'if(!fn&&' + ('true' if HAY_EXTENSOS else 'false') + '){var nt')
    open(p, 'w', encoding='utf-8').write(t[:i] + js + t[j:])
    p = os.path.join(OUT, 'buscar', 'index.html')
    doc = open(p, encoding='utf-8').read()
    if '/assets/biblioteca.css' not in doc:
        doc = doc.replace('<link rel="stylesheet" href="/assets/estilos.css">', '<link rel="stylesheet" href="/assets/estilos.css">\n<link rel="stylesheet" href="/assets/biblioteca.css">', 1)
        open(p, 'w', encoding='utf-8').write(doc)


indice_ampliado()
parchar_sitio_js()
