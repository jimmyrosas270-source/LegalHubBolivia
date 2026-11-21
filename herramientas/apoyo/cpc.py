import re,sys,subprocess,functools
PDF='/home/claude/legalhubbolivia/biblioteca/pdf/procesal-civil/ley-439-codigo-procesal-civil.pdf'
@functools.lru_cache(None)
def datos():
    P=subprocess.run(['pdftotext','-layout',PDF,'-'],capture_output=True,text=True).stdout.split('\f')
    full='';offs=[]
    for p in P: offs.append(len(full)); full+=p+'\n'
    pat=re.compile(r'(?m)^\s*ART[ÍI]CULO\s+(\d+)\.?\s*\(')
    idx={}
    for m in pat.finditer(full):
        idx.setdefault(int(m.group(1)),[]).append(m.start())
    return full,offs,idx
def art(n,maxc=3000):
    full,offs,idx=datos()
    if n not in idx: return None
    s=idx[n][0]
    nxt=[p for v in idx.values() for p in v if p>s]
    e=min(nxt) if nxt else s+maxc
    pg=max(i for i,o in enumerate(offs) if o<=s)+1
    return pg, re.sub(r'\s+',' ',full[s:e])[:maxc]
if __name__=='__main__':
    if sys.argv[1]=='titulos':
        full,offs,idx=datos()
        a,b=int(sys.argv[2]),int(sys.argv[3])
        for n in range(a,b+1):
            r=art(n,250)
            if r:
                m=re.match(r'.{0,20}?\(([^)]*)\)',r[1]); print(n,r[0],m.group(1) if m else '?')
            else: print(n,'NO')
    elif sys.argv[1]=='faltan':
        full,offs,idx=datos(); print(max(idx),[n for n in range(1,max(idx)+1) if n not in idx])
    else:
        for a in sys.argv[1:]:
            r=art(int(a)); print(f'## art {a}:',r if r else 'NO'); print()
