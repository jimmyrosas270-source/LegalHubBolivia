"""Compone el PDF nuevo con texto real a partir de json/ (OCR por zonas) + correcciones.json.
Cada página del escaneado = una página del PDF nuevo, con el texto en la misma posición."""
import json, os, re, glob, statistics, io
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import Color, black
from PIL import Image

os.chdir('/home/claude/manual')
FD = '/usr/share/fonts/truetype/'
pdfmetrics.registerFont(TTFont('R', FD + 'liberation/LiberationSans-Regular.ttf'))
pdfmetrics.registerFont(TTFont('B', FD + 'liberation/LiberationSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('HB', FD + 'dejavu/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('S', FD + 'dejavu/DejaVuSans.ttf'))  # viñetas y símbolos
PW, PH = 597.6, 756.0
GRIS = Color(0.45, 0.45, 0.45)

FINAL = json.load(open('final.json'))  # {pagina: {'lineas': [...], 'segs': [...], 'hb':..., 'W':..., 'H':..., 'num': 'N de 101'}}
ALTO = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789bdfhklt()/|[]{}!?¿¡%&$#@ÑÁÉÍÓÚÜ')
DESC = set('gjpqyQ,;()[]{}|')


def medidas(t):
    top = 0.53
    if any(c in ALTO for c in t): top = 0.73
    if any(c in 'ÁÉÍÓÚÑÜ' for c in t): top = 0.90
    if any(c in 'áéíóúñüi¡' for c in t) and top < 0.73: top = 0.73
    bot = -0.21 if any(c in DESC for c in t) else 0.0
    return top, bot


def logo():
    im = Image.open('img/p-001.jpg').crop((205, 100, 405, 288)).convert('RGB')
    b = io.BytesIO(); im.save(b, 'JPEG', quality=70); b.seek(0)
    return b


def escudo():
    im = Image.open('img/p-000.jpg').convert('RGB')
    W, H = im.size
    c = im.crop((int(W * 0.37), int(H * 0.31), int(W * 0.62), int(H * 0.48)))
    c.thumbnail((400, 400))
    b = io.BytesIO(); c.save(b, 'JPEG', quality=72); b.seek(0)
    return b


from reportlab.lib.utils import ImageReader
LOGO = ImageReader(logo())


def cabecera(c, num):
    # plantilla de la cabecera (medida en el escaneado a 200 ppp: x 200-1520, y 90-288)
    s = 0.36
    X0, X1, Y0, Y1 = 200 * s, 1520 * s, PH - 90 * s, PH - 288 * s
    xa, xb, xm = 412 * s, 1272 * s, 1394 * s
    c.setLineWidth(0.7); c.setStrokeColor(black)
    c.rect(X0, Y1, X1 - X0, Y0 - Y1)
    c.line(xa, Y0, xa, Y1); c.line(xb, Y0, xb, Y1)
    ys = [PH - 137 * s, PH - 184 * s, PH - 226 * s]
    for y in ys: c.line(xb, y, X1, y)
    c.line(xm, ys[1], xm, Y1)
    c.drawImage(LOGO, X0 + 4, Y1 + 3, width=xa - X0 - 8, height=Y0 - Y1 - 6, preserveAspectRatio=True)
    c.setFont('HB', 9.6); c.drawCentredString((xa + xb) / 2, (Y0 + Y1) / 2 - 3.5, 'MANUAL DE PROCESOS DE DEPOSITOS JUDICIALES')
    c.setFont('HB', 5.6); c.drawCentredString((xb + X1) / 2, (Y0 + ys[0]) / 2 - 2, 'VERSION:')
    c.drawCentredString((xb + X1) / 2, (ys[0] + ys[1]) / 2 - 2, '1/2021')
    c.drawCentredString((xb + xm) / 2, (ys[1] + ys[2]) / 2 - 2, 'Gestión')
    c.drawCentredString((xm + X1) / 2, (ys[1] + ys[2]) / 2 + 1, 'Número de')
    c.drawCentredString((xm + X1) / 2, (ys[1] + ys[2]) / 2 - 5, 'Páginas')
    c.setFont('S', 5.6)
    c.drawCentredString((xb + xm) / 2, (ys[2] + Y1) / 2 - 2, '2021')
    if num: c.drawCentredString((xm + X1) / 2, (ys[2] + Y1) / 2 - 2, num)


def portada(c, pag):
    W, H = pag['W'], pag['H']
    sx, sy = PW / W, PH / H
    x0, y0, x1, y1 = 231, 227, 1439, 1838
    c.setLineWidth(4); c.roundRect((x0 + 9) * sx, PH - (y1 + 9) * sy, (x1 - x0) * sx, (y1 - y0) * sy, 14)
    c.setFillColor(Color(1, 1, 1)); c.setLineWidth(1.1)
    c.roundRect(x0 * sx, PH - y1 * sy, (x1 - x0) * sx, (y1 - y0) * sy, 14, fill=1)
    c.setFillColor(black)
    im = ImageReader(escudo())
    c.drawImage(im, W * 0.37 * sx, PH - H * 0.48 * sy, width=W * 0.25 * sx, height=H * 0.17 * sy, preserveAspectRatio=True)
    cx = 834 * sx
    for y, t, tam in ((430, 'DIRECCIÓN ADMINISTRATIVA Y', 15.5), (487, 'FINANCIERA', 15.5), (1124, 'ÓRGANO JUDICIAL', 15.5),
                      (1214, 'ESTADO PLURINACIONAL DE BOLIVIA', 15.5), (1386, 'MANUAL DE PROCESOS DE DEPÓSITOS', 15.5),
                      (1443, 'JUDICIALES', 15.5), (1600, 'GESTIÓN 2021', 12.5), (1645, 'Sucre-Bolivia', 12.5)):
        c.setFont('HB', tam); c.drawCentredString(cx, PH - y * sy - tam * 0.36, t)


FIGURAS = {'p-001': (320, 1385, 1312, 1800)}  # flujograma: va como imagen; su texto, invisible (se puede buscar y copiar)


def figura(c, k, caja, sx, sy):
    import cv2, numpy as np
    x0, y0, x1, y1 = caja
    im = cv2.imread(f'img/{k}.jpg')
    B, G, R = [im[:, :, i].astype(int) for i in range(3)]
    im[(B - R > 35) & (B - G > 5)] = 255
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)[y0:y1, x0:x1]
    b = io.BytesIO(); Image.fromarray(g).save(b, 'JPEG', quality=60); b.seek(0)
    c.drawImage(ImageReader(b), x0 * sx, PH - y1 * sy, width=(x1 - x0) * sx, height=(y1 - y0) * sy)


def dentro(caja, x, y):
    return caja and caja[0] <= x <= caja[2] and caja[1] <= y <= caja[3]


def pagina(c, k, pag):
    W, H = pag['W'], pag['H']
    sx, sy = PW / W, PH / H
    if pag.get('blanca'):
        c.setFont('R', 8); c.setFillColor(GRIS)
        c.drawCentredString(PW / 2, PH / 2, '[Página en blanco en el escaneado]')
        c.setFillColor(black); return
    if pag.get('hb'):
        cabecera(c, pag.get('num'))
    if pag.get('portada'):
        portada(c, pag)
    caja = FIGURAS.get(k)
    if caja: figura(c, k, caja, sx, sy)
    c.setLineWidth(0.6)
    for kind, x, y, w, h in pag['segs']:
        if dentro(caja, x, y): continue
        if kind == 'h' and w > 25: c.line(x * sx, PH - (y + h / 2) * sy, (x + w) * sx, PH - (y + h / 2) * sy)
        if kind == 'v' and h > 25: c.line((x + w / 2) * sx, PH - y * sy, (x + w / 2) * sx, PH - (y + h) * sy)
    def tam_linea(ws):
        tams = []
        for w in ws:
            if w.get('sim'): continue
            top, bot = medidas(w['t'])
            th = w['h'] * sy / (top - bot)
            an = pdfmetrics.stringWidth(w['t'], 'B' if w.get('b') else 'R', 1)
            if an > 0 and len(w['t']) >= 3: th = min(th, 1.2 * w['w'] * sx / an)  # el ancho no se infla con subrayados
            tams.append(th)
        return statistics.median(tams) if tams else None
    todos = [t for t in (tam_linea(l['p']) for l in pag['lineas'] if len(l['p']) >= 2) if t]
    med = statistics.median(todos) if todos else 11
    for ln in pag['lineas']:
        ws = ln['p']
        if not ws: continue
        bases = []
        size = tam_linea(ws)
        if size is None:  # línea solo con una viñeta
            w = ws[0]; size = med * 0.9
            to = c.beginText(w['x'] * sx, PH - (w['y'] + w['h']) * sy); to.setFont('S', size); to.textOut(w['t']); c.drawText(to)
            continue
        corto = len(''.join(w['t'] for w in ws)) <= 4
        if 0.78 * med <= size <= 1.28 * med or (corto and 0.6 * med <= size <= 1.6 * med): size = med
        size = max(5.5, min(size, 20))
        for w in ws:
            if w.get('sim'): continue
            top, bot = medidas(w['t'])
            esperado = (top - bot) * size / sy
            if w['h'] > 1.3 * esperado:  # caja inflada por la línea de abajo: se mide desde arriba
                bases.append(w['y'] * sy + top * size)
            else:
                bases.append((w['y'] + w['h']) * sy + bot * size)
        base = PH - statistics.median(bases)
        orden = sorted(ws, key=lambda w: w['x'])
        for i, w in enumerate(orden):  # una caja inflada no puede invadir la palabra siguiente
            if i + 1 < len(orden):
                lim = orden[i + 1]['x'] - w['x'] - 0.28 * size / sx
                if lim > 0 and w['w'] > lim: w = dict(w, w=lim); orden[i] = w
        ws = orden
        for w in ws:
            fuente = 'B' if w.get('b') else 'R'
            t = w['t']
            if w.get('sim'):
                to = c.beginText(w['x'] * sx, base); to.setFont('S', size * 0.9); to.textOut(t); c.drawText(to); continue
            ancho = pdfmetrics.stringWidth(t, fuente, size)
            esc = 100.0
            if ancho > 0 and not w.get('sim'):
                esc = max(72, min(128, w['w'] * sx / ancho * 100))
            to = c.beginText(w['x'] * sx, base)
            to.setFont(fuente, size); to.setHorizScale(esc)
            if dentro(caja, w['x'], w['y']): to.setTextRenderMode(3)
            to.textOut(t)
            c.drawText(to)


def main(salida='manual.pdf'):
    c = canvas.Canvas(salida, pagesize=(PW, PH), pageCompression=1)
    c.setTitle('Manual de Procesos de Depósitos Judiciales (transcripción)')
    c.setAuthor('Órgano Judicial · Dirección Administrativa y Financiera (texto); transcripción: LegalHubBolivia')
    c.setSubject('Transcripción del escaneado oficial, gestión 2021. No es la copia oficial.')
    for k in sorted(FINAL):
        pagina(c, k, FINAL[k])
        c.showPage()
    c.save()


if __name__ == '__main__':
    import sys
    main(*(sys.argv[1:2] or []))
