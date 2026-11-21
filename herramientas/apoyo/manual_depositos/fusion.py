"""Fusiona las dos pasadas de OCR (json: x1,5; json1: x1) y marca las palabras dudosas para revisión visual.
Salida: dudas.json (lista de dudas con id, página, bbox y candidatos) y base.json (palabras por línea)."""
import json, glob, os, re, collections, unicodedata
os.chdir('/home/claude/manual')

V = collections.Counter(re.findall(r'[a-záéíóúüñ]+', open('/tmp/corpus.txt', encoding='utf-8', errors='ignore').read().lower()))


def sin_tilde(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


VARIANTES = collections.defaultdict(set)
for w in V:
    if V[w] >= 3: VARIANTES[sin_tilde(w)].add(w)


def iou(a, b):
    x0, y0 = max(a['x'], b['x']), max(a['y'], b['y'])
    x1, y1 = min(a['x'] + a['w'], b['x'] + b['w']), min(a['y'] + a['h'], b['y'] + b['h'])
    if x1 <= x0 or y1 <= y0: return 0
    i = (x1 - x0) * (y1 - y0)
    return i / (a['w'] * a['h'] + b['w'] * b['h'] - i)


paginas = {}
todas = []
for f in sorted(glob.glob('json/p-*.json')):
    k = os.path.basename(f)[:-5]
    A = json.load(open(f)); B = json.load(open('json1/' + k + '.json'))
    for w in A['palabras']:
        m = max(B['palabras'], key=lambda b: iou(w, b), default=None)
        w['alt'] = m['t'] if m and iou(w, m) > 0.4 else None
        todas.append((k, w))
    paginas[k] = A

# vocabulario propio del documento: palabras en que coinciden las dos pasadas con buena confianza
OC = collections.Counter()
for k, w in todas:
    if w['alt'] == w['t'] and w['c'] >= 85:
        OC[re.sub(r'[^\wáéíóúüñÁÉÍÓÚÜÑ/-]', '', w['t']).lower()] += 1


def nucleo(t):
    return re.sub(r'^[^\wáéíóúüñÁÉÍÓÚÜÑ]+|[^\wáéíóúüñÁÉÍÓÚÜÑ]+$', '', t)


dudas = []
for k, w in todas:
    t = w['t']; n = nucleo(t); ln = n.lower()
    motivos = []
    if w['alt'] != t: motivos.append('dif')
    if w['c'] < 85: motivos.append('conf')
    alfa = re.fullmatch(r'[a-záéíóúüñ]+', ln)
    if alfa and len(ln) > 1 and V[ln] < 2 and OC[ln] < 3: motivos.append('dicc')
    mayus = sum(ch.isupper() for ch in n) >= 2
    if alfa and mayus and len(ln) > 2 and len(VARIANTES.get(sin_tilde(ln), ())) > 1: motivos.append('tilde')
    if w['alt'] and w['alt'] != t and sin_tilde(w['alt']) == sin_tilde(t): motivos.append('tilde')
    if not alfa and n and not re.fullmatch(r'\d+|[A-ZÁÉÍÓÚÑ]+|OJ/DJT-0\d|y/o|N°|Nº|[\d.,]+|\d+/\d+', n): motivos.append('raro')
    if not n: motivos.append('signo')
    if re.search(r'\d', t) and len(re.sub(r'\D', '', t)) >= 1 and w['k'].startswith('t'): motivos.append('num')
    if motivos:
        w['id'] = len(dudas)
        dudas.append({'id': w['id'], 'k': k, 'x': w['x'], 'y': w['y'], 'w': w['w'], 'h': w['h'], 't': t, 'alt': w['alt'], 'm': motivos})
json.dump(dudas, open('dudas.json', 'w'), ensure_ascii=False)
json.dump(paginas, open('base.json', 'w'), ensure_ascii=False)
print('palabras', len(todas), 'dudas', len(dudas))
print(collections.Counter(m for d in dudas for m in d['m']))
print(collections.Counter(tuple(d['m']) for d in dudas).most_common(15))
