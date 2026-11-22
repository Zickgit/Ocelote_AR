# Ocelote UNACH · Realidad Aumentada

Página web que muestra al Ocelote de la UNACH en realidad aumentada (AR) usando la
cámara del celular. Se accede escaneando un código QR; no hace falta instalar ninguna app.

- **Android (Chrome):** AR dentro de la página (WebXR) con animaciones, botones y voz.
  Si el teléfono no admite WebXR se abre Google Scene Viewer.
- **iPhone / iPad (Safari o Chrome):** se abre AR Quick Look de Apple (ver nota sobre iOS abajo).
- **Computadora:** se ve el modelo 3D interactivo y un QR para abrirlo en el celular.

## Estructura

| Ruta | Contenido |
| --- | --- |
| `index.html`, `css/`, `js/` | La página web |
| `models/ocelote.glb` | Modelo convertido del FBX (665 KB, comprimido con Draco, 6 animaciones) |
| `vendor/model-viewer.min.js` | [`<model-viewer>`](https://modelviewer.dev) 4.4.0 de Google |
| `vendor/draco/` | Decodificador Draco (de three.js) para leer el modelo comprimido |
| `audio/` | Aquí va el audio de voz (ver abajo) |
| `qr/ocelote-qr.png` / `.svg` | Código QR que abre la página |
| `qr/imprimir.html` | Hoja lista para imprimir con el QR e instrucciones |
| `source/Ocelote_UNACH.fbx` | Modelo original |
| `tools/` | Scripts para reconvertir el modelo y regenerar el QR |

## Animaciones incluidas

`Idle` (reposo, en bucle), `Saludo`, `Hablar` (45 s), `Hablar_Loop`, `Celebrar` y `Caminar`.
Al cargar y al entrar en AR el Ocelote saluda y luego queda en reposo. Los botones de la
parte inferior cambian de animación.

## Audio

El archivo FBX **no contiene audio** (el formato FBX no guarda pistas de sonido), así que
hay que agregarlo aparte:

1. Exporta el audio de la voz (el que va con la animación `Hablar`, de 45 s) como MP3.
2. Guárdalo como `audio/ocelote.mp3`.
3. Haz commit y push.

La página lo detecta sola: al tocar **💬 Hablar** suena la voz sincronizada con la
animación, y aparece el botón 🔊 para silenciar. Sin el archivo, la animación se
reproduce sin sonido.

## Publicar en GitHub Pages

1. En GitHub: **Settings → Pages → Build and deployment → Source: Deploy from a branch**.
2. Elige la rama donde está este código (por ejemplo `main`) y la carpeta `/ (root)`.
3. La página quedará en **https://zickgit.github.io/Ocelote_AR/** — el QR de `qr/` ya
   apunta a esa dirección.

La AR requiere HTTPS (GitHub Pages lo da automáticamente).

Si publicas en otra dirección, regenera el QR:

```bash
cd tools
npm install
node make-qr.mjs https://tu-dominio.com/ruta/
```

## Reconvertir el modelo

Si actualizas el FBX en Blender, reemplaza `source/Ocelote_UNACH.fbx` y ejecuta:

```bash
cd tools
npm install
npm run build-model
```

El script usa three.js para leer el FBX, convierte los materiales a PBR (corrigiendo el
espacio de color lineal de Blender), une los grupos de material, y luego glTF-Transform
suelda vértices, re-muestrea las animaciones y comprime con Draco.

## Nota sobre iOS

Quick Look de Apple solo lee archivos USDZ. Si no hay uno, `<model-viewer>` genera un USDZ
al vuelo a partir del GLB, pero **sin animación ni audio**. Para tener animación en iPhone,
exporta un USDZ animado desde Blender (File → Export → Universal Scene Description, con
animación) o con Reality Converter, y guárdalo como `models/ocelote.usdz`; la página lo
usará automáticamente.
