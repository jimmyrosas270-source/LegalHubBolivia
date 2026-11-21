import sys
from urllib.parse import quote
from playwright.sync_api import sync_playwright
qs=sys.argv[1:]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
    for q in qs:
        ctx=b.new_context(viewport={'width':1280,'height':900}); pg=ctx.new_page(); errs=[]
        pg.on('pageerror',lambda e: errs.append(str(e)))
        pg.goto('http://localhost:8765/buscar/?q='+quote(q)); pg.wait_for_timeout(3500)
        print('==',q,'|',pg.locator('#estado').inner_text(), errs)
        items=pg.evaluate("""()=>[...document.querySelectorAll('#resultados > *, .resultados > *')].slice(0,9).map(e=>(e.tagName=='H2'?'## ':'')+(e.querySelector('b')?e.querySelector('b').innerText+' — '+(e.querySelector('small')||{}).innerText:e.innerText))""")
        for it in items: print('   ',it[:110])
        ctx.close()
    b.close()
