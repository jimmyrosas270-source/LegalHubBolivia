(function(){
var d=document;
var m=d.querySelector('[data-menu]'),menu=d.getElementById('menu');
if(m&&menu){m.addEventListener('click',function(){var a=menu.hasAttribute('hidden');if(a){menu.removeAttribute('hidden')}else{menu.setAttribute('hidden','')}m.setAttribute('aria-expanded',a?'true':'false')})}
var c=d.querySelector('[data-copiar]');
if(c){c.addEventListener('click',function(){var t=c.lastChild;function ok(){var o=t.textContent;t.textContent='Copiado';setTimeout(function(){t.textContent=o},1600)}
if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(location.href).then(ok,function(){})}else{var i=d.createElement('input');i.value=location.href;d.body.appendChild(i);i.select();try{d.execCommand('copy');ok()}catch(e){}d.body.removeChild(i)}})}
var l=d.querySelector('[data-lectura]');
function lectura(on){d.body.classList.toggle('lectura',on);if(l)l.setAttribute('aria-pressed',on?'true':'false');try{sessionStorage.setItem('lectura',on?'1':'')}catch(e){}}
if(l){var prev='';try{prev=sessionStorage.getItem('lectura')}catch(e){}if(prev)lectura(true);l.addEventListener('click',function(){lectura(!d.body.classList.contains('lectura'))})}
var R=d.getElementById('resultados');
if(R){
var est=d.getElementById('estado'),inp=d.querySelector('.buscador input');
var q=new URLSearchParams(location.search).get('q')||'';inp.value=q;
function norm(s){return s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'')}
function esc(s){return s.replace(/[&<>"]/g,function(ch){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[ch]})}
function pinta(lista,palabras){R.innerHTML='';lista.slice(0,60).forEach(function(a){var t=a.t,n=norm(t),p=0;for(var i=0;i<palabras.length;i++){var k=n.indexOf(palabras[i]);if(k>=0){p=k;break}}
var ini=Math.max(0,p-70),frag=(ini>0?'…':'')+t.slice(ini,ini+220)+(ini+220<t.length?'…':'');var h=esc(frag);
palabras.forEach(function(w){if(w.length<3)return;var nf=norm(frag),out='',pos=0,k;while((k=nf.indexOf(w,pos))>=0){out+=esc(frag.slice(pos,k))+'<mark>'+esc(frag.slice(k,k+w.length))+'</mark>';pos=k+w.length}if(out){h=out+esc(frag.slice(pos))}});
var e=d.createElement('a');e.className='res';e.href=a.u;e.innerHTML='<b>Artículo '+a.n+'</b><span>'+h+'</span>';R.appendChild(e)})}
function busca(datos){var s=norm(q.trim());if(!s){est.textContent='';return}
var num=s.match(/^(?:art(?:iculo)?\.?\s*)?(\d{1,3})$/);var palabras=s.split(/\s+/).filter(Boolean);var lista;
if(num){lista=datos.filter(function(a){return a.n===+num[1]});palabras=[]}else{lista=datos.filter(function(a){var n=norm(a.t);return palabras.every(function(w){return n.indexOf(w)>=0})})}
est.textContent=lista.length?(lista.length+(lista.length===1?' resultado':' resultados')+(lista.length>60?'; se muestran los primeros 60':'')):'Sin resultados. Prueba con otra palabra o con el número del artículo.';pinta(lista,palabras)}
if(q){est.textContent='Buscando…';fetch('/buscar/indice.json').then(function(r){return r.json()}).then(busca).catch(function(){est.textContent='No se pudo cargar el índice de búsqueda.'})}
}
})();
