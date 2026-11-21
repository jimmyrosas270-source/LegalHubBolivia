import re,json
pages=open('all.txt',encoding='utf-8').read().split('\f')
idx='\n'.join(pages[1:3])
pairs=sorted((int(a),int(b)) for a,b in re.findall(r'(\d{3})\s*\.{3,}\s*(\d+)',idx))
# build full text with page markers
out=[]
for i,(n,pp) in enumerate(pairs):
    pdfp=pp+4
    # find marker line "   n" alone on a line in that page
    found=None
    for q in range(pdfp, pdfp+2):
        m=re.search(r'^\s{20,}%d\s*$'%n, pages[q-1], re.M)
        if m: found=(q,m.start()); break
    if not found: print('NO marker',n,pdfp); continue
    out.append({'n':n,'pdf':found[0],'off':found[1]})
for i,a in enumerate(out):
    q,o=a['pdf'],a['off']
    if i+1<len(out):
        q2,o2=out[i+1]['pdf'],out[i+1]['off']
    else:
        q2,o2=len(pages),0
    txt=pages[q-1][o:] if q!=q2 else pages[q-1][o:o2]
    if q!=q2:
        for k in range(q,q2-1): txt+='\n\f\n'+pages[k]
        txt+='\n\f\n'+pages[q2-1][:o2]
    txt=re.sub(r'^[ \t]*SALA CIVIL[ \t]+Página \| \d+[ \t]*$','',txt,flags=re.M)
    a['texto']=txt
    a['pdf_fin']=q2
    L=[l.strip() for l in txt.split('\n') if l.strip()]
    a['partes_linea']=L[1]; a['proceso']=L[2]; a['distrito']=L[3] if L[3].startswith('Distrito') else ''
    a['tipo']=next((l for l in L[3:7] if l.isupper()),'')
    f=re.findall(r'Sucre,\s*(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})',txt)
    a['fecha']=f[-1] if f else ''
    pt=re.search(r'POR TANTO:(.{0,700})',re.sub(r'\s+',' ',txt))
    a['portanto']=pt.group(1) if pt else ''
    a['doctrina']=[re.sub(r'\s+',' ',x).strip() for x in re.findall(r'^\s*(III\.\d+\.?-?\s*[^\n]{3,160})',txt,re.M)]
json.dump(out,open('autos.json','w'),ensure_ascii=False,indent=1)
print(len(out))
from collections import Counter
print(Counter(a['tipo'] for a in out))
print(sum(1 for a in out if not a['fecha']), [a['n'] for a in out if not a['fecha']])

# --- refinamiento: parte del auto supremo
for a in out:
    q=a['pdf']; txt=a['texto']
    # reconstruir con marcas de página
    heads=[m for m in re.finditer(r'^[ \t]{20,}(AUTO SUPREMO|AUTO DEFINITIVO|AUTO INTERLOCUTORIO|SENTENCIA|SENTECIA|AUTO DE VISTA)\s*$',txt,re.M)]
    a['secciones']=[h.group(1) for h in heads]
    asup=[h for h in heads if h.group(1).startswith('AUTO') and h.group(1)!='AUTO DE VISTA']
    h=asup[-1] if asup else heads[-1]
    a['tipo_final']=h.group(1)
    sub=txt[h.start():]
    a['pagina_as']=q+txt[:h.start()].count('\f')
    pt=re.search(r'POR TANTO:(.{0,600})',re.sub(r'\s+',' ',sub))
    a['portanto']=pt.group(1) if pt else ''
    a['doctrina']=[re.sub(r'\s+',' ',x).strip() for x in re.findall(r'^\s*(III\.\d+\.?-?\s*[^\n]{3,200})',sub,re.M)]
json.dump(out,open('autos.json','w'),ensure_ascii=False,indent=1)
print(Counter(tuple(a['secciones']) for a in out).most_common(8))
