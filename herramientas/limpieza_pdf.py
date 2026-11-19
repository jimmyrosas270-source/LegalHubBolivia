# -*- coding: utf-8 -*-
"""Limpieza de PDF al publicar (se ejecuta dentro de construir.py con exec).

- Quita hipervínculos y resaltados o notas de lector. El texto no cambia.
  Los enlaces internos (a otra página del mismo PDF, como los de un índice) se conservan.
- Si algún enlace apuntaba a una página que no es oficial del Estado (LexiVox,
  InfoLeyes, «javascript:», etc.), además pone en negro el texto azul de esos
  enlaces, quita su subrayado y quita los iconos de barra de herramientas del
  sitio web (imágenes de menos de 40 px).
"""
import re as _re

OFICIALES = _re.compile(r'^(https?://)?([a-z0-9-]+\.)*(gob\.bo|tcpbolivia\.bo|tsj\.bo|organojudicial\.gob\.bo|oep\.org\.bo|asfi\.gob\.bo)(/|$)', _re.I)
QUITAR = ('/Link', '/Highlight', '/Popup')


def _interno(a):
    """Enlace a otra página del mismo PDF (por ejemplo, el índice de una revista): se conserva."""
    if a.get('/Subtype') != '/Link':
        return False
    act = a.get('/A')
    if act is None:
        return '/Dest' in a
    return str(act.get_object().get('/S')) == '/GoTo'


def _uri(a):
    act = a.get('/A')
    if not act:
        return ''
    act = act.get_object()
    return str(act.get('/URI') or act.get('/JS') or act.get('/S') or '')


def _azul(ops, NameObject):
    v = [float(x) for x in ops if not isinstance(x, NameObject)]
    return len(v) == 3 and v[0] < .2 and v[2] > .6 and v[2] - v[0] > .4


def _sin_azul(w, pypdf):
    from pypdf.generic import ContentStream, NameObject, FloatObject, ArrayObject
    negro = lambda ops: ArrayObject([FloatObject(0)] * 3 + [x for x in ops if isinstance(x, NameObject)])
    for pg in w.pages:
        xo = (pg.get('/Resources') or {}).get('/XObject') or {}
        chicas = {k for k, v in xo.items() if v.get_object().get('/Subtype') == '/Image' and int(v.get_object().get('/Width', 999)) < 40}
        cs = ContentStream(pg.get_contents(), w)
        fill = stroke = False
        pila, nuevas = [], []
        for ops, op in cs.operations:
            if op == b'q':
                pila.append((fill, stroke))
            elif op == b'Q':
                fill, stroke = pila.pop() if pila else (False, False)
            elif op in (b'rg', b'sc', b'scn'):
                fill = _azul(ops, NameObject)
                if fill:
                    ops = negro(ops)
            elif op in (b'RG', b'SC', b'SCN'):
                stroke = _azul(ops, NameObject)
                if stroke:
                    ops = negro(ops)
            elif op in (b'g', b'k'):
                fill = False
            elif op in (b'G', b'K'):
                stroke = False
            elif (op in (b'S', b's') and stroke) or (op in (b'f', b'F', b'f*') and fill) or (op in (b'B', b'B*', b'b', b'b*') and (fill or stroke)):
                op = b'n'
            elif op == b'Do' and ops and ops[0] in chicas:
                continue
            nuevas.append((ops, op))
        cs.operations = nuevas
        pg.replace_contents(cs)


def quitar_enlaces(origen, destino):
    """Copia el PDF limpio en destino. Devuelve False si no había nada que limpiar
    (o si pypdf no está instalado): entonces el PDF se copia tal cual."""
    try:
        import pypdf
        from pypdf.generic import NameObject, ArrayObject
    except ImportError:
        return False
    try:
        r = pypdf.PdfReader(origen)
        anots = [a.get_object() for pg in r.pages for a in (pg.get('/Annots') or [])]
        anots = [a for a in anots if a.get('/Subtype') in QUITAR and not _interno(a)]
        if not anots:
            return False
        no_oficial = any(a.get('/Subtype') == '/Link' and _uri(a) and not OFICIALES.match(_uri(a)) for a in anots)
        antes = [''.join((p.extract_text() or '').split()) for p in r.pages]
        w = pypdf.PdfWriter(clone_from=r)
        for pg in w.pages:
            an = pg.get('/Annots')
            if an:
                quedan = ArrayObject([a for a in an.get_object() if a.get_object().get('/Subtype') not in QUITAR or _interno(a.get_object())])
                if quedan:
                    pg[NameObject('/Annots')] = quedan
                else:
                    del pg['/Annots']
        if no_oficial:
            _sin_azul(w, pypdf)
        with open(destino, 'wb') as o:
            w.write(o)
        despues = [''.join((p.extract_text() or '').split()) for p in pypdf.PdfReader(destino).pages]
        if antes != despues:
            AVISOS.append(f'«{os.path.basename(origen)}»: la limpieza cambiaba el texto; se publica tal cual.')
            return False
        AVISOS.append(f'«{os.path.basename(origen)}»: se quitaron hipervínculos o resaltados al publicarlo'
                      + (' y las marcas de una página web no oficial' if no_oficial else '') + ' (el texto no cambia).')
        return True
    except Exception as e:
        AVISOS.append(f'No se pudo limpiar «{os.path.basename(origen)}»: {e}. Se publica tal cual.')
        return False
