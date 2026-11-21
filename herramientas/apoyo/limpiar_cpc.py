"""CPC (Ley 439, texto de consulta de la Gaceta): quita el rótulo «TEXTO DE CONSULTA / Gaceta Oficial... / Derechos
Reservados © 2021» y la raya gris de la esquina superior de la primera página, el recuadro «Suscripción obligatoria
(DS 690)» al pie de la última página de texto, y quita la última página (portada del manual de la Gaceta). No toca el resto del contenido."""
import sys, re, pypdf
from pypdf.generic import NameObject, DecodedStreamObject
src, dst = sys.argv[1], sys.argv[2]
r = pypdf.PdfReader(src)
w = pypdf.PdfWriter()
n = len(r.pages)
ultimo = r.pages[-1].extract_text() or ''
assert 'MANÜA' in ultimo or 'Edición Oficial' in ultimo or 'Edicióñ' in ultimo, 'la última página no es la esperada'
for i, p in enumerate(r.pages[:-1]):
    np = w.add_page(p)
    if i == 0:
        datos = b''.join(c.get_object().get_data() for c in p['/Contents'])
        antes = len(datos)
        # raya gris del encabezado (dos rectángulos y dos remates), hasta volver al color negro
        datos, k1 = re.subn(rb'\.6039 \.6039 \.6039 RG \.6039 \.6039 \.6039 rg\n/G3 gs\n8 70 725 1 re\nf\n.*?(?=0 0 0 RG 0 0 0 rg\nBT)', b'/G3 gs\n', datos, count=1, flags=re.S)
        # los tres renglones del rótulo (MCID 0, 1 y 2)
        datos, k2 = re.subn(rb'BT\n/P <</MCID [012] >>BDC\n.*?EMC\nET\n', b'', datos, count=3, flags=re.S)
        assert (k1, k2) == (1, 3), (k1, k2)
        s = DecodedStreamObject(); s.set_data(datos)
        np[NameObject('/Contents')] = w._add_object(s)
        np.compress_content_streams()
        print('página 1: quitados', antes - len(datos), 'bytes del rótulo')
    if i == n - 2:
        # recuadro final «SUSCRIPCIÓN OBLIGATORIA · Decreto Supremo Nº 690» (aviso de la Gaceta, no es parte del Código)
        c = p['/Contents'].get_object()
        datos = b''.join(x.get_object().get_data() for x in c) if isinstance(c, pypdf.generic.ArrayObject) else c.get_data()
        inicio = datos.find(b'q\n118.75 118.75 2314.0625 3064.0625 re\nW* n\nq\n3.125')
        assert inicio > 0 and b'110614 721 1 re' in datos[:inicio]
        datos = datos[:datos.find(b'\n') + 1] + datos[inicio:]
        datos, k = re.subn(rb'BT\n/P <</MCID 3[0-7] >>BDC\n.*?EMC\nET\n', b'', datos, flags=re.S)
        assert k == 8, k
        s = DecodedStreamObject(); s.set_data(datos)
        np[NameObject('/Contents')] = w._add_object(s)
        np.compress_content_streams()
        print('penúltima página: quitado el recuadro del DS 690')
w.add_metadata({'/Title': 'Código Procesal Civil (Ley 439)'})
with open(dst, 'wb') as f:
    w.write(f)
print('páginas', n, '->', len(w.pages))
