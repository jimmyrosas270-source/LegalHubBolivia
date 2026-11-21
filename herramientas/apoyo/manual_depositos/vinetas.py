"""Detecta viñetas (➢ ❖ • o -) que el OCR leyó como letras sueltas y las agrupa por forma."""
import json, re, os, collections
import numpy as np, cv2
os.chdir('/home/claude/manual')
P = json.load(open('base.json'))


def lineas(pag):
    L = collections.OrderedDict()
    for w in pag['palabras']:
        L.setdefault(w['k'], []).append(w)
    return L


cand = []
for k, pag in P.items():
    L = lineas(pag)
    todas = [ws for ws in L.values()]
    for key, ws in L.items():
        ws.sort(key=lambda w: w['x'])
        w0 = ws[0]
        core = re.sub(r'[\W_]', '', w0['t'])
        corto = len(core) <= 2 and w0['w'] < 45 and w0['h'] < 45
        if not corto: continue
        if len(ws) >= 2:
            gap = ws[1]['x'] - (w0['x'] + w0['w'])
            if gap >= 16 and not re.fullmatch(r'\d+[.)]?|[a-zA-Z][.)]', w0['t']):
                cand.append((k, w0, 'ini'))
        else:
            # suelta: ¿hay texto a la derecha a la misma altura?
            cy = w0['y'] + w0['h'] / 2
            der = [w for ws2 in todas for w in ws2 if w is not w0 and w['x'] > w0['x'] + w0['w'] + 10 and abs(w['y'] + w['h'] / 2 - cy) < 18 and w['x'] - (w0['x'] + w0['w']) < 120]
            if der and not re.fullmatch(r'\d+[.)]?', w0['t']):
                cand.append((k, w0, 'sola'))
print('candidatas', len(cand))
feats = []
imgs = {}
for k, w, tipo in cand:
    if k not in imgs: imgs[k] = cv2.imread(f'img/{k}.jpg', 0)
    g = imgs[k]
    cr = g[max(0, w['y'] - 3):w['y'] + w['h'] + 3, max(0, w['x'] - 3):w['x'] + w['w'] + 3]
    cr = cv2.resize(cr, (16, 16), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    feats.append(cr.flatten())
X = np.array(feats)
K = 8
crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.01)
_, lab, cen = cv2.kmeans(X, K, None, crit, 5, cv2.KMEANS_PP_CENTERS)
lab = lab.flatten()
out = [{'k': k, 'x': w['x'], 'y': w['y'], 'w': w['w'], 'h': w['h'], 't': w['t'], 'tipo': tipo, 'g': int(g)} for (k, w, tipo), g in zip(cand, lab)]
json.dump(out, open('vinetas.json', 'w'), ensure_ascii=False)
print(collections.Counter(lab.tolist()))
# lámina: por grupo, 24 muestras
from PIL import Image, ImageDraw
H = Image.new('RGB', (24 * 50 + 60, K * 52), 'white'); d = ImageDraw.Draw(H)
for gi in range(K):
    d.text((4, gi * 52 + 18), f'G{gi}', fill='red')
    m = [o for o in out if o['g'] == gi][:24]
    for j, o in enumerate(m):
        im = Image.open(f'img/{o["k"]}.jpg').crop((o['x'] - 4, o['y'] - 4, o['x'] + o['w'] + 4, o['y'] + o['h'] + 4))
        im.thumbnail((46, 46)); H.paste(im, (40 + j * 50, gi * 52 + 3))
H.save('/tmp/vinetas.png')
