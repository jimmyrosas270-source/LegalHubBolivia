"""Revisa el HTML y los enlaces internos del sitio construido. Uso: python3 herramientas/revisar.py salida"""
import sys, os, re, html.parser
root = sys.argv[1]
VOID = {'meta', 'link', 'input', 'br', 'img', 'hr', 'circle', 'path', 'rect'}
class C(html.parser.HTMLParser):
    def __init__(s): super().__init__(); s.st = []; s.err = []; s.hrefs = []
    def handle_starttag(s, t, a):
        for k, v in a:
            if k in ('href', 'src') and v: s.hrefs.append(v)
        if t not in VOID: s.st.append(t)
    def handle_startendtag(s, t, a): pass
    def handle_endtag(s, t):
        if t in VOID: return
        if not s.st or s.st[-1] != t: s.err.append((t, s.st[-3:], s.getpos()))
        else: s.st.pop()
files = []; bad = 0; missing = set(); n_links = 0
for dp, _, fs in os.walk(root):
    for f in fs: files.append(os.path.join(dp, f))
for f in files:
    if not f.endswith('.html'): continue
    c = C(); c.feed(open(f, encoding='utf-8').read())
    if c.err or c.st: bad += 1; print('HTML', f, c.err[:2], c.st[:4])
    for h in c.hrefs:
        if not h.startswith('/'): continue
        n_links += 1
        path = h.split('#')[0].split('?')[0]
        target = os.path.join(root, path.lstrip('/'))
        if path.endswith('/'): target = os.path.join(target, 'index.html')
        if not os.path.isfile(target): missing.add(h)
graves = sorted(h for h in missing if h.startswith(('/biblioteca/', '/visor/', '/assets/')))
otros = sorted(set(missing) - set(graves))
print('archivos', len(files), '| html con errores', bad, '| enlaces internos', n_links, '| rotos', len(missing))
if otros: print('AVISO: enlaces a secciones que aún no existen:', otros[:10])
if graves: print('ERROR: enlaces rotos de la Biblioteca:', graves[:10])
print('tamaño total MB', sum(os.path.getsize(f) for f in files) // 1048576)
if bad or graves: sys.exit(1)
