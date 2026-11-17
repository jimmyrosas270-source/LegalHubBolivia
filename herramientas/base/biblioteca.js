(function(){
var d=document,inp=d.getElementById('filtro');if(!inp)return;
var dest=d.getElementById('destacadas'),libros=[].slice.call(d.querySelectorAll('.libro:not(.destacada)')),chips=[].slice.call(d.querySelectorAll('.chip-f')),grupos=[].slice.call(d.querySelectorAll('.grupo-lib')),
cuenta=d.getElementById('cuenta'),nada=d.getElementById('nada'),todos=d.getElementById('todos'),carpetas=d.getElementById('carpetas'),mat='';
function norm(s){return s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'')}
function aplica(){var p=norm(inp.value.trim()).split(/\s+/).filter(Boolean),n=0;
if(todos){todos.hidden=!p.length;if(carpetas)carpetas.hidden=!!p.length}
if(dest)dest.hidden=!!(p.length||mat);
libros.forEach(function(l){var t=norm(l.getAttribute('data-texto')),ok=(!mat||l.getAttribute('data-materia')===mat)&&p.every(function(w){return t.indexOf(w)>=0});l.hidden=!ok;if(ok)n++});
grupos.forEach(function(g){g.hidden=!g.querySelector('.libro:not([hidden])')});
if(cuenta)cuenta.textContent=n+(n===1?' documento':' documentos');if(nada)nada.hidden=n>0}
inp.addEventListener('input',aplica);
chips.forEach(function(c){c.addEventListener('click',function(){mat=c.getAttribute('data-m');chips.forEach(function(o){o.setAttribute('aria-pressed',o===c?'true':'false')});aplica()})});
})();
