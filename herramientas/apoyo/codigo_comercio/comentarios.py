"""Separa, de la edición anotada del Código de Comercio, el comentario que sigue a cada artículo (material de apoyo, no se publica).
Uso: python3 -I comentarios.py edicion-anotada.pdf salida.json"""
import re, json, subprocess, sys
src = sys.argv[1]  # PDF de la edición anotada (no está en el repositorio)
t=subprocess.run(['pdftotext',src,'-'],capture_output=True,text=True).stdout.replace('\f','\n')
t=re.sub(r'\n?Descargado desde el sitio www\.bolivianland\.net\s*\nPágina \d+\s*\n','\n',t)
t=t.replace('CAP╓TULO','CAPÍTULO')
t=re.sub(r'(?<=\S)[ \t]*((?:LIBRO|T[IÍ]TULO|CAP[IÍ]TULO|SECCI[OÓ]N)\s+(?:[IVXL]+|PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|PRELIMINAR|[ÚU]NIC[OA])\b)', r'\n\1', t)
CAB=re.compile(r'ART[IÍ]CULOS?\.?\s+((?:\d|l)\.\d{3}|\d{1,2}\.\d{3}|\d+)\s*[º°]?\s*(?:[\.\-–]\s*){1,3}(?=\(|[A-ZÁÉÍÓÚÑ¿"“])')
num=lambda x:int(x.group(1).replace('l','1').replace('.',''))
FIN=re.compile(r'(?:(?<=\s)|(?<=^))(Precd\s*[:.]?|Conc\s*[:.\-]|Conc\s+(?=c\.|C\.|Const|p\.\s?c|loj|L\.|D\.\s?S|DD|Rgto|Tdo)|Con:)')
heads,prev,pos=[],0,0
while True:
    m=None
    for x in CAB.finditer(t,pos):
        n=num(x)
        if n==prev+1 or (prev and 1<n-prev<=3 and not re.search(r'ART[IÍ]CULO\s+%s\b'%(prev+1),t[pos:x.start()])):
            m=x;break
    if not m: break
    heads.append(m); prev,pos=num(m),m.end()
k_dt=t.index('DISPOSICIONES TRANSITORIAS',heads[-1].end())
res={}
for i,h in enumerate(heads):
    sig=heads[i+1].start() if i+1<len(heads) else k_dt
    tramo=t[h.end():sig]; f=FIN.search(tramo)
    if not f: continue
    resto=tramo[f.start():]
    # quitar el bloque de precedentes y concordancias: renglones hasta el primero que parece prosa (empieza con mayúscula y tiene 8+ palabras sin abreviaturas de concordancia)
    ls=[l.strip() for l in resto.split('\n')]
    k=0
    while k<len(ls) and (not ls[k] or re.match(r'^(Precd|Conc|Con:)',ls[k]) or re.search(r'\b(c\.\s?c\.|c\.\s?com|p\.\s?c\.|Const\.|Art\.|arts?\.)\s*\d',ls[k]) and len(ls[k])<160 and not re.search(r'[a-záéíóú]{4,}\s+[a-záéíóú]{4,}\s+[a-záéíóú]{4,}\s+[a-záéíóú]{4,}',ls[k])):
        k+=1
    com=' '.join(ls[k:]).strip()
    com=re.sub(r'\s+',' ',com)
    # quitar encabezados de estructura del final
    com=re.sub(r'\s*((LIBRO|T[IÍ]TULO|CAP[IÍ]TULO|SECCI[OÓ]N)\s+[IVXLÚÚNICOPRELIMNAR]+\b[^a-z]*)$','',com)
    res[num(h)]=com
json.dump(res,open(sys.argv[2],'w'),ensure_ascii=False)
L=sorted(((len(v),k) for k,v in res.items()),reverse=True)
print(len(res),sum(1 for v in res.values() if len(v)>200),sum(len(v) for v in res.values()))
print(L[:40])
