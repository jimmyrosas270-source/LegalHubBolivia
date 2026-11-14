(function(){
var d=document,inp=d.getElementById('filtro');if(!inp)return;
var libros=[].slice.call(d.querySelectorAll('.libro')),chips=[].slice.call(d.querySelectorAll('.chip-f')),cuenta=d.getElementById('cuenta'),nada=d.getElementById('nada'),mat='';
function norm(s){return s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'')}
function aplica(){var p=norm(inp.value.trim()).split(/\s+/).filter(Boolean),n=0;
libros.forEach(function(l){var t=norm(l.getAttribute('data-texto')),ok=(!mat||l.getAttribute('data-materia')===mat)&&p.every(function(w){return t.indexOf(w)>=0});l.hidden=!ok;if(ok)n++});
cuenta.textContent=n+(n===1?' documento':' documentos');nada.hidden=n>0}
inp.addEventListener('input',aplica);
chips.forEach(function(c){c.addEventListener('click',function(){mat=c.getAttribute('data-m');chips.forEach(function(o){o.setAttribute('aria-pressed',o===c?'true':'false')});aplica()})});
})();
