# Configuración de cada norma que se publica por artículos (la lee extraer.py).
# pdf: ruta bajo biblioteca/pdf/; paginas: (desde, hasta) del PDF; desde: regex del renglón donde empieza la norma;
# saltar: regex de renglones del compilador que no son texto de la norma (y saltar_bloque: hasta dónde sigue el bloque);
# reemplazos: (regex, texto) aplicados antes de separar (solo para unir encabezados partidos, nunca para cambiar palabras).
NORMAS = {
 'codigo-civil': dict(pdf='civil/codigo-civil.pdf', materia='civil', slug='codigo-civil', titulo='Código Civil', tipo='Decreto Ley',
                      fecha='1975-08-06', epigrafe='Decreto Ley 12760 de 6 de agosto de 1975',
                      desde=r'^LIBRO PRIMERO$', estructura_mixta=True, num_solo=True, fin=r'^Información extraída del Sistema',
                      # en algunas páginas el rótulo del artículo siguiente quedó pegado al final del renglón anterior
                      reemplazos=[(r'^Art\. 13760\.', 'Art. 1376.'), (r'(?<=[^\s(]) +(Art\.\s*\d+\s*[o°º]?\s*[\.\-]+\s*\((?=[A-ZÁÉÍÓÚ]))', r'\n\1')]),
 'codigo-procesal-civil': dict(pdf='procesal-civil/ley-439-codigo-procesal-civil.pdf', materia='procesal-civil', slug='codigo-procesal-civil', titulo='Código Procesal Civil', tipo='Ley',
                      fecha='2013-11-19', epigrafe='Ley 439 de 19 de noviembre de 2013'),
 'codigo-penal': dict(pdf='penal/codigo-penal-2025.pdf', materia='penal', slug='codigo-penal', titulo='Código Penal', tipo='Decreto Ley',
                      fecha='1972-08-23', epigrafe='Decreto Ley 10426 de 23 de agosto de 1972, edición actualizada 2025',
                      reemplazos=[(r' {2,}\d{1,4} +Fiscalía General del Estado( {2,}|$)', ' '), (r' {2,}C[ÓO]DIGO PENAL +\d{1,4}( {2,}|$)', ' ')]),
 'codigo-de-procedimiento-penal': dict(pdf='procesal-penal/ley-1970-codigo-de-procedimiento-penal-2025.pdf', materia='procesal-penal', slug='codigo-de-procedimiento-penal',
                      titulo='Código de Procedimiento Penal', tipo='Ley', fecha='1999-03-25', epigrafe='Ley 1970 de 25 de marzo de 1999, edición actualizada 2025',
                      ruido_re=[r'^Ley N° 1970\s+\d{1,4}$'], reemplazos=[(r' {2,}Ley N° 1970 +\d{1,4}( {2,}|$)', ' '), (r'(?<=\S) Ley N° 1970 \d{3} (?=\S)', ' '), (r' {2,}\d{1,4} +Fiscalía General del Estado( {2,}|$)', ' ')]),
 'codigo-de-las-familias': dict(pdf='familia/ley-603-codigo-de-las-familias.pdf', materia='familia', slug='codigo-de-las-familias', titulo='Código de las Familias y del Proceso Familiar',
                      tipo='Ley', fecha='2014-11-19', epigrafe='Ley 603 de 19 de noviembre de 2014', mitades=(454, 596)),
 'codigo-nina-nino-y-adolescente': dict(pdf='familia/codigo-nina-nino-y-adolescente-ley-548.pdf', materia='familia', slug='codigo-nina-nino-y-adolescente', titulo='Código Niña, Niño y Adolescente',
                      tipo='Ley', fecha='2014-07-17', epigrafe='Ley 548 de 17 de julio de 2014'),
 'codigo-procesal-constitucional': dict(pdf='constitucional/ley-254-codigo-procesal-constitucional.pdf', materia='constitucional', slug='codigo-procesal-constitucional',
                      titulo='Código Procesal Constitucional', tipo='Ley', fecha='2012-07-05', epigrafe='Ley 254 de 5 de julio de 2012',
                      reemplazos=[(r' {2,}\d{1,4} +Fiscalía General del Estado( {2,}|$)', ' '), (r' {2,}Ley N° 254 +\d{1,4}( {2,}|$)', ' ')]),
 'ley-348': dict(pdf='penal/ley-348.pdf', materia='penal', slug='ley-348', titulo='Ley 348 Integral para Garantizar a las Mujeres una Vida Libre de Violencia', tipo='Ley',
                      fecha='2013-03-09', epigrafe='Ley 348 de 9 de marzo de 2013',
                      # número de página al margen izquierdo, que en el texto queda al comienzo o en medio del renglón
                      pre=[(r'^ {0,3}\d{1,3} {3,}', ''), (r' {3,}\d{1,3}$', ''), (r'(?<=\S) {3,}\d{1,3} {3,}(?=\S)', ' ')]),
 'ley-2341': dict(pdf='administrativa/ley-2341.pdf', materia='administrativa', slug='ley-de-procedimiento-administrativo', titulo='Ley de Procedimiento Administrativo', tipo='Ley',
                      fecha='2002-04-23', epigrafe='Ley 2341 de 23 de abril de 2002'),
 'codigo-de-seguridad-social': dict(pdf='laboral/codigo-de-seguridad-social.pdf', materia='laboral', slug='codigo-de-seguridad-social', titulo='Código de Seguridad Social', tipo='Ley',
                      fecha='1956-12-14', epigrafe='Ley de 14 de diciembre de 1956',
                      # notas de la base de datos legislativa («Referencia: … <<<<») y pies «TEXTO INOFICIAL»: no son texto del Código
                      reemplazos=[(r' *Pag\. \d+ de 110', ''), (r' *(LEY +)?PRESIDENCIA DE LA ASAMBLEA LEGISLATIVA PLURINACIONAL( +14/12/1956)?', ''), (r' *VICEPRESIDENCIA DEL ESTADO( +LEY)?', ''), (r' *ÁREA LABORAL Y SEGURIDAD SOCIAL', ''), (r'(?s)Referencia:(?:(?!ART[IÍ]CULO\s*\d).){0,4000}?<<<<', ''), (r'^.*>>>>AREA.*$', ''), (r'^TEXTO INOFICIAL\..*$', '')]),
 'ley-025': dict(pdf='constitucional/ley-025-organo-judicial.pdf', materia='constitucional', slug='ley-del-organo-judicial', titulo='Ley del Órgano Judicial', tipo='Ley',
                      fecha='2010-06-24', epigrafe='Ley 025 de 24 de junio de 2010'),
 'ley-223': dict(pdf='personas-con-discapacidad/ley-223.pdf', materia='personas-con-discapacidad', slug='ley-223', titulo='Ley General para Personas con Discapacidad', tipo='Ley',
                      fecha='2012-03-02', epigrafe='Ley 223 de 2 de marzo de 2012'),
 'ley-393': dict(pdf='comercial/ley-393-servicios-financieros.pdf', materia='comercial', slug='ley-de-servicios-financieros', titulo='Ley de Servicios Financieros', tipo='Ley',
                      fecha='2013-08-21', epigrafe='Ley 393 de 21 de agosto de 2013'),
 'ley-1178': dict(pdf='administrativa/ley-1178.pdf', materia='administrativa', slug='ley-safco', titulo='Ley de Administración y Control Gubernamentales (SAFCO)', tipo='Ley',
                      fecha='1990-07-20', epigrafe='Ley 1178 de 20 de julio de 1990'),
 'ley-708': dict(pdf='civil/ley-708-conciliacion-y-arbitraje.pdf', materia='civil', slug='ley-de-conciliacion-y-arbitraje', titulo='Ley de Conciliación y Arbitraje', tipo='Ley',
                      fecha='2015-06-25', epigrafe='Ley 708 de 25 de junio de 2015'),
}
