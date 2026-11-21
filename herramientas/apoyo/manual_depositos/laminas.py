import json
from PIL import Image, ImageDraw, ImageFont
V=json.load(open('vinetas.json'))
B={(o['k'],o['x'],o['y']) for o in V if o['v']}
D=json.load(open('dudas.json'))
D=[d for d in D if d['k']!='p-000' and (d['k'],d['x'],d['y']) not in B and not (d['m']==['conf']) and not (d['m']==['signo'] and d['t'] in ('-','.',',',':',';')) and d['t']!='|']
json.dump([d['id'] for d in D],open('rev/ids.json','w'))
F=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
cols,rows=3,16; CW,CH=420,62
imgs={}
for li in range(0,len(D),cols*rows):
    lote=D[li:li+cols*rows]
    H=Image.new('RGB',(cols*CW,rows*CH),'white'); dr=ImageDraw.Draw(H)
    for j,d in enumerate(lote):
        x=(j%cols)*CW; y=(j//cols)*CH
        if d['k'] not in imgs: imgs[d['k']]=Image.open(f"img/{d['k']}.jpg").convert('RGB')
        im=imgs[d['k']]
        x0=max(0,d['x']-60); x1=min(im.width,d['x']+d['w']+60); y0=max(0,d['y']-6); y1=d['y']+d['h']+6
        cr=im.crop((x0,y0,x1,y1)).copy(); cd=ImageDraw.Draw(cr)
        cd.rectangle((d['x']-x0-2,d['y']-y0-2,d['x']-x0+d['w']+2,d['y']-y0+d['h']+2),outline=(255,0,0))
        cr.thumbnail((CW-6,40))
        H.paste(cr,(x+2,y+1))
        alt='' if d['alt']==d['t'] else f" | {d['alt']}"
        dr.text((x+2,y+43),f"{d['id']}: {d['t']}{alt}",fill=(0,0,200),font=F)
        dr.line((x,y+CH-1,x+CW,y+CH-1),fill=(200,200,200))
    H.save(f'rev/l{li//(cols*rows):02d}.png')
print(len(D), (len(D)+47)//48)
