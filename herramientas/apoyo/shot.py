import sys
from playwright.sync_api import sync_playwright
pages=sys.argv[1].split(',')
w=int(sys.argv[2]); full=len(sys.argv)>3
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
    for u in pages:
        ctx=b.new_context(viewport={'width':w,'height':900})
        pg=ctx.new_page(); errs=[]
        pg.on('pageerror',lambda e: errs.append(str(e)))
        pg.on('console',lambda m: errs.append(m.text) if m.type=='error' else None)
        pg.goto('http://localhost:8765'+u); pg.wait_for_timeout(1500)
        n=u.strip('/').replace('/','_') or 'home'
        pg.screenshot(path=f'/home/claude/prev/{n}_{w}.png',full_page=full)
        print(u,w,'errores:',errs)
        ctx.close()
    b.close()
