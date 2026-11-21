import json,re,difflib,glob,collections
F=json.load(open('final.json'))
out=[]
for k in sorted(F):
    if k=='p-000' or F[k]['blanca']: continue
    fin=[w for l in F[k]['lineas'] for w in l['p'] if not w.get('sim')]
    ft=[w['t'] for w in sorted(fin,key=lambda w:(w['y']//30,w['x']))]
    pl=open(f'ocr/{k}.txt',encoding='utf-8').read().split()
    norm=lambda t: re.sub(r'[^\wáéíóúüñ]','',t.lower())
    a=[norm(t) for t in pl]; b=[norm(t) for t in ft]
    sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
    for op,i1,i2,j1,j2 in sm.get_opcodes():
        if op=='equal':
            for i,j in zip(range(i1,i2),range(j1,j2)):
                p1=re.sub(r'[\wáéíóúüñÁÉÍÓÚÜÑ]','',pl[i]); p2=re.sub(r'[\wáéíóúüñÁÉÍÓÚÜÑ]','',ft[j])
                if p1!=p2 and (p1.strip('|')!=p2) and len(pl[i])>1:
                    out.append((k,'punt',pl[i],ft[j]))
                elif pl[i]!=ft[j] and pl[i].lower()==ft[j].lower():
                    out.append((k,'mayus',pl[i],ft[j]))
        elif op in ('delete','replace'):
            miss=[pl[i] for i in range(i1,i2) if len(norm(pl[i]))>=2 and re.fullmatch(r'[\wáéíóúüñÁÉÍÓÚÜÑ.,;:()/$°-]+',pl[i])]
            got=' '.join(ft[j1:j2])
            if miss and op=='delete': out.append((k,'falta',' '.join(miss),''))
print(len(out))
print(collections.Counter(o[1] for o in out))
json.dump(out,open('comparacion.json','w'),ensure_ascii=False)
for o in out[:60]: print(o)
