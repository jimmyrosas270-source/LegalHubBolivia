import json, re, collections, statistics, cv2, numpy as np
P = json.load(open('base.json'))
D = {d['id']: d for d in json.load(open('dudas.json'))}
C = {}
for l in open('corr.txt', encoding='utf-8'):
    l = l.rstrip('\n')
    if '=' in l:
        i, t = l.split('=', 1); C[(D[int(i)]['k'], D[int(i)]['x'], D[int(i)]['y'])] = t
VI = {(o['k'], o['x'], o['y']): o['v'] for o in json.load(open('vinetas.json')) if o['v']}
SIMB = set('✓●■❖○➢•')
GLOBAL = {'Unica': 'Única', 'Sila': 'Si la', 'Siel': 'Si el', 'Silos': 'Si los', 'Siexiste': 'Si existe', 'Enel': 'En el', 'Enun': 'En un', 'Enlos': 'En los', 'Sitiene': 'Si tiene', 'Siesta': 'Si esta'}
LC = json.load(open('lineas_corr.json', encoding='utf-8'))
PC = json.load(open('palabras_corr.json', encoding='utf-8'))
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont('R', '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'))


def relinea(lw, texto):
    """Sustituye el texto de una línea revisada a ojo: mantiene las cajas si coincide el número de palabras;
    si no, reparte las palabras nuevas a lo largo de la línea."""
    toks = texto.split()
    viejas = [w for w in lw]
    if len(toks) == len(viejas):
        for w, t in zip(viejas, toks):
            w['t'] = t; w['sim'] = 1 if t in SIMB else 0
        return viejas
    x0 = viejas[0]['x']; x1 = max(w['x'] + w['w'] for w in viejas)
    y = min(w['y'] for w in viejas if not w.get('sim')) if any(not w.get('sim') for w in viejas) else viejas[0]['y']
    h = statistics.median([w['h'] for w in viejas if not w.get('sim')] or [24])
    b = sum(1 for w in viejas if w.get('b')) > len(viejas) / 2
    anchos = [pdfmetrics.stringWidth(t, 'R', 10) for t in toks]
    esp = pdfmetrics.stringWidth(' ', 'R', 10)
    tot = sum(anchos) + esp * (len(toks) - 1)
    f = (x1 - x0) / tot if tot else 1
    out, x = [], x0
    for t, a in zip(toks, anchos):
        w = {'t': t, 'x': int(x), 'y': y, 'w': int(a * f), 'h': h, 'c': 99, 'd': 0, 'k': viejas[0]['k'], 'corr': 1}
        if t in SIMB: w['sim'] = 1
        elif b: w['b'] = 1
        out.append(w); x += (a + esp) * f
    return out


final = {}
for k, pag in P.items():
    ws = []
    for w in pag['palabras']:
        key = (k, w['x'], w['y'])
        t = w['t']
        if key in VI: t = VI[key]
        if f'{k}|{w["x"]}|{w["y"]}' in PC: t = PC[f'{k}|{w["x"]}|{w["y"]}']; corr = True
        elif key in C: t = C[key]; corr = True
        else: corr = False
        if t == '' and re.fullmatch(r'[-–—=_~]+', w['t']) and w['w'] <= 40 and w['h'] < 10: t = w['t']  # se decide abajo (guion o subrayado)
        if t == '' or t in ('|', '||', '[|', '|]'): continue
        t = t.replace('OJ/DJT-O', 'OJ/DJT-0').replace('N*', 'N°')
        t = GLOBAL.get(t, t)
        t = re.sub(r'^aajunt', 'adjunt', t); t = t.replace('Extraniera', 'Extranjera').replace('DEPÉSITO', 'DEPÓSITO').replace('1lro', '1ro')
        if any(abs(w['x'] - v['x']) < 6 and abs(w['y'] - v['y']) < 6 and v['t'] == t for v in ws): continue  # duplicada
        if t in ('—', '-—-', '—-', '-—', '—_', '–'): t = '–'
        if t.startswith('_') and len(t) > 1: t = t.lstrip('_')
        w = dict(w); w['t'] = t
        if corr: w['corr'] = 1
        if t in SIMB: w['sim'] = 1
        ws.append(w)
    # fuera restos de subrayado y palabras repetidas por celdas anidadas
    def guion(w):  # guion entre dos palabras de la misma línea (no resto de subrayado)
        if not re.fullmatch(r'[-–—=_~]+', w['t']) or w['w'] > 40: return False
        cy = w['y'] + w['h'] / 2
        medio = lambda v: v['y'] + 0.3 * v['h'] < cy < v['y'] + 0.8 * v['h']
        izq = [v for v in ws if v is not w and v['h'] >= 12 and 0 <= w['x'] - (v['x'] + v['w']) <= 40 and medio(v)]
        der = [v for v in ws if v is not w and v['h'] >= 12 and 0 <= v['x'] - (w['x'] + w['w']) <= 40 and medio(v)]
        return bool(izq or der)
    for w in ws:
        if w['h'] < 8 and guion(w): w['t'] = '–'; w['h'] = 8; w['y'] -= 2
    ws = [w for w in ws if w['h'] >= 8 or w.get('sim')]
    def solapa(a, b):
        x0, y0 = max(a['x'], b['x']), max(a['y'], b['y'])
        x1, y1 = min(a['x'] + a['w'], b['x'] + b['w']), min(a['y'] + a['h'], b['y'] + b['h'])
        if x1 <= x0 or y1 <= y0: return 0
        return (x1 - x0) * (y1 - y0) / min(a['w'] * a['h'], b['w'] * b['h'])
    quitar = set()
    for i in range(len(ws)):
        for j in range(i + 1, len(ws)):
            a, b = ws[i], ws[j]
            if a.get('sim') or b.get('sim') or i in quitar or j in quitar: continue
            import difflib
            parecido = difflib.SequenceMatcher(None, a['t'].lower(), b['t'].lower()).ratio() > 0.5
            if (solapa(a, b) > 0.5 and parecido) or solapa(a, b) > 0.9:
                ca = a['c'] + (100 if a.get('corr') else 0); cb = b['c'] + (100 if b.get('corr') else 0)
                quitar.add(j if ca >= cb else i)
    ws = [w for i, w in enumerate(ws) if i not in quitar]
    # viñetas partidas en pedazos (❖): se unen las que se tocan
    sims = [w for w in ws if w.get('sim')]
    resto = [w for w in ws if not w.get('sim')]
    grupos = []
    for w in sorted(sims, key=lambda w: (w['y'], w['x'])):
        for g in grupos:
            if g['t'] == w['t'] and abs(g['x'] - w['x']) < 22 and abs(g['y'] - w['y']) < 22:
                x0, y0 = min(g['x'], w['x']), min(g['y'], w['y'])
                x1, y1 = max(g['x'] + g['w'], w['x'] + w['w']), max(g['y'] + g['h'], w['y'] + w['h'])
                g.update(x=x0, y=y0, w=x1 - x0, h=y1 - y0); break
        else:
            grupos.append(dict(w))
    ws = resto + grupos
    # negrita: grosor del trazo (2 x área / perímetro de la tinta) frente a la mediana de la página
    im = cv2.imread(f'img/{k}.jpg'); B_, G_, R_ = [im[:, :, i].astype(int) for i in range(3)]
    im[(B_ - R_ > 35) & (B_ - G_ > 5)] = 255
    g_ = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    for w in ws:
        cr = g_[w['y']:w['y'] + w['h'], w['x']:w['x'] + w['w']]
        bw = (cr < 140).astype(np.uint8)
        cs, _ = cv2.findContours(bw, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        per = sum(cv2.arcLength(c, True) for c in cs)
        w['g'] = 2 * float(bw.sum()) / per if per else 0
    base = [w['g'] for w in ws if not w.get('sim') and len(w['t']) >= 4 and w['g']]
    med = statistics.median(base) if base else 2
    for w in ws:
        if not w.get('sim') and re.search(r'\w', w['t']) and w['g'] > med * 1.38: w['b'] = 1
    L = collections.OrderedDict()
    for w in ws: L.setdefault(w['k'], []).append(w)
    lineas = []
    for key, lw in L.items():
        lw.sort(key=lambda w: w['x'])
        # palabras cortas siguen a sus vecinas (evita «de», «en» sueltos en negrita)
        for i, w in enumerate(lw):
            if len(re.sub(r'\W', '', w['t'])) <= 3 and not w.get('sim'):
                vec = [v for v in (lw[i - 1] if i else None, lw[i + 1] if i + 1 < len(lw) else None) if v and not v.get('sim')]
                if vec:
                    if all(v.get('b') for v in vec): w['b'] = 1
                    elif not any(v.get('b') for v in vec): w.pop('b', None)
        clave = f"{k}|{lw[0]['x']}|{lw[0]['y']}"
        if clave in LC:
            lw = relinea(lw, LC[clave])
        lineas.append({'p': lw})
    PIE = {'p-001': ('1', 1375, 1817), 'p-081': ('76', 1345, 1820), 'p-076': ('71', 1345, 1817)}
    if k in PIE:
        n_, x_, y_ = PIE[k]
        lineas = [l for l in lineas if not (l['p'][0]['y'] > 1780 and re.search(r'101|de', ' '.join(w['t'] for w in l['p'])))]
        lineas.append({'p': [{'t': n_, 'x': x_ - 20 * (len(n_) - 1), 'y': y_, 'w': 10 * len(n_), 'h': 15, 'd': 0}, {'t': 'de', 'x': x_ + 16, 'y': y_, 'w': 19, 'h': 15, 'd': 0}, {'t': '101', 'x': x_ + 46, 'y': y_, 'w': 26, 'h': 15, 'd': 0}]})
    # número de página impreso (pie «N de 101»)
    num = ''
    for ln in lineas:
        s = ' '.join(w['t'] for w in ln['p'])
        m = re.fullmatch(r'(\d{1,3}) ?de ?101', s)
        if m and ln['p'][0]['y'] > pag['H'] * 0.85: num = f'{m.group(1)} de 101'
    final[k] = {'W': pag['W'], 'H': pag['H'], 'hb': pag['hb'], 'segs': pag['segs'], 'lineas': lineas, 'num': num,
                'blanca': not ws and not pag['hb']}
final['p-000'].update(lineas=[], segs=[], hb=0, portada=1)
json.dump(final, open('final.json', 'w'), ensure_ascii=False)
print('blancas', [k for k, v in final.items() if v['blanca']])
print('sin número', [k for k, v in final.items() if not v['num'] and v['hb']])
nums = [int(v['num'].split()[0]) for k, v in sorted(final.items()) if v['num']]
print('números', nums[:5], '...', nums[-5:], 'salto', [(a, b) for a, b in zip(nums, nums[1:]) if b != a + 1])
