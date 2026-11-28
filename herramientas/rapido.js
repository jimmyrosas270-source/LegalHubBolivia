/* LegalHubBolivia · buscador rápido (sugerencias al escribir). Lo instala herramientas/rapido.py al principio de assets/sitio.js. */
(function(){
'use strict';
var d=document,W=window,DATOS=null,PROM=null,PREV={};
var STOP={de:1,del:1,la:1,el:1,los:1,las:1,y:1,e:1,en:1,a:1,al:1,un:1,una:1,que:1,sobre:1,segun:1,por:1,para:1,con:1,lo:1};
var ART={art:1,arts:1,articulo:1,articulos:1,nro:1,numero:1,num:1,n:1,no:1};
var SUBDIV={paragrafo:1,parrafo:1,par:1,inciso:1,inc:1,numeral:1,literal:1};
var NOMBRE_N={ley:1,ds:1,dl:1,decreto:1,supremo:1,rm:1,resolucion:1,ministerial:1,sc:1,scp:1,as:1,auto:1};
var SUF={bis:1,ter:1,quater:1,quinquies:1,sexies:1};
function norm(s){return String(s||'').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'').replace(/(\d)\.(\d)/g,'$1$2').replace(/\./g,'').replace(/([a-z])(\d)/g,'$1 $2').replace(/(\d)([a-z])/g,'$1 $2').replace(/[^a-z0-9]+/g,' ').trim()}
function esc(s){return String(s||'').replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function palabras(s){return norm(s).split(' ').filter(function(w){return w&&!STOP[w]})}
function prepara(D){
 D.col.forEach(function(c){c._a=c.a.map(function(x){return palabras(x).join(' ')}).filter(Boolean);c._k={};c.A.split(',').forEach(function(k){c._k[k]=1});c._n=c.A.split(',');c._t='col'});
 D.doc.forEach(function(x){x._a=x.a.map(function(y){return palabras(y).join(' ')}).filter(Boolean);x._t='doc'});
 D.mat.forEach(function(x){x._a=[x.r].concat(x.a).map(function(y){return palabras(y).join(' ')}).filter(Boolean);x._t='mat'});
 D.arts=[];D.col.forEach(function(c){Object.keys(c.T).forEach(function(k){D.arts.push({c:c,k:k,r:c.T[k],n:' '+norm(c.T[k])+' '})})});
 ['tem','gui','glo','pre'].forEach(function(s){D[s].forEach(function(x){x._r=' '+norm(x.r)+' ';x._d=' '+norm(x.d||'')+' ';x._t=s})});
 return D}
function carga(){if(!PROM){PROM=fetch('/buscar/rapido.json').then(function(r){return r.json()}).then(function(D){DATOS=prepara(D);return DATOS}).catch(function(){PROM=null;return null})}return PROM}
/* ---- normas: puntaje de un texto contra los alias de una norma ---- */
function prefijos(ws,txt){return ws.every(function(w){return w.length>=2&&(' '+txt+' ').indexOf(' '+w)>=0})}
function puntNorma(x,q,ws){var best=0;for(var i=0;i<x._a.length;i++){var al=x._a[i],p=0;
 if(al===q)p=100;else if(q.length>=3&&al.indexOf(q)===0)p=82;else if(ws.length&&ws.join('').length>=3&&prefijos(ws,al))p=62;
 if(p>best)best=p}return best}
function normas(ws,lista){var q=ws.join(' ');if(!q)return [];var out=[];lista.forEach(function(x){var p=puntNorma(x,q,ws);if(p)out.push({x:x,p:p})});
 out.sort(function(a,b){return b.p-a.p||((a.x.o==null?50:a.x.o)-(b.x.o==null?50:b.x.o))});return out}
/* ---- referencia a un artículo: «art 24 cpe», «artículo 22 del código civil», «cpe 24», «24», «art 5 bis cp» ---- */
function ref(texto){if(!DATOS)return null;var t=norm(texto).split(' ').filter(Boolean);if(!t.length)return null;
 var todo=palabras(texto),nm=normas(todo,DATOS.col.concat(DATOS.doc));
 if(nm.length&&nm[0].p>=82&&!/^\d+$/.test(todo[0]||'')){var hayArt=t.some(function(w){return ART[w]});if(!hayArt)return {tipo:'norma',x:nm[0].x,p:nm[0].p}}
 var cands=[];
 for(var i=0;i<t.length;i++){if(!/^\d{1,4}$/.test(t[i]))continue;
  var j=i-1;while(j>=0&&STOP[t[j]])j--;var marcado=j>=0&&!!ART[t[j]];
  if(!marcado&&j>=0&&NOMBRE_N[t[j]])continue;
  var suf=(i+1<t.length&&SUF[t[i+1]])?t[i+1]:'';
  var resto=[];for(var k=0;k<t.length;k++){if(k===i||(suf&&k===i+1)||ART[t[k]]||STOP[t[k]])continue;
   if(SUBDIV[t[k]]){k++;continue}resto.push(t[k])}
  var num=t[i].replace(/^0+(?=\d)/,''),clave=num+(suf?'-'+suf:'');
  if(!resto.length){cands.push({tipo:'numero',num:num,suf:suf,clave:clave,cols:DATOS.col.filter(function(c){return c._k[clave]}),marcado:marcado,p:marcado?50:40});continue}
  var ms=normas(resto,DATOS.col);if(!ms.length||ms[0].p<62)continue;
  var top=ms.filter(function(m){return m.p===ms[0].p});
  var con=top.filter(function(m){return m.x._k[clave]});var elegida=(con[0]||top[0]).x;
  cands.push({tipo:'articulo',num:num,suf:suf,clave:clave,x:elegida,existe:!!elegida._k[clave],otras:top.filter(function(m){return m.x!==elegida&&m.x._k[clave]}).map(function(m){return m.x}),marcado:marcado,p:ms[0].p+(marcado?10:0)})}
 if(!cands.length)return nm.length&&nm[0].p>=62?{tipo:'norma',x:nm[0].x,p:nm[0].p}:null;
 cands.sort(function(a,b){return (b.tipo==='articulo')-(a.tipo==='articulo')||b.p-a.p});return cands[0]}
function urlArt(c,k){return c.u+'articulo-'+k+'/'}
function etiqArt(k){return 'Artículo '+k.replace('-',' ')}
function rango(c){return 'artículos '+c._n[0].replace('-',' ')+' a '+c._n[c._n.length-1].replace('-',' ')}
/* ---- vista previa del texto de un artículo (se lee de su propia página) ---- */
function previa(u){if(!PREV[u]){PREV[u]=fetch(u).then(function(r){if(!r.ok)throw 0;return r.text()}).then(function(h){var x=new DOMParser().parseFromString(h,'text/html'),a=x.querySelector('article.legal');if(!a)return null;
 var ps=[].slice.call(a.querySelectorAll('p')).filter(function(p){return !p.closest('footer')&&!p.closest('.entre')&&!p.closest('.nota')}).map(function(p){return p.textContent.trim()}).filter(Boolean);
 var cap=x.querySelector('.ruta b');return {cap:cap?cap.textContent.trim():'',txt:ps.join(' '),ps:ps}}).catch(function(){return null})}return PREV[u]}
/* ---- sugerencias ---- */
function cuenta(ws,campo){return ws.every(function(w){return w.length<3?campo.indexOf(' '+w+' ')>=0:campo.indexOf(' '+w)>=0})}
function sugerencias(texto){var D=DATOS,out={secs:[],fuerte:false},r=ref(texto),ws=palabras(texto);
 function sec(t,items){if(items.length)out.secs.push({t:t,items:items})}
 if(r&&r.tipo==='articulo'){var c=r.x,it=[];
  if(r.existe){it.push({u:urlArt(c,r.clave),t:etiqArt(r.clave)+(c.T[r.clave]?' · '+c.T[r.clave]:''),s:c.r,i:c.i,prev:urlArt(c,r.clave)});out.fuerte=true}
  else it.push({u:c.u+'#indice',t:'No hay '+etiqArt(r.clave).toLowerCase()+' en '+c.r,s:'Esta norma por artículos tiene '+rango(c)+'. Puede estar derogado o tener otro número. Abrir el índice',i:c.i});
  r.otras.forEach(function(o){it.push({u:urlArt(o,r.clave),t:etiqArt(r.clave)+(o.T[r.clave]?' · '+o.T[r.clave]:''),s:o.r,i:o.i})});
  sec('Ir al artículo',it);sec('La norma',[{u:c.u,t:c.r,s:'Índice y todos los artículos'+(c.s?' · '+c.s:''),i:c.i}])}
 else if(r&&r.tipo==='numero'){sec(etiqArt(r.clave)+' en…',r.cols.slice(0,8).map(function(c,ix){return {u:urlArt(c,r.clave),t:c.r,s:etiqArt(r.clave)+(c.T[r.clave]?' · '+c.T[r.clave]:''),i:c.i,prev:ix===0?urlArt(c,r.clave):''}}));
  out.pista='Escribe también la norma para ir directo: «art '+r.clave.replace('-',' ')+' CPE», «art '+r.clave.replace('-',' ')+' código civil»…'}
 if(!(r&&r.tipo==='articulo')){var nm=normas(ws,D.col.concat(D.doc)).slice(0,5);
  var mt=normas(ws,D.mat).filter(function(m){return m.p>=82}).slice(0,1);
  var it2=nm.map(function(m){var x=m.x;return x._t==='col'?{u:x.u,t:x.r,s:'Por artículos'+(x.s?' · '+x.s:''),i:x.i,p:m.p}:{u:x.l,t:x.r,s:x.s+' · leer el PDF',i:x.i,p:m.p,u2:x.u}});
  mt.forEach(function(m){it2.push({u:m.x.u,t:m.x.r+': todas las normas de la materia',s:'Materia',p:m.p,ico:'mat'})});
  if(it2.length&&it2[0].p>=82&&!(r&&r.tipo==='numero'))out.fuerte=true;
  sec('Normas',it2)}
 if(ws.length&&ws.join('').length>=3&&!(r&&r.tipo==='articulo')){
  var ar=[];for(var i=0;i<D.arts.length&&ar.length<40;i++){var a=D.arts[i];if(cuenta(ws,a.n))ar.push(a)}
  var fr=' '+ws.join(' ')+' ';ar.sort(function(a,b){return (b.n.indexOf(fr)>=0)-(a.n.indexOf(fr)>=0)||(a.c.o-b.c.o)});
  sec('Artículos cuyo título coincide',ar.slice(0,6).map(function(a){return {u:urlArt(a.c,a.k),t:a.r,s:a.c.r+' · '+etiqArt(a.k),i:a.c.i}}));
  var tg=[];['tem','gui'].forEach(function(s){D[s].forEach(function(x){var p=cuenta(ws,x._r)?2:(cuenta(ws,x._d)?1:0);if(p)tg.push({x:x,p:p})})});
  tg.sort(function(a,b){return b.p-a.p});
  sec('Temas y guías',tg.slice(0,5).map(function(m){var x=m.x;return {u:x.u,t:x.r,s:(x._t==='tem'?'Tema de interés':'Guía')+' · '+x.s,ico:x._t}}));
  sec('Glosario',D.glo.filter(function(x){return cuenta(ws,x._r)}).slice(0,3).map(function(x){return {u:x.u,t:x.r,s:x.d,ico:'glo'}}));
  sec('Preguntas frecuentes',D.pre.filter(function(x){return cuenta(ws,x._r)}).slice(0,3).map(function(x){return {u:x.u,t:x.r,s:'Pregunta frecuente · '+x.s,ico:'pre'}}))}
 out.ref=r;return out}
var ICO={mat:'M4 5h16M4 12h16M4 19h10',tem:'M12 3l8 4-8 4-8-4zM4 12l8 4 8-4M4 17l8 4 8-4',gui:'M5 4h10l4 4v12H5zM14 4v5h5',glo:'M4 5h12a3 3 0 013 3v11H7a3 3 0 01-3-3zM8 9h7M8 13h5',pre:'M12 18v.01M9.5 9a2.5 2.5 0 115 .5c0 1.5-2.5 2-2.5 4',bus:'M11 4a7 7 0 100 14 7 7 0 000-14zM16.5 16.5L21 21'};
function icono(k){return '<span class="lhb-ic" aria-hidden="true"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="'+(ICO[k]||ICO.bus)+'"/></svg></span>'}
/* ---- caja de sugerencias pegada a un campo de búsqueda ---- */
function engancha(inp,opc){opc=opc||{};var form=inp.closest('form'),caja=d.createElement('div'),activo=-1,items=[],ultimo='',tmr=0,nid='lhb-sug-'+Math.random().toString(36).slice(2,7);
 caja.className='lhb-sug';caja.id=nid;caja.setAttribute('role','listbox');caja.hidden=true;(opc.dentro||form).appendChild(caja);
 if(!opc.dentro)form.classList.add('lhb-anc');
 inp.setAttribute('aria-controls',nid);inp.setAttribute('aria-autocomplete','list');inp.setAttribute('autocomplete','off');
 function cierra(){caja.hidden=true;activo=-1;inp.setAttribute('aria-expanded','false')}
 function marca(i){items.forEach(function(e,k){e.classList.toggle('activo',k===i);e.setAttribute('aria-selected',k===i?'true':'false')});activo=i;if(i>=0&&items[i])items[i].scrollIntoView({block:'nearest'})}
 function pinta(){var v=inp.value;if(!v.trim()){caja.innerHTML=opc.vacio?opc.vacio():'';caja.hidden=!opc.vacio;items=[].slice.call(caja.querySelectorAll('.lhb-it'));activo=-1;return}
  if(!DATOS){caja.innerHTML='<p class="lhb-nota">Cargando el buscador…</p>';caja.hidden=false;carga().then(function(){if(inp.value===v)pinta()});return}
  var S=sugerencias(v),h='';
  S.secs.forEach(function(s){h+='<div class="lhb-h">'+esc(s.t)+'</div>';s.items.forEach(function(x){
   h+='<a class="lhb-it'+(x.i?' con-tapa':'')+'" role="option" href="'+esc(x.u)+'"'+(x.prev?' data-prev="'+esc(x.prev)+'"':'')+'>'+(x.i?'<img src="'+esc(x.i)+'" alt="" loading="lazy" width="40" height="52">':icono(x.ico))+
    '<span class="lhb-tx"><b>'+esc(x.t)+'</b><small>'+esc(x.s||'')+'</small>'+(x.prev?'<span class="lhb-prev">Cargando el texto…</span>':'')+'</span></a>'})});
  if(S.pista)h+='<p class="lhb-nota">'+esc(S.pista)+'</p>';
  h+='<a class="lhb-it lhb-todo" role="option" href="/buscar/?q='+encodeURIComponent(v.trim())+'">'+icono('bus')+'<span class="lhb-tx"><b>Buscar «'+esc(v.trim())+'» en todo el sitio</b><small>Artículos, guías, temas, glosario, preguntas y texto de los PDF</small></span></a>';
  caja.innerHTML=h;caja.hidden=false;inp.setAttribute('aria-expanded','true');items=[].slice.call(caja.querySelectorAll('.lhb-it'));
  marca(S.fuerte?0:-1);
  [].slice.call(caja.querySelectorAll('[data-prev]')).forEach(function(a){var u=a.getAttribute('data-prev');previa(u).then(function(p){var s=a.querySelector('.lhb-prev');if(!s)return;if(!p||!p.txt){s.remove();return}
   s.textContent=(p.cap?p.cap+' — ':'')+(p.txt.length>260?p.txt.slice(0,260).replace(/\s+\S*$/,'')+'…':p.txt)})})}
 inp.addEventListener('input',function(){clearTimeout(tmr);tmr=setTimeout(function(){if(inp.value!==ultimo){ultimo=inp.value;pinta()}},70)});
 inp.addEventListener('focus',function(){carga();if(inp.value.trim()||opc.vacio){ultimo=inp.value;pinta()}});
 inp.addEventListener('keydown',function(e){if(caja.hidden&&e.key!=='Escape')return;
  if(e.key==='ArrowDown'){e.preventDefault();marca(Math.min(items.length-1,activo+1))}
  else if(e.key==='ArrowUp'){e.preventDefault();marca(Math.max(-1,activo-1))}
  else if(e.key==='Enter'&&activo>=0&&items[activo]){e.preventDefault();location.href=items[activo].href}
  else if(e.key==='Escape'){if(!caja.hidden){e.stopPropagation();cierra()}else if(opc.alEscape)opc.alEscape()}});
 form.addEventListener('submit',function(e){if(activo>=0&&items[activo]){e.preventDefault();location.href=items[activo].href}});
 d.addEventListener('mousedown',function(e){if(!caja.contains(e.target)&&e.target!==inp&&!opc.dentro)cierra()});
 caja.addEventListener('mousemove',function(e){var a=e.target.closest('.lhb-it');if(a)marca(items.indexOf(a))});
 return {pinta:pinta,cierra:cierra}}
/* ---- ventana de búsqueda que abre la lupa de la cabecera ---- */
var modal=null;
function ejemplos(){return '<div class="lhb-h">Prueba así</div><div class="lhb-ej">'+['art 24 CPE','artículo 138 código civil','CPP 233','despido','usucapión','constitución','letra de cambio','LGT 52'].map(function(x){return '<button type="button" class="lhb-chip">'+esc(x)+'</button>'}).join('')+'</div><p class="lhb-nota">Escribe una norma («constitución», «código penal», «Ley 348»), un artículo con su norma («art 24 CPE», «CC 138») o un tema. <kbd>Enter</kbd> abre la primera sugerencia marcada.</p>'}
function abreModal(){if(!modal){modal=d.createElement('div');modal.className='lhb-modal';modal.hidden=true;modal.setAttribute('role','dialog');modal.setAttribute('aria-modal','true');modal.setAttribute('aria-label','Buscar en LegalHubBolivia');
  modal.innerHTML='<div class="lhb-caja"><form class="buscador" role="search" action="/buscar/" method="get"><svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="M16.5 16.5L21 21"/></svg><input type="search" name="q" aria-label="Buscar en todo el sitio" placeholder="Norma, artículo o tema: «art 24 CPE»"><button type="button" class="lhb-x" aria-label="Cerrar">Esc</button></form><div class="lhb-lista"></div></div>';
  d.body.appendChild(modal);var inp=modal.querySelector('input'),lista=modal.querySelector('.lhb-lista');
  var ctl=engancha(inp,{dentro:lista,vacio:ejemplos,alEscape:cierraModal});
  modal.addEventListener('mousedown',function(e){if(e.target===modal)cierraModal()});
  modal.querySelector('.lhb-x').addEventListener('click',cierraModal);
  lista.addEventListener('click',function(e){var b=e.target.closest('.lhb-chip');if(b){inp.value=b.textContent;inp.focus();ctl.pinta()}});
  modal._inp=inp;modal._ctl=ctl}
 modal.hidden=false;d.body.classList.add('lhb-abierto');modal._inp.focus();modal._inp.select();carga();modal._ctl.pinta()}
function cierraModal(){if(modal){modal.hidden=true;d.body.classList.remove('lhb-abierto')}}
function inicia(){
 [].slice.call(d.querySelectorAll('form.buscador[action="/buscar/"] input[name="q"]')).forEach(function(i){engancha(i)});
 var enBuscar=/^\/buscar\/?$/.test(location.pathname);
 [].slice.call(d.querySelectorAll('a.ico-btn[href="/buscar/"]')).forEach(function(a){a.addEventListener('click',function(e){if(e.ctrlKey||e.metaKey||e.shiftKey)return;e.preventDefault();
  var p=d.querySelector('main form.buscador[action="/buscar/"] input');if(p&&enBuscar){p.focus();p.select();return}abreModal()})});
 d.addEventListener('keydown',function(e){var t=e.target,escribe=t&&(t.isContentEditable||/^(input|textarea|select)$/i.test(t.tagName));
  if(((e.key==='k'||e.key==='K')&&(e.ctrlKey||e.metaKey))||(e.key==='/'&&!escribe&&!e.ctrlKey&&!e.metaKey&&!e.altKey)){e.preventDefault();
   var p=d.querySelector('main form.buscador[action="/buscar/"] input');if(p){p.focus();p.select()}else abreModal()}
  else if(e.key==='Escape'&&modal&&!modal.hidden)cierraModal()})}
if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',inicia);else inicia();
/* ---- lo que usa la página de resultados (/buscar/) ---- */
function tapa(u){if(!DATOS||!u)return '';var i,x;for(i=0;i<DATOS.col.length;i++){x=DATOS.col[i];if(u.indexOf(x.u)===0)return x.i}for(i=0;i<DATOS.doc.length;i++){x=DATOS.doc[i];if(u.indexOf(x.u)===0)return x.i}return ''}
function destacado(cont,texto){var r=ref(texto);if(!r)return null;var c,u,tit,sub,img;
 if(r.tipo==='articulo'&&r.existe){c=r.x;u=urlArt(c,r.clave);tit=etiqArt(r.clave)+(c.T[r.clave]?' · '+c.T[r.clave]:'');sub=c.r;img=c.i}
 else if(r.tipo==='articulo'){c=r.x;var e0=d.createElement('div');e0.className='lhb-dest';e0.innerHTML=(c.i?'<img src="'+esc(c.i)+'" alt="" width="96" height="124">':'')+'<div><span class="etq">'+esc(c.r)+'</span><h2>No hay '+esc(etiqArt(r.clave).toLowerCase())+' en esta norma</h2><p class="sec">Esta norma por artículos tiene '+esc(rango(c))+'. El artículo puede estar derogado o tener otro número.</p><p class="lhb-acc"><a class="btn" href="'+esc(c.u)+'#indice">Abrir el índice</a></p></div>';cont.appendChild(e0);return r}
 else if(r.tipo==='norma'&&r.p>=82){var x=r.x,e1=d.createElement('div');e1.className='lhb-dest norma';var ab=x._t==='col'?x.u:x.l;
  e1.innerHTML=(x.i?'<a href="'+esc(ab)+'"><img src="'+esc(x.i)+'" alt="" width="96" height="124"></a>':'')+'<div><span class="etq">'+(x._t==='col'?'Norma por artículos':'Biblioteca · PDF')+'</span><h2><a href="'+esc(ab)+'">'+esc(x.r)+'</a></h2><p class="sec">'+esc(x.s||'')+'</p><p class="lhb-acc"><a class="btn" href="'+esc(ab)+'">'+(x._t==='col'?'Ver los artículos':'Leer el PDF')+'</a>'+(x._t==='doc'?'<a href="'+esc(x.u)+'">Ficha</a>':'')+'</p><p class="sec lhb-tip">Para ir a un artículo, escribe su número con la norma: «art 24 '+esc(x._t==='col'?(x.a[1]||x.r):x.r)+'».</p></div>';cont.appendChild(e1);return r}
 else return r;
 var e=d.createElement('div');e.className='lhb-dest';
 e.innerHTML=(img?'<a href="'+esc(u)+'"><img src="'+esc(img)+'" alt="" width="96" height="124"></a>':'')+'<div><span class="etq">'+esc(sub)+'</span><h2><a href="'+esc(u)+'">'+esc(tit)+'</a></h2><p class="lhb-cap sec"></p><div class="lhb-txt">Cargando el texto…</div><p class="lhb-acc"><a class="btn" href="'+esc(u)+'">Abrir el artículo</a><a href="'+esc(c.u)+'#indice">Índice de la norma</a></p></div>';
 cont.appendChild(e);previa(u).then(function(p){var t=e.querySelector('.lhb-txt');if(!p||!p.txt){t.textContent='';return}t.textContent=p.ps.join('\n');if(p.cap)e.querySelector('.lhb-cap').textContent=p.cap});return r}
W.LHB={carga:carga,ref:ref,tapa:tapa,destacado:destacado,norm:norm,palabras:palabras,urlArt:urlArt};
})();
