// Visor de PDF de la Biblioteca (usa pdf.js, licencia Apache 2.0)
const $ = (id) => document.getElementById(id);
const raiz = $('lector'), carga = $('carga'), avance = $('avance');
const movil = () => window.innerWidth < 700;

function falla() {
  carga.hidden = false;
  carga.innerHTML = 'No se pudo abrir el documento en el visor.<br><a href="' + raiz.dataset.pdf + '" download>Descargar el PDF</a>';
}

(async () => {
try {
  const pdfjsLib = await import('/visor/pdf.min.js');
  pdfjsLib.GlobalWorkerOptions.workerSrc = '/visor/pdf.worker.min.js';
  globalThis.pdfjsLib = pdfjsLib;
  const V = await import('/visor/pdf_viewer.js');

  const eventBus = new V.EventBus();
  const linkService = new V.PDFLinkService({ eventBus });
  const findController = new V.PDFFindController({ eventBus, linkService });
  const viewer = new V.PDFViewer({ container: $('visor-cont'), viewer: $('viewer'), eventBus, linkService, findController });
  linkService.setViewer(viewer);

  const params = new URLSearchParams(location.search);
  const inicial = params.get('buscar') || '';
  const pagHash = parseInt((location.hash.match(/page=(\d+)/) || [])[1], 10);

  eventBus.on('pagesinit', () => {
    viewer.currentScaleValue = movil() ? 'page-width' : 'auto';
    if (pagHash) viewer.currentPageNumber = pagHash;
    carga.hidden = true;
    if (inicial) { $('q').value = inicial; abreBusca(); buscar(''); }
  });
  eventBus.on('pagechanging', (e) => { $('pag').value = e.pageNumber; });

  // buscador interno
  const q = $('q'), conteo = $('conteo'), form = $('busca');
  function buscar(tipo, previo) {
    if (!q.value.trim()) { conteo.textContent = ''; conteo.className = 'conteo'; }
    eventBus.dispatch('find', { source: null, type: tipo, query: q.value.trim(), caseSensitive: false, entireWord: false,
      highlightAll: true, findPrevious: !!previo, matchDiacritics: false });
  }
  function pintaConteo(m) {
    if (!q.value.trim()) return;
    if (m && m.total) { conteo.textContent = m.current + ' de ' + m.total; conteo.className = 'conteo'; }
  }
  eventBus.on('updatefindmatchescount', (e) => pintaConteo(e.matchesCount));
  eventBus.on('updatefindcontrolstate', (e) => {
    if (e.state === 1 && q.value.trim()) { conteo.textContent = 'Sin resultados'; conteo.className = 'conteo no'; }
    else pintaConteo(e.matchesCount);
  });
  let t;
  q.addEventListener('input', () => { clearTimeout(t); t = setTimeout(() => buscar(''), 300); });
  form.addEventListener('submit', (e) => { e.preventDefault(); buscar('again', false); q.blur(); });
  q.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); buscar('again', e.shiftKey); } });
  $('sig').addEventListener('click', () => buscar('again', false));
  $('ant').addEventListener('click', () => buscar('again', true));
  function abreBusca() { form.classList.add('abierto'); }
  $('abre-busca').addEventListener('click', () => {
    if (form.classList.toggle('abierto')) q.focus();
  });

  // página y tamaño
  $('pag').addEventListener('change', (e) => {
    const n = Math.max(1, Math.min(viewer.pagesCount, parseInt(e.target.value, 10) || 1));
    viewer.currentPageNumber = n;
  });
  $('mas').addEventListener('click', () => viewer.increaseScale());
  $('menos').addEventListener('click', () => viewer.decreaseScale());
  let ancho = window.innerWidth;
  window.addEventListener('resize', () => {
    if (Math.abs(window.innerWidth - ancho) > 80 && ['page-width', 'auto'].includes(viewer.currentScaleValue)) {
      viewer.currentScaleValue = movil() ? 'page-width' : 'auto';
    }
    ancho = window.innerWidth;
  });

  const tarea = pdfjsLib.getDocument({ url: raiz.dataset.pdf, cMapUrl: '/visor/cmaps/', cMapPacked: true,
    standardFontDataUrl: '/visor/standard_fonts/', wasmUrl: '/visor/wasm/', iccUrl: '/visor/iccs/' });
  tarea.onProgress = (p) => { if (p.total) avance.textContent = Math.round(100 * p.loaded / p.total) + ' %'; };
  const doc = await tarea.promise;
  viewer.setDocument(doc);
  linkService.setDocument(doc, null);
} catch (e) {
  console.error(e);
  falla();
}
})();
