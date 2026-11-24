"""Ley 1715 (texto de consulta de la Gaceta): quita la raya gris del encabezado de la primera página, el aviso
«Suscripción obligatoria · DS 690» y el rótulo «TEXTO DE CONSULTA / Gaceta Oficial... / Derechos Reservados © 2014 /
www.gacetaoficialdebolivia.gob.bo» de la última página de texto, y la última página (catálogo de ediciones de la Gaceta).
No toca el texto de la Ley. Uso: python3 -I limpiar_1715.py origen.pdf destino.pdf"""
import sys, re, pypdf
from pypdf.generic import NameObject, DecodedStreamObject, ArrayObject

src, dst = sys.argv[1], sys.argv[2]
r = pypdf.PdfReader(src)
w = pypdf.PdfWriter()
n = len(r.pages)
assert not (r.pages[-1].extract_text() or '').strip(), 'la última página no es la esperada (debería ser solo imagen)'


def datos_de(p):
    c = p['/Contents'].get_object()
    return b''.join(x.get_object().get_data() for x in c) if isinstance(c, ArrayObject) else c.get_data()


def pone(np, datos):
    s = DecodedStreamObject(); s.set_data(datos)
    np[NameObject('/Contents')] = w._add_object(s)
    np.compress_content_streams()


for i, p in enumerate(r.pages[:-1]):
    np = w.add_page(p)
    if i == 0:
        d = datos_de(p)
        partes = re.split(rb'(?= /P <</MCID \d+>> BDC)', d)
        quita = [x for x in partes if re.match(rb' /P <</MCID [01]>> BDC', x)]
        assert len(quita) == 2 and b'TJ' not in b''.join(quita), 'el encabezado no es el esperado'
        pone(np, b''.join(x for x in partes if x not in quita))
        print('página 1: quitada la raya del encabezado')
    if i == n - 2:
        d = datos_de(p)
        partes = re.split(rb'(?= /P <</MCID \d+>> BDC)', d)
        plano = lambda x: re.sub(rb'\)-?[\d.]*\(', b'', b''.join(re.findall(rb'\[(.*?)\] TJ', x)))
        assert b'Thenier' in plano(partes[1]) and b'SUSCRIPCION' in plano(partes[2]) and b'TEXTO DE CONSULTA' in plano(partes[-1])
        pone(np, b''.join(partes[:2]))
        print(f'página {i + 1}: quitados el aviso del DS 690 y el rótulo de la Gaceta')
w.add_metadata({'/Title': 'Ley 1715 del Servicio Nacional de Reforma Agraria'})
with open(dst, 'wb') as f:
    w.write(f)
print('páginas', n, '->', len(w.pages))
