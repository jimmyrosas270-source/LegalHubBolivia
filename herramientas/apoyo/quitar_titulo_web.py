"""Quita de la primera página el título grande (24 pt) que pone una página web de recopilación de normas encima del
texto de la ley («Bolivia: Ley de ..., fecha») y sube el resto de la página para que no quede un hueco. No toca el
texto de la norma. Uso: python3 -I quitar_titulo_web.py origen.pdf destino.pdf"""
import sys, re, pypdf
from pypdf.generic import NameObject, DecodedStreamObject, ArrayObject

src, dst = sys.argv[1], sys.argv[2]
r = pypdf.PdfReader(src)
w = pypdf.PdfWriter()
for i, p in enumerate(r.pages):
    np = w.add_page(p)
    if i:
        continue
    c = p['/Contents'].get_object()
    d = b''.join(x.get_object().get_data() for x in c) if isinstance(c, ArrayObject) else c.get_data()
    bloques = re.split(rb'(?<=\nQ)(?=\s)', d)
    titulo = [b for b in bloques if re.search(rb'/F\d+ 24 Tf', b)]
    assert 5 <= len(titulo) <= 15, len(titulo)
    ys_t = [float(y) for b in titulo for y in re.findall(rb'1 0 0 1 [\d.]+ ([\d.]+) Tm', b)]
    resto = [b for b in bloques if b not in titulo]
    ys_r = [float(y) for b in resto for y in re.findall(rb'1 0 0 1 [\d.]+ ([\d.]+) Tm', b)]
    sube = max(ys_t) - max(ys_r)
    assert 0 < sube < 400, sube
    nuevo = b''.join(resto)
    # se conserva la marca de contenido inicial (BDC) que abría el primer bloque
    if titulo[0] is bloques[0]:
        m = re.match(rb'\s*/\w+ <<.*?>> BDC', bloques[0], re.S)
        nuevo = (m.group(0) if m else b'') + nuevo
    nuevo = b'q\n1 0 0 1 0 %.2f cm\n' % sube + nuevo + b'\nQ\n'
    s = DecodedStreamObject(); s.set_data(nuevo)
    np[NameObject('/Contents')] = w._add_object(s)
    np.compress_content_streams()
    print(f'página 1: quitado el título web ({len(titulo)} renglones); el texto sube {sube:.1f} pt')
with open(dst, 'wb') as f:
    w.write(f)
