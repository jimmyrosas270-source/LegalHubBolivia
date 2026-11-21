import sys,re,html,os
B='/home/claude/legalhubbolivia/salida/leyes/'
def art(ruta,n,maxc=1500):
    p=os.path.join(B,ruta,f'articulo-{n}','index.html')
    if not os.path.exists(p): return None
    s=open(p).read()
    m=re.search(r'<article.*?</article>',s,re.S)
    t=re.sub(r'<[^>]+>',' ',m.group(0) if m else s); t=html.unescape(re.sub(r'\s+',' ',t))
    return t[:maxc]
if __name__=='__main__':
    ruta=sys.argv[1]
    for a in sys.argv[2:]: print('##',a,art(ruta,a)); print()
