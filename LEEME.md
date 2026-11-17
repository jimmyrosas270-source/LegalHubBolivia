# LegalHubBolivia

Sitio legal boliviano. Cada cambio que se guarda en este repositorio (rama `main`) se construye y se publica solo en Cloudflare, en unos 2 minutos. El avance se ve en la pestaña **Actions**.

## Carpetas

| Carpeta | Qué va ahí | Quién la toca |
| --- | --- | --- |
| `biblioteca/pdf/<materia>/` | Los PDF de la Biblioteca, uno por norma, dentro de la carpeta de su materia: `laboral/`, `familia/`, `constitucional/`, `civil/`, `procesal-civil/`, `penal/`, `procesal-penal/`, `administrativa/`, `personas-con-discapacidad/` (máximo 25 MB cada uno) | Titular |
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

**Materia nueva** (por ejemplo tributaria): en `biblioteca/pdf/` → **Add file** → **Create new file** → escribe `tributaria/.gitkeep` → **Commit changes**. Luego sube los PDF dentro de esa carpeta.

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

Al publicar, el generador (`herramientas/limpieza_pdf.py`) quita solo los hipervínculos y los resaltados o notas de lector que traigan los PDF. Si los enlaces iban a páginas que no son oficiales del Estado (LexiVox, InfoLeyes y similares), también pone en negro el texto azul de esos enlaces, quita su subrayado y los iconos de la barra del sitio web. El texto no cambia. No hace falta limpiarlos a mano antes de subirlos.

## Secciones por tipo de norma y autos supremos

- Cada materia tiene páginas por tipo: `/biblioteca/<materia>/<tipo>/` (por ejemplo `/biblioteca/laboral/sentencias-constitucionales/`), y cada tipo tiene una página con todas las materias: `/biblioteca/tipos/<tipo>/`. Se generan solas a partir de la columna `tipo` del catálogo.
- Los autos supremos que están dentro de las revistas se listan desde `contenido/autos_supremos.json` (número, fecha, sala, materia, página de la revista, tema con palabras propias y guías relacionadas). Para añadir uno, copia una entrada.

## Buscador

El buscador (`/buscar/`) busca en las normas por artículos, las guías, las preguntas, el glosario, las fichas de la Biblioteca, los autos supremos y el texto de todas las páginas de los PDF. Se arma solo al publicar (`herramientas/buscador.py`).

## Recuadro «Reportar un error»

Si `contenido/sitio.json` tiene `"reportes_url"` (la dirección de un formulario, por ejemplo de Google Forms), todas las páginas muestran al final un recuadro para avisar de un dato erróneo o desactualizado. Si la dirección contiene `{pagina}`, se reemplaza por la página desde la que se reporta. Sin esa clave, el recuadro no aparece.
