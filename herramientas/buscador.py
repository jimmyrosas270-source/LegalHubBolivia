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
    # fichas de la Biblioteca y de Jurisprudencia
    for ruta_s, docs in (('biblioteca', DOCS), ('jurisprudencia', DOCS_JUR)):
        for d in docs:
            nuevos.append({'n': 0, 'u': f'/{ruta_s}/{d["slug"]}/', 'r': d['titulo'], 'c': 'bib',
                           'k': f'{"Biblioteca" if ruta_s == "biblioteca" else "Jurisprudencia"} · {d.get("tipo") or "PDF"} · {d.get("materia", "")}'.rstrip(' ·'),
                           't': f'{d["titulo"]}. {d.get("tipo", "")} {d.get("numero", "")} {d.get("fecha", "")}. {d.get("descripcion", "")}'})
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
                      'Escribe una o varias palabras, o un número de artículo. Se busca en los temas de interés, las normas por artículos, las guías, las preguntas frecuentes, el glosario, las fichas de la Biblioteca, los autos supremos y el texto de todos los PDF.')
    extra = ('<option value="tem">Temas de interés</option><option value="gui">Guías</option><option value="pre">Preguntas frecuentes</option><option value="glo">Glosario</option>'
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

JS_BUSQUEDA = r"""var NOMBRE={tem:'Temas de interés',glo:'Glosario',gui:'Guías',pre:'Preguntas',aut:'Autos supremos',cpe:'Constitución',lgt:'Ley General del Trabajo',rgl:'Reglamento de la LGT',cpt:'Código Procesal del Trabajo',cmp:'Normas modificatorias',trn:'Normas transcritas',trn:'Normas transcritas',bib:'Fichas de la Biblioteca',pdf:'Texto de los PDF',jur:'Revistas de jurisprudencia'};
var ORDEN=['tem','glo','gui','pre','aut','cpe','lgt','rgl','cpt','cmp','trn','bib','pdf','jur'];
function rango(c){var i=ORDEN.indexOf(c);return i<0?ORDEN.length:i}
function pinta(lista,palabras){R.innerHTML='';lista.slice(0,60).forEach(function(a){var t=a.t,n=norm(t),p=0;for(var i=0;i<palabras.length;i++){var k=n.indexOf(palabras[i]);if(k>=0){p=k;break}}
var ini=Math.max(0,p-70),frag=(ini>0?'…':'')+t.slice(ini,ini+220)+(ini+220<t.length?'…':'');var h=esc(frag);
palabras.forEach(function(w){if(w.length<3)return;var nf=norm(frag),out='',pos=0,k;while((k=nf.indexOf(w,pos))>=0){out+=esc(frag.slice(pos,k))+'<mark>'+esc(frag.slice(k,k+w.length))+'</mark>';pos=k+w.length}if(out){h=out+esc(frag.slice(pos))}});
var e=d.createElement('a');e.className='res';e.href=a.u;e.innerHTML='<b>'+esc(a.r||('Artículo '+a.n))+'</b><small>'+esc(a.k)+'</small><span>'+h+'</span>';R.appendChild(e)})}
function resumen(lista){var cu={};lista.forEach(function(a){cu[a.c]=(cu[a.c]||0)+1});var ks=Object.keys(cu).sort(function(x,y){return rango(x)-rango(y)});if(ks.length<2)return;
var nav=d.createElement('nav');nav.className='por-tipo';nav.setAttribute('aria-label','Resultados por sección');nav.innerHTML='<b>Ver solo:</b>'+ks.map(function(c){return '<a href="/buscar/?q='+encodeURIComponent(q)+'&n='+c+'">'+esc(NOMBRE[c]||c)+' <small>('+cu[c]+')</small></a>'}).join('');R.parentNode.insertBefore(nav,R)}
function busca(datos){var s=norm(q.trim());if(!s){est.textContent='';return}if(fn){datos=datos.filter(function(a){return a.c===fn})}
var num=s.match(/^(?:art(?:iculo)?\.?\s*)?(\d{1,3})$/);var palabras=s.split(/\s+/).filter(Boolean);var lista;
if(num){lista=datos.filter(function(a){return a.n===+num[1]&&(!a.x||fn===a.c)});palabras=[]}else{lista=datos.filter(function(a){var n=norm(a.t+' '+(a.r||''));return palabras.every(function(w){return n.indexOf(w)>=0})})}
lista=lista.map(function(a,i){return [a,i]}).sort(function(x,y){return rango(x[0].c)-rango(y[0].c)||x[1]-y[1]}).map(function(x){return x[0]});
est.textContent=lista.length?(lista.length+(lista.length===1?' resultado':' resultados')+(lista.length>60?'; se muestran los primeros 60':'')):'Sin resultados. Prueba con otra palabra o con el número del artículo.';if(!fn)resumen(lista);pinta(lista,palabras)}
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
