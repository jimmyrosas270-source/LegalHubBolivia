# LegalHubBolivia

Sitio legal boliviano. Cada cambio que se guarda en este repositorio (rama `main`) se construye y se publica solo en Cloudflare, en unos 2 minutos. El avance se ve en la pestaña **Actions**.

## Carpetas

| Carpeta | Qué va ahí | Quién la toca |
| --- | --- | --- |
| `biblioteca/pdf/<materia>/` | Los PDF de la Biblioteca, uno por norma, dentro de la carpeta de su materia: `laboral/`, `familia/`, `constitucional/`, `civil/`, `procesal-civil/`, `penal/`, `procesal-penal/`, `administrativa/`, `agraria/`, `tributario/`, `personas-con-discapacidad/` (máximo 25 MB cada uno) | Titular |
| `biblioteca/catalogo.csv` | Una fila por PDF: título, tipo, número, fecha, materia, estado | Titular |
| `jurisprudencia/pdf/` | Las revistas jurisprudenciales en PDF, una por año o tomo (máximo 25 MB cada una) | Titular |
| `jurisprudencia/catalogo.csv` | Una fila por revista: título, tipo, número, fecha (año), materia | Titular |
| `sitio_base/` | Las normas publicadas por artículos (vista previa v2), como `.zip` | Titular, una vez |
| `contenido/notas_editoriales.json` | Notas propias del editor que se insertan bajo un artículo | Claude / titular |
| `contenido/sitio.json` | `abierto_a_buscadores`: `false` hasta el lanzamiento | Claude |
| `herramientas/` | Generador, revisor y visor de PDF (pdf.js) | Claude |

## Subir un PDF nuevo

1. Entra a `biblioteca/pdf/` → abre la carpeta de la materia (por ejemplo `laboral/`) → **Add file** → **Upload files** → arrastra el PDF → **Commit changes**.
   Nombre del archivo: minúsculas, sin tildes ni espacios, empezando por el tipo de norma, para que la carpeta quede ordenada:
   `ley-1468.pdf`, `decreto-supremo-28699.pdf`, `resolucion-ministerial-447-09.pdf`, `sentencia-constitucional-1262-2013.pdf`.
   **La carpeta decide la materia** en el sitio: un PDF en `laboral/` sale en la carpeta «Laboral» de `/biblioteca/`.
2. Abre `biblioteca/catalogo.csv` → lápiz (**Edit**) → añade una línea con el mismo nombre de archivo (solo el nombre, sin la carpeta) → **Commit changes**.
   Columnas separadas por punto y coma: `archivo;titulo;tipo;numero;fecha;materia;estado;descripcion;revisado;version`.
   El catálogo está ordenado por materia; pon la línea nueva junto a las de su materia.
   `tipo` decide el grupo dentro de la materia: Ley · Decreto Supremo / Decreto Ley / Fe de erratas · Resolución Ministerial · Reglamento / Protocolo · Sentencia Constitucional Plurinacional / Auto Supremo. Si el título dice «Código», va en «Códigos».
   `fecha` ordena: dentro de cada grupo, del más antiguo al más reciente.
   Estados válidos: Vigente, Con modificaciones, Verificar, Desactualizada, Derogada, Abrogada.
   Si un PDF no tiene fila, igual se publica con el nombre del archivo y estado «Verificar».
3. Espera la marca verde en **Actions**. El documento aparece en `/biblioteca/<materia>/`.

**Materia nueva** (por ejemplo comercial): en `biblioteca/pdf/` → **Add file** → **Create new file** → escribe `comercial/.gitkeep` → **Commit changes**. Luego sube los PDF dentro de esa carpeta.

Para retirar un PDF: bórralo de su carpeta (y su fila del catálogo). Para cambiarlo de materia: bórralo y súbelo a la otra carpeta. Los enlaces de cada norma (`/biblioteca/<nombre>/`) no cambian al moverla de carpeta, porque salen del título.

## Subir una revista de jurisprudencia

Igual que la Biblioteca, pero en la carpeta `jurisprudencia/`:

1. `jurisprudencia/pdf/` → **Add file** → **Upload files** → arrastra el PDF (máximo 25 MB) → **Commit changes**.
2. `jurisprudencia/catalogo.csv` → lápiz → añade una línea con el mismo nombre de archivo.
   Columnas: `archivo;titulo;tipo;numero;fecha;materia;estado;descripcion;revisado;version`.
   Ejemplo: `resumenes-de-jurisprudencia-tsj-2023.pdf;Resúmenes de Jurisprudencia TSJ 2023;Revista jurisprudencial;;2023;Varias;;Compilación de la jurisprudencia más relevante de 2023.;;1`
   Lo que importa: `titulo` (da el enlace) y `fecha` (el año; las revistas se agrupan por año, de la más reciente a la más antigua). La columna `estado` se deja vacía: aquí no se usa. Sin punto y coma dentro de ningún texto.
3. Espera la marca verde en **Actions**. La revista aparece en `/jurisprudencia/`.

## Configuración inicial (una sola vez)

1. **Normas por artículos**: sube `LegalHubBolivia_vista_previa_v2.zip` tal cual (sin descomprimir) a `sitio_base/`. El generador lo descomprime, añade «Biblioteca» al menú y coloca las notas editoriales.
2. **Clave de Cloudflare**:
   - Cloudflare → tu perfil → **API Tokens** → **Create Token** → plantilla **Edit Cloudflare Workers** → **Continue to summary** → **Create Token**. Copia la clave.
   - Cloudflare → **Workers & Pages**: copia el **Account ID** (columna derecha).
   - GitHub → este repositorio → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:
     `CLOUDFLARE_API_TOKEN` (la clave) y `CLOUDFLARE_ACCOUNT_ID` (el Account ID).
   - **Actions** → «Construir y publicar» → **Run workflow**.

El sitio se publica sobre el Worker `legalhubbolivia` (misma dirección de prueba). Mientras `abierto_a_buscadores` sea `false`, el sitio pide a los buscadores no indexarlo.

## Construir en una computadora (opcional)

```
python3 herramientas/construir.py
python3 herramientas/revisar.py salida
cd salida && python3 -m http.server 8000
```
Requiere Python 3 y poppler-utils (`pdfinfo`, `pdftoppm`, `pdftotext`).

## Normas principales y portadas (`contenido/destacadas.json`)

- Cada materia tiene una lista de normas principales, en el orden en que se muestran: la primera sale arriba en `/biblioteca/<materia>/` y en `/leyes/<materia>/`.
- Para cambiar el orden, mueve las entradas en el archivo; para quitar una, bórrala; para añadir un PDF, copia una entrada y pon en `archivo` el nombre que tiene en `catalogo.csv`.
- `"inicio": true` la muestra también en la portada de la Biblioteca.
- `portada` dibuja una tapa propia: `tipo` (rótulo de arriba), `lineas` (el título en renglones cortos), `pie` (año) y `color` (tinta, verde, bosque, menta, kantuta, ocre o papel). Sin `portada`, se usa la primera página del PDF.

## Hipervínculos en los PDF

Al publicar, el generador (`herramientas/limpieza_pdf.py`) quita solo los hipervínculos y los resaltados o notas de lector que traigan los PDF. Si los enlaces iban a páginas que no son oficiales del Estado (LexiVox, InfoLeyes y similares), también pone en negro el texto azul de esos enlaces, quita su subrayado y los iconos de la barra del sitio web. Los enlaces internos (de un índice a otra página del mismo PDF) se conservan. El texto no cambia. No hace falta limpiarlos a mano antes de subirlos.

## Secciones por tipo de norma y autos supremos

- Cada materia tiene páginas por tipo: `/biblioteca/<materia>/<tipo>/` (por ejemplo `/biblioteca/laboral/sentencias-constitucionales/`), y cada tipo tiene una página con todas las materias: `/biblioteca/tipos/<tipo>/`. Se generan solas a partir de la columna `tipo` del catálogo.
- Los autos supremos que están dentro de las revistas se listan desde `contenido/autos_supremos.json` (número, fecha, sala, materia, página de la revista, tema con palabras propias y guías relacionadas). Si el auto está en otra publicación distinta de la general, lleva su clave `revista` (nombre del PDF de `jurisprudencia/pdf/` sin `.pdf`; así están los 177 autos de la Gaceta Judicial Tomo 4). La ficha de cada publicación muestra el índice de sus autos. Para añadir uno, copia una entrada.

## Buscador

El buscador (`/buscar/`) busca en las normas por artículos, las guías, las preguntas, el glosario, las fichas de la Biblioteca, los autos supremos y el texto de todas las páginas de los PDF. Se arma solo al publicar (`herramientas/buscador.py`).
Si lo que se escribe coincide con el nombre de una norma o de una materia («procesal civil», «Constitución», «familia», «Ley 348», «CPC»), primero aparece la norma como tal (su ficha o su página por artículos) y la materia; después, los artículos y lo demás. Las siglas y nombres comunes de cada norma están en la lista `_ALIAS` de `herramientas/buscador.py`; para una norma nueva basta con su título, tipo y número en el catálogo, y la primera frase de su descripción si empieza con su nombre («Ley del Notariado Plurinacional.»).

Buscador rápido (`herramientas/rapido.py`, `rapido.js`, `rapido.css`): mientras se escribe en la portada, en `/buscar/` o en la ventana que abre la lupa de la cabecera (también con «/» o Ctrl+K), aparecen sugerencias con portada. Entiende referencias como «art 24 CPE», «artículo 22 del Código Civil», «CPE 24», «CPP 233», «art 5 bis CP» o solo «art 24» (lo muestra en cada código), lleva directo a la norma si se escribe su nombre («constitución», «código penal») y sugiere artículos por su título, temas, guías, glosario y preguntas. Usa `buscar/rapido.json` (se descarga solo al empezar a escribir). Las siglas que usan docentes y estudiantes están en `_EXTRA_ALIAS` de `herramientas/rapido.py`; una norma por artículos nueva entra sola (conviene añadirle siglas allí y una portada en `contenido/destacadas.json`).
Las revistas de jurisprudencia y los PDF de más de 500 páginas (por ejemplo, un tomo de la Gaceta Judicial) no entran en la búsqueda general, para que no pese demasiado en el celular: se buscan con el filtro «Texto de los PDF» o «Texto de las revistas de jurisprudencia», o dentro de su propio visor.

## Recuadro «Reportar un error»

Si `contenido/sitio.json` tiene `"reportes_url"` (la dirección de un formulario, por ejemplo de Google Forms), todas las páginas muestran al final un recuadro para avisar de un dato erróneo o desactualizado. Si la dirección contiene `{pagina}`, se reemplaza por la página desde la que se reporta. Sin esa clave, el recuadro no aparece.

## Temas de interés y tarjetas «¿Sabías que?»

- Cada tema es un archivo en `contenido/temas/<nombre>.md` y se publica en `/temas/<nombre>/`. Copia uno existente para empezar.
- Encabezado: `titulo`, `materia` (decide el color), `imagen` (ilustración: ninez, mujer, beneficios, asistencia, usucapion, propiedad, denuncia, discriminacion, discapacidad, animales, divorcio, defensa, herencia, alquiler, deudas, juicio, cobro, desalojo, contrato, compraventa, danos), `orden` (posición en la portada), `actualizada`, `resumen`, y las listas `tarjetas`, `normas`, `guias` y `autos` (`- 435/2017 | por qué sirve, con palabras propias`: sale en «Jurisprudencia relacionada» con enlace a la página del visor).
- Cada tarjeta: `- Texto breve | Título exacto de una sección ## del tema | Norma, art. N`. Al tocarla se abre esa sección. Si el título no coincide, el generador avisa.
- Las tarjetas también salen de las líneas `> ` (¿Sabías que?) de las guías. Todas van a `assets/tarjetas.json` y aparecen en la portada, en `/temas/`, dentro de las páginas y, una vez por visita, como tarjeta flotante.
- Los artículos de `/leyes/` que cita un tema muestran «Explicado en un tema».
- Colores por materia: `herramientas/base/materias.css` (el menú queda blanco). Ilustraciones: `herramientas/ilustraciones.py`.

## Cuestionarios de estudio (Estudiantes)

Están en `contenido/cuestionarios/<materia>/<tema>.md` y se publican en `/estudiantes/cuestionarios/<materia>/<tema>/`.
Para **añadir una pregunta**, se escribe al final del archivo del tema:

```
### V | Enunciado que es verdadero.
Explicación corta con palabras propias.
norma: /leyes/laboral/ley-general-del-trabajo/articulo-46/ | Ley General del Trabajo, art. 46
guia: /guias/laboral/jornada-de-trabajo/ | La jornada de trabajo
```

(`### F |` si el enunciado es falso). La línea `norma:` es obligatoria; puede haber varias `norma:` y `guia:`.
En el encabezado, `mostrar: 10` dice cuántas preguntas salen por intento: si el banco tiene más, se eligen al azar.
Para **una materia nueva**, se crea la carpeta (p. ej. `contenido/cuestionarios/familia/`) con sus temas.
No se usan contenidos con [VERIFICAR] (el generador los descarta y avisa en Actions) ni cifras de años pasados.
Todo funciona en el navegador; solo se guarda allí la mejor nota de cada cuestionario.

## Descarga de los PDF (apagada)

Desde el 17 nov 2026 los PDF de la Biblioteca y de Jurisprudencia solo se leen en el visor: no hay botones ni enlaces de descarga.
Para volver a activarlos basta poner `"descargas": true` en `contenido/sitio.json`.
