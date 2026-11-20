/* LegalHubBolivia: tarjetas «¿Sabías que?».
   - Carrusel en [data-tarjetas]: avanza solo cada 9 s (se detiene al pasar el mouse, al enfocar,
     si la pestaña no está visible y nunca con «reducir movimiento»); botones anterior y siguiente.
   - Una tarjeta al azar dentro de las páginas de contenido (antes del recuadro «Reportar un error»).
   - Una tarjeta flotante, una sola vez por sesión del navegador (sessionStorage), a los 25 s; se puede cerrar.
   - Filtro por materia en /temas/.
   Los datos salen de /assets/tarjetas.json (temas y guías del sitio). */
(function () {
  var d = document, w = window;
  var quieto = w.matchMedia && w.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var ruta = location.pathname;

  function esc(t) { var e = d.createElement('div'); e.textContent = t; return e.innerHTML; }
  function nombreMateria(m) {
    var n = {'constitucional': 'Constitucional', 'laboral': 'Laboral', 'familia': 'Familia', 'civil': 'Civil', 'procesal-civil': 'Procesal civil',
      'penal': 'Penal', 'procesal-penal': 'Procesal penal', 'administrativa': 'Administrativa', 'agraria': 'Agraria', 'tributario': 'Tributario',
      'personas-con-discapacidad': 'Personas con discapacidad', 'comercial': 'Comercial'};
    return n[m] || '';
  }
  function datoHTML(x) {
    return '<article class="dato" data-mc="' + esc(x.m) + '"><span class="dato-m">' + esc(nombreMateria(x.m) || '¿Sabías que?') + '</span><p>' + esc(x.t) +
      '</p><footer><small>' + esc(x.f) + '</small><a href="' + esc(x.u) + '">Leer más: ' + esc(x.tema) + '</a></footer></article>';
  }

  /* ---------- carrusel ---------- */
  Array.prototype.forEach.call(d.querySelectorAll('[data-tarjetas]'), function (c) {
    var pista = c.querySelector('.sabias-pista');
    if (!pista) return;
    // El HTML ya viene intercalado por tema y materia: se rota desde un punto al azar para no repetir el orden.
    var hijos = Array.prototype.slice.call(pista.children), k = Math.floor(Math.random() * hijos.length);
    hijos.slice(0, k).forEach(function (h) { pista.appendChild(h); });
    pista.scrollLeft = 0;
    function paso() { var h = pista.children[0]; return h ? h.getBoundingClientRect().width + 14 : pista.clientWidth; }
    function mueve(dir) {
      var max = pista.scrollWidth - pista.clientWidth - 2;
      if (dir > 0 && pista.scrollLeft >= max) pista.scrollTo({left: 0, behavior: quieto ? 'auto' : 'smooth'});
      else if (dir < 0 && pista.scrollLeft <= 2) pista.scrollTo({left: max, behavior: quieto ? 'auto' : 'smooth'});
      else pista.scrollBy({left: dir * paso(), behavior: quieto ? 'auto' : 'smooth'});
    }
    var prev = c.querySelector('[data-prev]'), next = c.querySelector('[data-next]');
    if (prev) prev.addEventListener('click', function () { mueve(-1); });
    if (next) next.addEventListener('click', function () { mueve(1); });
    pista.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight') { e.preventDefault(); mueve(1); }
      if (e.key === 'ArrowLeft') { e.preventDefault(); mueve(-1); }
    });
    if (quieto) return;
    var pausa = false;
    c.addEventListener('mouseenter', function () { pausa = true; });
    c.addEventListener('mouseleave', function () { pausa = false; });
    c.addEventListener('focusin', function () { pausa = true; });
    c.addEventListener('focusout', function () { pausa = false; });
    pista.addEventListener('touchstart', function () { pausa = true; }, {passive: true});
    setInterval(function () {
      if (pausa || d.hidden) return;
      var r = c.getBoundingClientRect();
      if (r.bottom < 0 || r.top > (w.innerHeight || 0)) return;
      mueve(1);
    }, 9000);
  });

  /* ---------- salida rápida ---------- */
  var sal = d.querySelector('[data-salida]');
  if (sal) {
    var vete = function () { try { d.body.style.display = 'none'; } catch (e) {} location.replace('https://www.google.com/search?q=clima'); };
    sal.addEventListener('click', vete);
    var ultEsc = 0;
    d.addEventListener('keydown', function (e) { if (e.key === 'Escape') { var t = Date.now(); if (t - ultEsc < 800) vete(); ultEsc = t; } });
  }

  /* ---------- filtro de temas ---------- */
  var filtro = d.querySelector('.filtro-temas'), rejilla = d.querySelector('[data-temas]');
  if (filtro && rejilla) {
    filtro.addEventListener('click', function (e) {
      var b = e.target.closest('button');
      if (!b) return;
      Array.prototype.forEach.call(filtro.querySelectorAll('button'), function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
      var m = b.getAttribute('data-ft');
      Array.prototype.forEach.call(rejilla.children, function (t) { t.hidden = !!m && t.getAttribute('data-mc') !== m; });
    });
  }

  /* ---------- tarjeta suelta y flotante ---------- */
  var excluida = ruta === '/' || ruta === '/index.html' || /^\/(temas\/?$|buscar\/|visor\/|estudiantes\/cuestionarios\/)/.test(ruta) || /\/leer\//.test(ruta);
  if (excluida) return;
  var main = d.querySelector('main');
  if (!main || !w.fetch) return;
  fetch('/assets/tarjetas.json').then(function (r) { return r.json(); }).then(function (todas) {
    var propias = function (x) { return ruta.indexOf(x.u.split('#')[0]) === 0; };
    var lista = todas.filter(function (x) { return !propias(x); });
    if (!lista.length) return;
    var mat = d.body.getAttribute('data-m');
    var mismas = mat ? lista.filter(function (x) { return x.m === mat; }) : [];
    var fuente = mismas.length ? mismas : lista;
    var uno = fuente[Math.floor(Math.random() * fuente.length)];

    // 1) tarjeta dentro de la página
    if (!d.querySelector('[data-tarjetas]')) {
      var caja = d.createElement('aside');
      caja.className = 'dato-suelto';
      caja.setAttribute('aria-label', '¿Sabías que?');
      caja.innerHTML = '<b>¿Sabías que?</b>' + datoHTML(uno);
      var rep = d.querySelector('.reportar');
      var envol = rep ? rep.parentNode : null;
      if (envol && envol.parentNode === main) {
        var cont = d.createElement('div');
        cont.className = 'cont estrecha';
        cont.appendChild(caja);
        main.insertBefore(cont, envol);
      } else {
        var dentro = main.querySelector('.pag') || main;
        dentro.appendChild(caja);
      }
    }

    // 2) tarjeta flotante, una vez por sesión
    var clave = 'lhb-tarjeta';
    try { if (sessionStorage.getItem(clave)) return; } catch (e) { return; }
    var otro = lista[Math.floor(Math.random() * lista.length)];
    if (otro === uno && lista.length > 1) otro = lista[(lista.indexOf(uno) + 1) % lista.length];
    setTimeout(function () {
      if (d.hidden) return;
      try { sessionStorage.setItem(clave, '1'); } catch (e) {}
      var f = d.createElement('aside');
      f.className = 'dato-flota';
      f.setAttribute('role', 'complementary');
      f.setAttribute('aria-label', '¿Sabías que?');
      f.innerHTML = '<button type="button" class="cerrar" aria-label="Cerrar la tarjeta"><svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg></button>' + datoHTML(otro);
      var cierra = function () { if (f.parentNode) f.parentNode.removeChild(f); d.removeEventListener('keydown', esc2); };
      var esc2 = function (e) { if (e.key === 'Escape') cierra(); };
      f.querySelector('.cerrar').addEventListener('click', cierra);
      d.addEventListener('keydown', esc2);
      d.body.appendChild(f);
    }, 25000);
  }).catch(function () {});
})();
