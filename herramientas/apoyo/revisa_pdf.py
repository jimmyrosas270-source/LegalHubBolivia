import sys, subprocess, re, unicodedata as u
from pypdf import PdfReader
for p in sys.argv[1:]:
    r = PdfReader(p)
    enc = r.is_encrypted
    annots = {}
    js = False
    for pg in r.pages:
        for a in (pg.get('/Annots') or []):
            a = a.get_object(); st = a.get('/Subtype'); annots[st] = annots.get(st,0)+1
    root = r.trailer['/Root']
    js = '/Names' in root and '/JavaScript' in root['/Names'].get_object() or '/OpenAction' in root
    acro = '/AcroForm' in root
    uris = set()
    for pg in r.pages:
        for a in (pg.get('/Annots') or []):
            a=a.get_object(); A=a.get('/A')
            if A and '/URI' in A.get_object(): uris.add(str(A.get_object()['/URI'])[:60])
    info = subprocess.run(['pdfinfo', p], capture_output=True, text=True).stdout
    size = re.search(r'Page size:\s+(.*)', info).group(1)
    print(u.normalize('NFC', p.split('/')[-1])[:55], '| enc', enc, '| annots', annots, '| js/openaction', js, '| form', acro, '| page', size, '| uris', sorted(uris)[:4])
