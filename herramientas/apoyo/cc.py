import re,sys,subprocess,functools
PDF='/home/claude/legalhubbolivia/biblioteca/pdf/civil/codigo-civil.pdf'
@functools.lru_cache(None)
def datos():
    P=subprocess.run(['pdftotext','-layout',PDF,'-'],capture_output=True,text=True).stdout.split('\f')
    full='';offs=[]
    for p in P: offs.append(len(full)); full+=p+'\n'
    pat=re.compile(r'(?m)^\s*(?:Art\.|ART\.|Artículo|ARTICULO|ARTÍCULO)\s*([0-9lI][0-9lI.]*)\s*[oº°]?\s*[-.,]*\s*(\(|[-.])?')
    idx={}
    for m in pat.finditer(full):
        n=m.group(1).replace('l','1').replace('I','1').replace('.','')
        if not n.isdigit(): continue
        n=int(n)
        if m.start()<offs[3]: continue  # preliminares
        idx.setdefault(n,[]).append(m.start())
    return full,offs,idx
def art(n,maxc=2500):
    full,offs,idx=datos()
    if n not in idx: return None
    s=idx[n][0]
    nxt=[p for k,v in idx.items() for p in v if p>s]
    e=min(nxt) if nxt else s+maxc
    pg=max(i for i,o in enumerate(offs) if o<=s)+1
    return pg, re.sub(r'\s+',' ',full[s:e])[:maxc]
if __name__=='__main__':
    if sys.argv[1]=='faltan':
        full,offs,idx=datos(); print('faltan',[n for n in range(1,1571) if n not in idx][:80], 'dup',[n for n,v in idx.items() if len(v)>1][:40])
    else:
        for a in sys.argv[1:]:
            r=art(int(a)); print(f'## art {a}:',r if r else 'NO'); print()
