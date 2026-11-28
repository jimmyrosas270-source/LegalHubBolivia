# -*- coding: utf-8 -*-
"""Buscador ampliado (se ejecuta al final de construir.py con exec).

- buscar/indice.json: además de los artículos, guías, preguntas, glosario, fichas de la
  Biblioteca y autos supremos.
- buscar/pdf-1.json, pdf-2.json...: el texto de cada página de los PDF de la Biblioteca, con enlace
  al visor en esa página, repartido en partes de hasta TOPE_PARTE (3 MB). Se descargan juntas solo
  cuando alguien busca; la búsqueda es la misma que con un solo archivo.
- buscar/extensos-1.json...: revistas y documentos de más de PAGINAS_EXTENSO páginas (solo con filtro).
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
_ALIAS_COL = {f'/leyes/{c["materia"]}/{c["slug"]}/': c['alias'].split('|') for c in COLECCIONES if c.get('alias')}
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
    'ley-843-texto-original-1986.pdf': ['Ley 843 original', 'Ley de Reforma Tributaria'],
    'ley-1448.pdf': ['Ley 1448'],
    'ley-348.pdf': ['Ley de violencia contra la mujer', 'Ley integral contra la violencia'],
    'ley-1178.pdf': ['SAFCO', 'Ley SAFCO'],
    'ley-2341.pdf': ['Procedimiento administrativo'],
    'ley-483-notariado.pdf': ['Ley del notariado', 'Notariado'],
    'ley-1715.pdf': ['Ley 1715 texto original'],
    '/leyes/comercial/codigo-de-comercio/': ['CCo', 'CCom', 'Código mercantil', 'Decreto Ley 14379', 'DL 14379'],
    'compilacion-normativa-agraria-inra.pdf': ['Normativa agraria', 'Compilación agraria', 'Reforma agraria', 'INRA'],
    'ley-393-servicios-financieros.pdf': ['Ley de servicios financieros', 'Ley de bancos', 'Servicios financieros'],
    'ley-708-conciliacion-y-arbitraje.pdf': ['Ley de conciliación y arbitraje', 'Arbitraje', 'Conciliación y arbitraje'],
    'materia:Constitucional': ['Derecho constitucional', 'Constitución'],
    'materia:Laboral': ['Trabajo', 'Derecho del trabajo'],
    'materia:Familia': ['Familias', 'Derecho de familia', 'Niñez'],
    'materia:Tributario': ['Tributaria', 'Impuestos'],
    'materia:Comercial': ['Derecho mercantil', 'Mercantil'],
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
    # normas reunidas en una compilación (p. ej. «Normativa Agraria» del INRA): cada norma y cada artículo, con enlace al visor
    for arch_, comp_ in COMPILACIONES.items():
        d_ = next((x for x in DOCS if x['archivo'] == arch_), None)
        if not d_:
            continue
        base_ = f'/biblioteca/{d_["slug"]}/leer/#page='
        for n_ in comp_['normas']:
            nombre_ = f'{n_["tipo"]} {n_["numero"]}'.strip()
            alias = '|'.join(x for x in [nombre_, *n_['alias']] if x)
            nuevos.append({'n': 0, 'u': base_ + str(n_['pagina']), 'r': n_['titulo'], 'c': 'bib', 'a': alias, 'p': 2 if n_['clave'] == '1715' else 1,
                           'k': f'En la compilación «{d_["titulo"]}» · págs. {n_["pagina"]} a {n_["hasta"]} · {d_.get("materia", "")}',
                           't': f'{n_["titulo"]}. {n_["fecha"]}. {n_["descripcion"]} {alias.replace("|", ". ")}'})
            for a_ in n_['articulos']:
                nuevos.append({'n': a_['n'], 'x': 1, 'u': base_ + str(a_['pagina']), 'c': 'cpl', 'm': alias,
                               'r': f'{nombre_} · Artículo {a_["n"]}' + (f' ({a_["titulo"]})' if a_['titulo'] else ''),
                               'k': f'{n_["titulo"]} · {d_["titulo"]}, pág. {a_["pagina"]}',
                               't': a_['texto']})
    # normas por artículos (Constitución, LGT, Reglamento, Código Procesal del Trabajo)
    for m_, lista_ in DESTACADAS.items():
        for x in lista_:
            if not x.get('ruta'):
                continue
            alias = '|'.join([x.get('titulo', ''), x.get('sub', ''), *_ALIAS.get(x['ruta'], []), *_ALIAS_COL.get(x['ruta'], [])])
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
        nuevos.append({'n': 0, 'u': url_auto(a), 'r': f'Auto Supremo {a["numero"]}',
                       'k': f'Auto supremo · {a["materia"]} · {a["fecha"]} · {TITULO_REVISTA.get(a["revista"], "")}'.rstrip(' ·'), 'c': 'aut',
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
    # el texto se reparte en varios archivos pequeños (pdf-1.json, pdf-2.json...) que el buscador descarga juntos:
    # la búsqueda es la misma, pero ningún archivo pasa de TOPE_PARTE y el índice puede crecer sin límite práctico
    global HAY_EXTENSOS, PARTES_PDF, PARTES_EXT
    PARTES_PDF = _partes('pdf', paginas)
    # los documentos muy extensos van aparte: solo se descargan al filtrar por «Texto de los PDF» o «revistas»
    PARTES_EXT = _partes('extensos', extensos)
    HAY_EXTENSOS = bool(nombres_ext)
    if nombres_ext:
        print(f'Buscador: {len(nombres_ext)} documento(s) en buscar/extensos.json (revistas y documentos extensos): {", ".join(nombres_ext)}.')
    # página de búsqueda: texto y filtro
    p = os.path.join(OUT, 'buscar', 'index.html')
    doc = open(p, encoding='utf-8').read()
    doc = doc.replace('Escribe un número de artículo o una o varias palabras. Se busca en el texto literal de las normas cargadas.',
                      'Escribe una norma («Constitución», «código penal», «Ley 348»), un artículo con su norma («art 24 CPE», «artículo 138 del Código Civil», «CPP 233») o un tema («despido», «usucapión»). Mientras escribes aparecen sugerencias: con Enter se abre la que está marcada.')
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
# Tamaño máximo de cada parte del índice de texto de los PDF (en bytes, sin comprimir).
TOPE_PARTE = 3_000_000
PARTES_PDF = PARTES_EXT = 0


def _partes(nombre, registros):
    """Escribe buscar/<nombre>-1.json, -2.json... (cada uno <= TOPE_PARTE) y devuelve cuántas partes hay."""
    partes, actual, peso = [], [], 2
    for r in registros:
        t = len(json.dumps(r, ensure_ascii=False, separators=(',', ':')).encode('utf-8')) + 1
        if actual and peso + t > TOPE_PARTE:
            partes.append(actual)
            actual, peso = [], 2
        actual.append(r)
        peso += t
    if actual:
        partes.append(actual)
    for i, parte in enumerate(partes, 1):
        escribe(f'buscar/{nombre}-{i}.json', json.dumps(parte, ensure_ascii=False, separators=(',', ':')))
    return len(partes)

JS_BUSQUEDA = r"""var NOMBRE={ley:'Normas por artículos',mat:'Materias',tem:'Temas de interés',glo:'Glosario',gui:'Guías',pre:'Preguntas',aut:'Autos supremos',cpe:'Constitución',lgt:'Ley General del Trabajo',rgl:'Reglamento de la LGT',cpt:'Código Procesal del Trabajo',cmp:'Normas modificatorias',trn:'Normas transcritas',cco:'Código de Comercio',nar:'Leyes y códigos por artículos',cpl:'Artículos de compilaciones',bib:'Fichas de la Biblioteca',pdf:'Texto de los PDF',jur:'Revistas de jurisprudencia'};
var ORDEN=['ley','mat','cpe','lgt','rgl','cpt','cco','nar','cmp','trn','tem','gui','glo','pre','aut','bib','cpl','pdf','jur'];
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
var e=d.createElement('a');e.className='res'+(a._s>0?' norma':'');e.href=a.u;e.innerHTML='<b>'+esc(a.r||('Artículo '+a.n))+'</b><small>'+esc(a.k)+'</small>'+(a._s>0&&a.c!=='bib'?'':'<span>'+h+'</span>');var im=window.LHB&&(a._s>0||a.n||a.c==='pdf')?LHB.tapa(a.u):'';if(im){e.classList.add('con-tapa');e.insertAdjacentHTML('afterbegin','<img src="'+esc(im)+'" alt="" loading="lazy" width="44" height="57">')}R.appendChild(e)})}
function resumen(lista){var cu={};lista.forEach(function(a){cu[a.c]=(cu[a.c]||0)+1});var ks=Object.keys(cu).sort(function(x,y){return rango(x)-rango(y)});if(ks.length<2)return;
var nav=d.createElement('nav');nav.className='por-tipo';nav.setAttribute('aria-label','Resultados por sección');nav.innerHTML='<b>Ver solo:</b>'+ks.map(function(c){return '<a href="/buscar/?q='+encodeURIComponent(q)+'&n='+c+'">'+esc(NOMBRE[c]||c)+' <small>('+cu[c]+')</small></a>'}).join('');var otros=R.querySelector('.res-sec + .res.norma ~ .res-sec');if(otros){R.insertBefore(nav,otros)}else{R.parentNode.insertBefore(nav,R)}}
function busca(datos){var s=norm(q.trim());if(!s){est.textContent='';return}if(fn){datos=datos.filter(function(a){return a.c===fn})}
var HL=!!window.LHB,RF=HL?LHB.ref(q):null;if(!fn&&HL){var cont=d.createElement('div');cont.className='lhb-dest-cont';R.parentNode.insertBefore(cont,R);LHB.destacado(cont,q)}

var num=s.match(/^(?:art(?:iculo)?\.?\s*)?(\d{1,4})$/);var palabras=s.split(/\s+/).filter(Boolean);var lista;
var na=num?null:s.match(/^(.+?)\s+art(?:iculo|\.)?\s*(\d{1,4})(?:\s*(bis|ter|quater))?$/);if(na){var pw=na[1].split(/\s+/).filter(Boolean),nn_=+na[2],sf=na[3]||'',fr=' '+na[1].replace(/[^a-z0-9ñ]+/g,' ').trim()+' ';var hx=function(a){return ' '+norm((a.r||'')+' '+(a.a||'')+' '+(a.m||MALIAS[a.u.split('/').slice(0,4).join('/')+'/']||'')+' '+(a.r?'':(a.k||''))).replace(/[^a-z0-9ñ]+/g,' ')+' '};lista=datos.filter(function(a){if(a.n!==nn_)return false;var r=norm(a.r||'');if(sf?r.indexOf(sf)<0:/ (bis|ter|quater)\b/.test(r))return false;var h=hx(a);return pw.every(function(w){return h.indexOf(w)>=0})});var ex=lista.filter(function(a){return hx(a).indexOf(fr)>=0});if(ex.length)lista=ex;if(lista.length){palabras=[];num=null}else{lista=null;na=null}}
if(RF&&RF.tipo==='articulo'&&RF.existe){var tu=LHB.urlArt(RF.x,RF.clave);lista=datos.filter(function(a){return a.u===tu}).concat(datos.filter(function(a){return a.n===+RF.num&&a.u!==tu&&!a.x&&(RF.suf?norm(a.r||'').indexOf(RF.suf)>=0:!/ (bis|ter|quater)\b/.test(norm(a.r||'')))}));palabras=[];num=null}else if(na){}else if(num){var soloArt=/^art/.test(s);lista=datos.filter(function(a){return (a.n===+num[1]&&(!a.x||fn===a.c))||(!soloArt&&puntaje(a,s,[s])>0)});palabras=[]}else{lista=datos.filter(function(a){var n=norm(a.t+' '+(a.r||'')+' '+(a.a||''));return palabras.every(function(w){return n.indexOf(w)>=0})})}
var TIT={tem:1,gui:1,glo:1,pre:1};lista.forEach(function(a){a._s=puntaje(a,s,palabras.length?palabras:[s]);a._t=0;if(palabras.length){var tt=TIT[a.c]?norm(a.r||''):(/^\s*\(/.test(a.t||'')?norm(a.t.slice(0,a.t.indexOf(')')+1)):'');if(tt&&palabras.every(function(w){return tt.indexOf(w)>=0}))a._t=TIT[a.c]&&a.c!=='pre'?2:1}});
var ordena=function(l){return l.map(function(a,i){return [a,i]}).sort(function(x,y){return (y[0]._s>0)-(x[0]._s>0)||y[0]._s-x[0]._s||(y[0]._t||0)-(x[0]._t||0)||rango(x[0].c)-rango(y[0].c)||x[1]-y[1]}).map(function(x){return x[0]})};
lista=ordena(lista);var nn=0;lista.forEach(function(a){if(a._s>0){nn++;if(nn>6)a._s=0}});if(nn>6)lista=ordena(lista);
est.textContent=lista.length?(lista.length+(lista.length===1?' resultado':' resultados')+(lista.length>60?'; se muestran los primeros 60':'')):'Sin resultados. Prueba con otra palabra o con el número del artículo.';pinta(lista,palabras);if(!fn)resumen(lista)}
function junta(nom,k){var ps=[];for(var i=1;i<=k;i++){ps.push(fetch('/buscar/'+nom+'-'+i+'.json').then(function(r){return r.json()}).catch(function(){return []}))}return Promise.all(ps).then(function(xs){return [].concat.apply([],xs)})}
function aviso(){var rep=d.querySelector('[data-reporte]');if(!rep)return;var pag=R.closest('.pag');var u=rep.getAttribute('data-reporte').split('{pagina}').join(encodeURIComponent(location.href));
var a=d.createElement('aside');a.className='aviso-falta';a.setAttribute('aria-label','¿No encontraste lo que buscabas?');
a.innerHTML='<b>¿No encontraste la norma que buscabas?</b><p>Puede que todavía no esté en LegalHubBolivia. En el formulario de <b>Reportar un error</b> también puedes contarnos qué norma, artículo o tema falta y sugerir que lo agreguemos. Es anónimo.</p><a class="btn-rep" href="'+u.replace(/"/g,'&quot;')+'" target="_blank" rel="noopener">Sugerir una norma o reportar</a><p class="sec">Antes, prueba con la sigla o el número: «CPE», «CC», «Ley 348», «art 24 CPE».</p>';
var c=d.createElement('p');c.className='aviso-falta-corto';c.innerHTML='¿No encuentras una norma? <a href="'+u.replace(/"/g,'&quot;')+'" target="_blank" rel="noopener">Sugiere que la agreguemos</a> (más abajo te explicamos cómo).';
if(pag)pag.classList.add('con-lateral');est.parentNode.insertBefore(a,est.nextSibling);est.parentNode.insertBefore(c,est.nextSibling)}
if(q){aviso();est.textContent='Buscando…';var quiere=!fn||fn==='pdf'||fn==='jur';
Promise.all([fetch('/buscar/indice.json').then(function(r){return r.json()}),window.LHB?LHB.carga():null,quiere?junta('pdf',NPDF):Promise.resolve([]),fn==='pdf'||fn==='jur'?junta('extensos',NEXT):Promise.resolve([])]).then(function(x){busca(x[0].concat(x[2],x[3]));if(!fn){var nt=d.createElement('p');nt.className='sec';nt.innerHTML='La búsqueda general no incluye el texto de las revistas de jurisprudencia ni de los documentos muy extensos. Para buscar también ahí: <a href="/buscar/?q='+encodeURIComponent(q)+'&n=jur">texto de las revistas de jurisprudencia</a> o <a href="/buscar/?q='+encodeURIComponent(q)+'&n=pdf">texto de los PDF de la Biblioteca</a>.';R.parentNode.appendChild(nt)}}).catch(function(){est.textContent='No se pudo cargar el índice de búsqueda.'})}
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
    js = js.replace('function junta(', f'var NPDF={PARTES_PDF},NEXT={PARTES_EXT};function junta(', 1)
    malias = {f'/leyes/{c["materia"]}/{c["slug"]}/': c['alias'] for c in COLECCIONES if c.get('alias')}
    malias.update({'/leyes/constitucional/constitucion-politica-del-estado/': 'CPE|Constitución Política del Estado|Constitución',
                   '/leyes/laboral/ley-general-del-trabajo/': 'LGT|Ley General del Trabajo',
                   '/leyes/laboral/reglamento-de-la-ley-general-del-trabajo/': 'Reglamento de la Ley General del Trabajo|Decreto Supremo 224|DS 224',
                   '/leyes/laboral/codigo-procesal-del-trabajo/': 'CPT|Código Procesal del Trabajo'})
    js = js.replace('function junta(', 'var MALIAS=' + json.dumps(malias, ensure_ascii=False) + ';function junta(', 1)
    open(p, 'w', encoding='utf-8').write(t[:i] + js + t[j:])
    p = os.path.join(OUT, 'buscar', 'index.html')
    doc = open(p, encoding='utf-8').read()
    if '/assets/biblioteca.css' not in doc:
        doc = doc.replace('<link rel="stylesheet" href="/assets/estilos.css">', '<link rel="stylesheet" href="/assets/estilos.css">\n<link rel="stylesheet" href="/assets/biblioteca.css">', 1)
        open(p, 'w', encoding='utf-8').write(doc)


indice_ampliado()
parchar_sitio_js()
exec(open(os.path.join(HERR, 'rapido.py'), encoding='utf-8').read())
