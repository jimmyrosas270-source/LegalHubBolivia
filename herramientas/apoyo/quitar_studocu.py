"""Quita la marca de Studocu de un PDF: portada añadida, pie (QR, logo, «Downloaded by…»),
texto invisible lOMoARcPSD y enlaces a studocu.com. No toca el contenido original de cada página."""
import sys, re, pypdf
from pypdf.generic import ArrayObject, DecodedStreamObject, NameObject, DictionaryObject
src, dst = sys.argv[1], sys.argv[2]
r = pypdf.PdfReader(src)
w = pypdf.PdfWriter()
for i, p in enumerate(r.pages):
    txt0 = p.extract_text() or ''
    if i == 0 and 'Studocu' in txt0 and 'Scan to open' in txt0:
        continue  # portada de Studocu
    c = p['/Contents']
    assert len(c) == 3, i
    ov = c[2].get_object().get_data()
    assert ov.startswith(b' Q') and b'Studocu' in ov, i
    orig = c[1].get_object()
    np = w.add_page(p)
    data = orig.get_data()
    nuevo = DecodedStreamObject(); nuevo.set_data(b' q ' + data + b' Q ')
    np[NameObject('/Contents')] = w._add_object(nuevo)
    usados = set(re.findall(rb'/([A-Za-z0-9_.+-]+)\s+(?:Do|gs)\b', data)) | set(re.findall(rb'/([A-Za-z0-9_.+-]+)\s+[-\d.]+\s+Tf\b', data))
    viejo = np['/Resources'].get_object()
    res = DictionaryObject({k: v for k, v in viejo.items()})
    for cat in ('/XObject', '/Font', '/ExtGState'):
        if cat in res:
            d = res[cat].get_object()
            res[NameObject(cat)] = DictionaryObject({k: v for k, v in d.items() if k[1:].encode() in usados})
    np[NameObject('/Resources')] = res
    if '/Annots' in np:
        keep = ArrayObject()
        for a in np['/Annots']:
            ao = a.get_object(); A = ao.get('/A')
            uri = str(A.get_object().get('/URI', '')) if A else ''
            if 'studocu' in uri.lower():
                continue
            keep.append(a)
        np[NameObject('/Annots')] = keep
for pg in w.pages:
    pg.compress_content_streams()
w.add_metadata({'/Title': 'Código Civil', '/Author': '', '/Creator': '', '/Producer': ''})
with open(dst, 'wb') as f:
    w.write(f)
print('páginas', len(w.pages))
