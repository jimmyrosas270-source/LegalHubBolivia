# LegalHubBolivia

Sitio legal boliviano. Cada cambio que se guarda en este repositorio (rama `main`) se construye y se publica solo en Cloudflare, en unos 2 minutos. El avance se ve en la pestaña **Actions**.

## Carpetas

| Carpeta | Qué va ahí | Quién la toca |
| --- | --- | --- |
| `biblioteca/pdf/` | Los PDF de la Biblioteca (máximo 25 MB cada uno) | Titular |
| `biblioteca/catalogo.csv` | Una fila por PDF: título, tipo, número, fecha, materia, estado | Titular |
| `jurisprudencia/pdf/` | Las revistas jurisprudenciales en PDF, una por año o tomo (máximo 25 MB cada una) | Titular |
| `jurisprudencia/catalogo.csv` | Una fila por revista: título, tipo, número, fecha (año), materia | Titular |
| `sitio_base/` | Las normas publicadas por artículos (vista previa v2), como `.zip` | Titular, una vez |
| `contenido/notas_editoriales.json` | Notas propias del editor que se insertan bajo un artículo | Claude / titular |
| `contenido/sitio.json` | `abierto_a_buscadores`: `false` hasta el lanzamiento | Claude |
| `herramientas/` | Generador, revisor y visor de PDF (pdf.js) | Claude |

## Subir un PDF nuevo

1. Entra a `biblioteca/pdf/` → **Add file** → **Upload files** → arrastra el PDF → **Commit changes**.
   Nombre del archivo: minúsculas, sin tildes ni espacios (ejemplo: `codigo-de-las-familias.pdf`).
2. Abre `biblioteca/catalogo.csv` → lápiz (**Edit**) → añade una línea con el mismo nombre de archivo → **Commit changes**.
   Columnas separadas por punto y coma: `archivo;titulo;tipo;numero;fecha;materia;estado;descripcion;revisado;version`.
   Estados válidos: Vigente, Con modificaciones, Verificar, Desactualizada, Derogada, Abrogada.
   Si un PDF no tiene fila, igual se publica con el nombre del archivo y estado «Verificar».
3. Espera la marca verde en **Actions**. El documento aparece en `/biblioteca/`.

Para retirar un PDF: bórralo de `biblioteca/pdf/` (y su fila del catálogo).

## Subir una revista de jurisprudencia

Igual que la Biblioteca, pero en la carpeta `jurisprudencia/`:

1. `jurisprudencia/pdf/` → **Add file** → **Upload files** → arrastra el PDF (máximo 25 MB) → **Commit changes**.
2. `jurisprudencia/catalogo.csv` → lápiz → añade una línea con el mismo nombre de archivo.
   Columnas: `archivo;titulo;tipo;numero;fecha;materia;estado;descripcion;revisado;version`.
   Ejemplo: `revista-2022.pdf;Revista Jurisprudencial 2022;Revista jurisprudencial;;2022;Varias;;Compilación de la jurisprudencia más relevante de 2022.;;1`
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
