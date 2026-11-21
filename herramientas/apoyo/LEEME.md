# Scripts de apoyo (no los usa el generador)

Scripts que se usaron en los chats de trabajo y que conviene conservar entre sesiones.
Rutas internas pueden apuntar a /home/claude/...: ajustarlas antes de usar.

- cc.py / cpc.py: artículo → página del PDF del Código Civil / Código Procesal Civil (modo «titulos»/«faltan»).
- art.py, cpe.py: búsqueda de artículos en PDF y en la CPE.
- quitar_studocu.py, limpiar_cpc.py: limpieza de PDF reescribiendo el contenido de cada página (pypdf); luego comparar texto con pdftotext.
- comparar.py, revisa_pdf.py: comparación de textos y revisión rápida de PDF.
- shot.py, busca.py, visor2.py: capturas con Playwright (/usr/bin/google-chrome, --no-sandbox) del sitio servido en local (puerto 8765), del buscador y del visor (#pag y .page[data-page-number=N]).
