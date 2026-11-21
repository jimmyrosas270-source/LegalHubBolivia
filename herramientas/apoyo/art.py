import sys,re,subprocess,functools,os,json
B='/home/claude/legalhubbolivia/biblioteca/pdf/'
@functools.lru_cache(None)
def paginas(pdf):
    cache='/home/claude/research/'+re.sub(r'\W','_',pdf)+os.environ.get('RAW','')+'.json'
    if os.path.exists(cache): return json.load(open(cache))
    t=subprocess.run(['pdftotext']+([] if os.environ.get('RAW') else ['-layout'])+[pdf,'-'],capture_output=True,text=True).stdout.split('\f')
    json.dump(t,open(cache,'w')); return t
def art(pdf,n,suf='',maxc=1800):
    P=paginas(pdf); full=''; offs=[]
    for i,p in enumerate(P): offs.append(len(full)); full+=p+'\n'
    pat=re.compile(r'(?im)^\s*ART[ÍI]CULO\.?\s+'+str(n)+r'\s*[°º]?\s*'+(suf+r'\b' if suf else r'(?!\s*(bis|ter|quater))')+r'[^\n]*')
    m=pat.search(full)
    if not m: return None
    nxt=re.compile(r'(?im)^\s*ART[ÍI]CULO\.?\s+\d+').search(full,m.end())
    txt=full[m.start(): nxt.start() if nxt else m.start()+maxc]
    pg=max(i for i,o in enumerate(offs) if o<=m.start())+1
    return pg, re.sub(r'\s+',' ',txt)[:maxc]
if __name__=='__main__':
    pdf=sys.argv[1] if sys.argv[1].startswith('/') else B+sys.argv[1]
    for a in sys.argv[2:]:
        n,_,suf=a.partition(':')
        r=art(pdf,n,suf)
        print(f'## art {a}:', r if r else 'NO ENCONTRADO'); print()
