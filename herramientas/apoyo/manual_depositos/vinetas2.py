import json, numpy as np, cv2, collections
from PIL import Image, ImageDraw
V=json.load(open('vinetas.json'))
imgs={}
def feat(o):
    if o['k'] not in imgs: imgs[o['k']]=cv2.imread(f"img/{o['k']}.jpg",0)
    g=imgs[o['k']]
    cr=g[max(0,o['y']-2):o['y']+o['h']+2, max(0,o['x']-2):o['x']+o['w']+2]
    _,bw=cv2.threshold(cr,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    ys,xs=np.nonzero(bw)
    if len(xs)==0: return None, 0
    bw=bw[ys.min():ys.max()+1, xs.min():xs.max()+1]
    ar=bw.shape[1]/bw.shape[0]
    f=cv2.resize(bw,(16,16),interpolation=cv2.INTER_AREA).astype(np.float32).flatten()
    f-=f.mean(); n=np.linalg.norm(f); 
    return (f/n if n else f), ar
# prototipos: índice en cada grupo según la lámina
def ej(g,i): return [o for o in V if o['g']==g][i]
PROTO={'✓':ej(0,0),'●':ej(2,0),'■':ej(2,12),'❖':ej(3,1),'○':ej(5,1),'➢':ej(7,0)}
PF={k:feat(o) for k,o in PROTO.items()}
for o in V:
    f,ar=feat(o)
    if f is None: o['v']=None; continue
    best=max(PF, key=lambda k: float(f@PF[k][0]))
    sc=float(f@PF[best][0]); arp=PF[best][1]
    o['v']=best if ((sc>0.6) or (sc>0.42 and best in ('❖','■','✓'))) and 0.55<ar/arp<1.8 and o['h']<40 else None
    o['sc']=round(sc,2)
json.dump(V,open('vinetas.json','w'),ensure_ascii=False)
print(collections.Counter(o['v'] for o in V))
cls=[c for c in PROTO]+[None]
filas=[]
for c in cls:
    m=[o for o in V if o['v']==c]
    for i in range(0,len(m),60): filas.append((c,m[i:i+60]))
H=Image.new('RGB',(60*22+40,len(filas)*24),'white');d=ImageDraw.Draw(H)
for r,(c,m) in enumerate(filas):
    d.text((2,r*24+6),str(c)[:1] if c else 'N',fill='red')
    for j,o in enumerate(m):
        im=Image.open(f"img/{o['k']}.jpg").crop((o['x']-2,o['y']-2,o['x']+o['w']+2,o['y']+o['h']+2)); im.thumbnail((20,20)); H.paste(im,(30+j*22,r*24+2))
H.save('/tmp/v2.png'); print(H.size)
