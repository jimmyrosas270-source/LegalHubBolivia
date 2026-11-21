"""OCR por zonas del manual escaneado: texto corrido (psm 3) y tablas con cuadrícula (celda por celda, psm 6).
Salida: json/p-NNN.json con palabras en coordenadas de la página (px a 200 ppp), segmentos de línea y tablas."""
import cv2, numpy as np, json, os, sys, glob
import pytesseract
from multiprocessing import Pool

os.chdir('/home/claude/manual')
OUTD = os.environ.get('OUTD', 'json'); os.makedirs(OUTD, exist_ok=True)
CFG = '--dpi 200 -c preserve_interword_spaces=1'


def limpia(im):
    B, G, R = [im[:, :, i].astype(int) for i in range(3)]
    blue = (B - R > 35) & (B - G > 5)
    im = im.copy(); im[blue] = 255
    im[:, :150] = 255
    return cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)


def comp(mask):
    n, lab, st, _ = cv2.connectedComponentsWithStats(mask)
    return [tuple(int(v) for v in st[i][:4]) for i in range(1, n)]


def cluster(vals, tol=10):
    vals = sorted(vals); out = []
    for v in vals:
        if out and v - out[-1][-1] <= tol: out[-1].append(v)
        else: out.append([v])
    return [int(round(sum(c) / len(c))) for c in out]


ESC = float(os.environ.get('ESC', '1.5'))


def datos(img, ox=0, oy=0, psm=3):
    if ESC != 1:
        img = cv2.resize(img, None, fx=ESC, fy=ESC, interpolation=cv2.INTER_CUBIC)
    d = pytesseract.image_to_data(img, lang='spa', config=f'--dpi {int(200*ESC)} -c preserve_interword_spaces=1 --psm {psm}', output_type=pytesseract.Output.DICT)
    for kk in ('left', 'top', 'width', 'height'):
        d[kk] = [int(round(v / ESC)) for v in d[kk]]
    words = []
    for i in range(len(d['text'])):
        t = d['text'][i].strip()
        if not t: continue
        words.append({'t': t, 'x': d['left'][i] + ox, 'y': d['top'][i] + oy, 'w': d['width'][i], 'h': d['height'][i],
                      'c': float(d['conf'][i]), 'k': f"{d['block_num'][i]}.{d['par_num'][i]}.{d['line_num'][i]}"})
    return words


def pagina(f):
    b = os.path.basename(f)[:-4]
    im = cv2.imread(f)
    g = limpia(im)
    H, W = g.shape
    bw = (g < 150).astype(np.uint8)
    hk = cv2.morphologyEx(bw, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (60, 1)))
    vk = cv2.morphologyEx(bw, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40)))
    # cabecera
    LL = sorted((y, y + h) for x, y, w, h in comp(hk) if w > 0.3 * W)
    tops = [y for y, _ in LL if y < 170]
    hb = 0
    if tops:
        t = tops[0]; c = [yb for y, yb in LL if t + 150 <= y <= t + 235]
        hb = c[0] if c else t + 195
    H_ = [s for s in comp(hk) if s[1] > hb + 3]
    V_ = [s for s in comp(vk) if s[1] > hb + 3 or s[1] + s[3] > hb + 20]
    V_ = [(x, max(y, hb + 4), w, h - max(0, hb + 4 - y)) for x, y, w, h in V_]
    lines = cv2.dilate(((hk | vk) > 0).astype(np.uint8), np.ones((5, 5), np.uint8))
    lines[:hb + 4] = 0
    tablas = []
    for x, y, w, h in comp(lines):
        if w < 150 or h < 30: continue
        hs = [s for s in H_ if s[0] >= x - 6 and s[0] + s[2] <= x + w + 6 and y - 6 <= s[1] <= y + h + 6]
        vs = [s for s in V_ if s[0] >= x - 6 and s[0] + s[2] <= x + w + 6 and s[1] >= y - 6 and s[1] + s[3] <= y + h + 6]
        if len(hs) < 2 or len(vs) < 2: continue
        ys = cluster([s[1] + s[3] // 2 for s in hs]); xs = cluster([s[0] + s[2] // 2 for s in vs])
        if len(ys) < 2 or len(xs) < 2: continue
        R, Cn = len(ys) - 1, len(xs) - 1
        par = list(range(R * Cn))
        def fnd(i):
            while par[i] != i: par[i] = par[par[i]]; i = par[i]
            return i
        def tiene_v(xv, ya, yb):  # hay línea vertical en xv que cubre el centro del tramo ya-yb
            ym = (ya + yb) / 2
            return any(abs(s[0] + s[2] / 2 - xv) < 12 and s[1] - 8 <= ym <= s[1] + s[3] + 8 for s in vs)
        def tiene_h(yh, xa, xb):
            xm = (xa + xb) / 2
            return any(abs(s[1] + s[3] / 2 - yh) < 12 and s[0] - 8 <= xm <= s[0] + s[2] + 8 for s in hs)
        for i in range(R):
            for j in range(Cn):
                if j + 1 < Cn and not tiene_v(xs[j + 1], ys[i], ys[i + 1]): par[fnd(i * Cn + j + 1)] = fnd(i * Cn + j)
                if i + 1 < R and not tiene_h(ys[i + 1], xs[j], xs[j + 1]): par[fnd((i + 1) * Cn + j)] = fnd(i * Cn + j)
        grupos = {}
        for i in range(R):
            for j in range(Cn):
                grupos.setdefault(fnd(i * Cn + j), []).append((i, j))
        celdas = []
        for gi, cs in grupos.items():
            x0 = xs[min(j for _, j in cs)]; x1 = xs[max(j for _, j in cs) + 1]
            y0 = ys[min(i for i, _ in cs)]; y1 = ys[max(i for i, _ in cs) + 1]
            celdas.append([x0, y0, x1, y1, min(i for i, _ in cs), min(j for _, j in cs)])
        celdas.sort(key=lambda c: (c[4], c[5]))
        tablas.append({'bbox': [x, y, x + w, y + h], 'celdas': celdas})
    # texto fuera de tablas
    g2 = g.copy()
    g2[(hk | vk) > 0] = 255
    g2[:hb + 4] = 255
    for t in tablas:
        x0, y0, x1, y1 = t['bbox']; g2[max(0, y0 - 3):y1 + 3, max(0, x0 - 3):x1 + 3] = 255
    palabras = datos(g2)
    for w in palabras: w['k'] = 'p' + w['k']
    for ti, t in enumerate(tablas):
        for ci, (x0, y0, x1, y1, _, _) in enumerate(t['celdas']):
            cr = g[y0 + 4:y1 - 3, x0 + 4:x1 - 3].copy()
            if cr.size == 0 or (cr < 150).sum() < 15: continue
            m = ((hk | vk)[y0 + 4:y1 - 3, x0 + 4:x1 - 3] > 0); cr[m] = 255
            cr = cv2.copyMakeBorder(cr, 12, 12, 12, 12, cv2.BORDER_CONSTANT, value=255)
            ws = datos(cr, x0 + 4 - 12, y0 + 4 - 12, psm=6)
            for w in ws: w['k'] = f't{ti}.c{ci}.' + w['k']
            palabras += ws
    # grosor de trazo (negrita): tinta / área
    for w in palabras:
        sub = bw[w['y']:w['y'] + w['h'], w['x']:w['x'] + w['w']]
        w['d'] = round(float(sub.mean()) if sub.size else 0, 3)
    segs = [['h'] + list(s) for s in H_] + [['v'] + list(s) for s in V_]
    json.dump({'hb': hb, 'W': W, 'H': H, 'palabras': palabras, 'tablas': tablas, 'segs': segs}, open(f'{OUTD}/{b}.json', 'w'), ensure_ascii=False)
    return b, len(palabras), len(tablas)


if __name__ == '__main__':
    fs = sorted(glob.glob('img/p-*.jpg'))
    if len(sys.argv) > 1: fs = [f for f in fs if any(a in f for a in sys.argv[1:])]
    with Pool(2) as p:
        for r in p.imap_unordered(pagina, fs): print(*r, flush=True)
