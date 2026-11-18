/* Cuestionarios de estudio de LegalHubBolivia. Todo ocurre en el navegador: no se envían respuestas.
   Solo se guarda, en este navegador, la mejor nota de cada cuestionario (localStorage, clave «lhb-cuestionarios»). */
(function () {
  'use strict';
  var CLAVE = 'lhb-cuestionarios';

  function leerNotas() {
    try { return JSON.parse(localStorage.getItem(CLAVE) || '{}') || {}; } catch (e) { return {}; }
  }
  function guardarNota(id, nota) {
    var n = leerNotas(), antes = n[id];
    if (typeof antes === 'number' && antes >= nota) return false;
    n[id] = nota;
    try { localStorage.setItem(CLAVE, JSON.stringify(n)); } catch (e) { return false; }
    return true;
  }
  function el(tag, attrs, html) {
    var x = document.createElement(tag);
    if (attrs) for (var k in attrs) { if (k === 'class') x.className = attrs[k]; else x.setAttribute(k, attrs[k]); }
    if (html != null) x.innerHTML = html;
    return x;
  }
  function esc(t) {
    return String(t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; });
  }
  function mezclar(a) {
    a = a.slice();
    for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)), t = a[i]; a[i] = a[j]; a[j] = t; }
    return a;
  }
  function enlaces(lista) {
    return lista.map(function (x) {
      return '<a href="' + esc(x.u) + '" target="_blank" rel="noopener">' + esc(x.t) + '</a>';
    }).join(' · ');
  }

  // ---- notas guardadas en las listas (Estudiantes y páginas de materia)
  function pintarNotas() {
    var notas = leerNotas();
    Array.prototype.forEach.call(document.querySelectorAll('[data-cq]'), function (a) {
      var s = a.querySelector('[data-cq-nota]'), v = notas[a.getAttribute('data-cq')];
      if (!s) return;
      if (typeof v === 'number') { s.textContent = 'Tu mejor nota: ' + v + '/100'; s.className = 'cq-nota si'; }
      else { s.textContent = 'Sin intentos'; s.className = 'cq-nota'; }
    });
    var m = document.querySelector('[data-cq-mejor]'), datos = document.getElementById('cq-datos');
    if (m && datos) {
      var id = JSON.parse(datos.textContent).id;
      if (typeof notas[id] === 'number') { m.textContent = 'Tu mejor nota en este navegador: ' + notas[id] + '/100.'; m.hidden = false; }
      else m.hidden = true;
    }
  }
  Array.prototype.forEach.call(document.querySelectorAll('[data-cq-borrar]'), function (b) {
    var original = b.textContent, armado = false;
    b.addEventListener('click', function () {
      if (!armado) { armado = true; b.textContent = '¿Seguro? Toca otra vez para borrar'; return; }
      try { localStorage.removeItem(CLAVE); } catch (e) {}
      armado = false; b.textContent = 'Notas borradas'; pintarNotas();
      setTimeout(function () { b.textContent = original; }, 2500);
    });
  });
  pintarNotas();

  // ---- cuestionario
  var caja = document.getElementById('cq'), fuente = document.getElementById('cq-datos');
  if (!caja || !fuente) return;
  var D = JSON.parse(fuente.textContent);
  var ronda, i, aciertos, falladas;

  function tramo(nota) {
    if (nota === 100) return { c: 't-ok', m: '¡Felicidades, estás listo para litigar!', s: 'Respondiste todo bien. Prueba otro tema, o vuelve a intentarlo: las preguntas cambian de orden.' };
    if (nota >= 90) return { c: 't-ok', m: 'Muy bueno.', s: 'Te faltó muy poco. Revisa la explicación de lo que fallaste.' };
    if (nota >= 70) return { c: 't-ok', m: 'Bueno.', s: 'Vas por buen camino. Repasa las preguntas que fallaste y vuelve a intentarlo.' };
    if (nota >= 51) return { c: 't-reg', m: 'Regular.', s: 'Te conviene un repaso antes de volver a intentarlo.', repaso: 'Repaso sugerido' };
    return { c: 't-mal', m: 'Reprobado.', s: 'No te desanimes: repasa estos temas y vuelve a intentarlo.', repaso: 'Temas que debes repasar' };
  }

  function empezar() {
    ronda = mezclar(D.preguntas).slice(0, D.mostrar);
    i = 0; aciertos = 0; falladas = [];
    pregunta();
  }

  function pregunta() {
    var p = ronda[i], n = ronda.length;
    caja.innerHTML = '';
    var barra = el('div', { class: 'cq-barra' }, '<span>Pregunta ' + (i + 1) + ' de ' + n + '</span><span>' + aciertos + ' correcta' + (aciertos === 1 ? '' : 's') + '</span>');
    var prog = el('div', { class: 'cq-prog', role: 'progressbar', 'aria-valuemin': '0', 'aria-valuemax': String(n), 'aria-valuenow': String(i), 'aria-label': 'Avance' }, '<i style="width:' + (i * 100 / n) + '%"></i>');
    var t = el('div', { class: 'cq-tarjeta' });
    t.appendChild(el('p', { class: 'cq-enun', id: 'cq-enun' }, esc(p.t)));
    var opc = el('div', { class: 'cq-opc', role: 'group', 'aria-labelledby': 'cq-enun' });
    var bV = el('button', { type: 'button' }, 'Verdadero'), bF = el('button', { type: 'button' }, 'Falso');
    opc.appendChild(bV); opc.appendChild(bF); t.appendChild(opc);
    caja.appendChild(barra); caja.appendChild(prog); caja.appendChild(t);
    function responder(valor, boton) {
      bV.disabled = bF.disabled = true;
      var ok = valor === p.r;
      boton.classList.add('elegida'); if (!ok) boton.classList.add('mal');
      if (ok) aciertos++; else falladas.push(p);
      barra.lastChild.textContent = aciertos + ' correcta' + (aciertos === 1 ? '' : 's');
      var r = el('div', { class: 'cq-res ' + (ok ? 'bien' : 'mal') });
      r.appendChild(el('h2', { tabindex: '-1' }, ok ? '✓ ¡Correcto!' : '✗ Incorrecto'));
      r.appendChild(el('p', null, '<b>La afirmación es ' + (p.r ? 'verdadera' : 'falsa') + '.</b> ' + p.e));
      var f = '<span><b>Norma:</b> ' + enlaces(p.n) + '</span>';
      if (p.g && p.g.length) f += '<span><b>Guía:</b> ' + enlaces(p.g) + '</span>';
      r.appendChild(el('p', { class: 'cq-fuentes' }, f));
      t.appendChild(r);
      var ult = i === n - 1;
      var sig = el('button', { type: 'button', class: 'btn cq-sig' }, ult ? 'Ver mi nota' : 'Siguiente pregunta');
      sig.addEventListener('click', function () { i++; if (ult) final(); else pregunta(); caja.scrollIntoView({ block: 'start', behavior: 'smooth' }); });
      t.appendChild(sig);
      r.firstChild.focus({ preventScroll: true });
      r.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
    bV.addEventListener('click', function () { responder(true, bV); });
    bF.addEventListener('click', function () { responder(false, bF); });
  }

  function final() {
    var n = ronda.length, nota = Math.round(aciertos * 100 / n), tr = tramo(nota);
    var record = guardarNota(D.id, nota);
    caja.innerHTML = '';
    var t = el('div', { class: 'cq-tarjeta cq-final ' + tr.c });
    t.appendChild(el('h2', { tabindex: '-1' }, 'Tu nota'));
    t.appendChild(el('p', { class: 'cq-nota-grande' }, nota + '<small>/100</small>'));
    t.appendChild(el('p', { class: 'sec' }, aciertos + ' de ' + n + ' respuestas correctas'));
    if (record) t.appendChild(el('span', { class: 'cq-sello' }, 'Tu mejor nota en este navegador'));
    t.appendChild(el('p', { class: 'cq-msg' }, esc(tr.m)));
    t.appendChild(el('p', null, esc(tr.s)));
    if (tr.repaso) {
      var vistas = {}, guias = [];
      falladas.forEach(function (p) { (p.g || []).forEach(function (g) { if (!vistas[g.u]) { vistas[g.u] = 1; guias.push(g); } }); });
      if (!guias.length) guias = D.repaso;
      var rep = el('div', { class: 'cq-repaso' }, '<h3>' + esc(tr.repaso) + '</h3>');
      guias.forEach(function (g) {
        rep.appendChild(el('a', { class: 'fila', href: g.u }, '<span><b>' + esc(g.t) + '</b><small>Guía</small></span><svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6l6 6-6 6"/></svg>'));
      });
      t.appendChild(rep);
    }
    if (falladas.length) {
      var fx = el('div', { class: 'cq-falladas' }, '<h3>Lo que fallaste</h3>');
      falladas.forEach(function (p) {
        fx.appendChild(el('details', null, '<summary>' + esc(p.t) + '</summary><p><b>Era ' + (p.r ? 'verdadera' : 'falsa') + '.</b> ' + p.e + '</p><p class="cq-fuentes"><span><b>Norma:</b> ' + enlaces(p.n) + '</span></p>'));
      });
      t.appendChild(fx);
    }
    var bot = el('div', { class: 'botones' });
    var otra = el('button', { type: 'button', class: 'btn' }, 'Intentar de nuevo');
    otra.addEventListener('click', function () { empezar(); caja.scrollIntoView({ block: 'start', behavior: 'smooth' }); });
    bot.appendChild(otra);
    bot.appendChild(el('a', { class: 'btn sec', href: D.materia_url }, 'Otros cuestionarios'));
    t.appendChild(bot);
    caja.appendChild(t);
    t.firstChild.focus({ preventScroll: true });
    pintarNotas();
  }

  empezar();
})();
