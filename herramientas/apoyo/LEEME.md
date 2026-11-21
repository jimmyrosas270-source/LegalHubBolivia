# Scripts de apoyo (no los usa el generador)

Scripts que se usaron en los chats de trabajo y que conviene conservar entre sesiones.
Rutas internas pueden apuntar a /home/claude/...: ajustarlas antes de usar.

- cc.py / cpc.py: artículo → página del PDF del Código Civil / Código Procesal Civil (modo «titulos»/«faltan»).
- art.py, cpe.py: búsqueda de artículos en PDF y en la CPE.
- quitar_studocu.py, limpiar_cpc.py: limpieza de PDF reescribiendo el contenido de cada página (pypdf); luego comparar texto con pdftotext.
- comparar.py, revisa_pdf.py: comparación de textos y revisión rápida de PDF.
- shot.py, busca.py, visor2.py: capturas con Playwright (/usr/bin/google-chrome, --no-sandbox) del sitio servido en local (puerto 8765), del buscador y del visor (#pag y .page[data-page-number=N]).
- manual_depositos/ (21 nov): cómo se rehízo con texto real el Manual de Depósitos Judiciales escaneado. ocr3.py (OCR por zonas y celdas de tabla, dos pasadas: x1,5 y x1) → fusion.py (marca dudas) → vinetas*.py (viñetas) → laminas.py (láminas para revisar a ojo) → corr.txt / lineas_corr.json / palabras_corr.json (correcciones hechas leyendo la imagen) → ensamblar.py → render.py (reportlab, misma página y posición). lado.py: escaneado y PDF nuevo lado a lado. Necesita las imágenes del escaneado (pdfimages -j), que no están en el repositorio.
- gaceta/ (21 nov): extraer.py separa los 177 autos de la Gaceta Judicial Tomo 4 (índice interno, página del visor donde empieza el AUTO SUPREMO, fecha, decisión, doctrina aplicable); temas.py tiene el tema de cada auto con palabras propias.
