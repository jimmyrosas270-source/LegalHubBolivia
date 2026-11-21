from playwright.sync_api import sync_playwright
casos=[('codigo-procesal-civil',23,'ARTÍCULO 110'),('codigo-procesal-civil',58,'ARTÍCULO 292'),('codigo-procesal-civil',76,'ARTÍCULO 363'),('codigo-procesal-civil',80,'ARTÍCULO 379'),('codigo-procesal-civil',64,'ARTÍCULO 318'),('codigo-procesal-civil',98,'ARTÍCULO 455'),('codigo-procesal-civil',52,'ARTÍCULO 261'),('codigo-procesal-civil',55,'ARTÍCULO 273'),('codigo-procesal-civil',83,'ARTÍCULO 393'),('codigo-procesal-civil',60,'ARTÍCULO 298'),
('codigo-civil',56,'Art. 450'),('codigo-civil',66,'Art. 549'),('codigo-civil',65,'Art. 537'),('codigo-civil',114,'Art. 984'),('codigo-civil',171,'Art. 1461'),('codigo-civil',172,'Art. 1466'),('codigo-civil',176,'PRESCRIPCION TRIENAL'),('codigo-civil',71,'Art. 584'),('codigo-civil',76,'Art. 629')]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
    for s,n,t in casos:
        ctx=b.new_context(); pg=ctx.new_page()
        pg.goto(f'http://localhost:8765/biblioteca/{s}/leer/#page={n}'); pg.wait_for_timeout(5000)
        v=pg.input_value('#pag'); txt=' '.join(pg.locator(f'.page[data-page-number="{n}"]').inner_text().split())
        print(s,n,'pag',v,t in txt)
        ctx.close()
    b.close()
