import sys,subprocess
from PIL import Image
for n in sys.argv[1:]:
    n=int(n)
    subprocess.run(['pdftoppm','-r','90','-f',str(n),'-l',str(n),'-png','-singlefile','prueba.pdf','/tmp/rr'],check=True)
    a=Image.open(f'img/p-{n-1:03d}.jpg'); b=Image.open('/tmp/rr.png')
    a=a.resize(b.size)
    c=Image.new('RGB',(b.width*2+10,b.height),'white'); c.paste(a,(0,0)); c.paste(b,(b.width+10,0))
    c.save(f'/tmp/lado{n}.png'); print(c.size)
