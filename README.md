# Ocelote UNACH · Realidad Aumentada

Página web que muestra al Ocelote de la UNACH en realidad aumentada (AR) usando la
cámara del celular. Se accede escaneando un código QR; no hace falta instalar ninguna app.

- **Android (Chrome):** AR dentro de la página (WebXR) con animaciones, botones y voz.
  Si el teléfono no admite WebXR se abre Google Scene Viewer.
- **iPhone / iPad (Safari):** se abre AR Quick Look de Apple con el Ocelote animado (ver limitaciones abajo).
- **Computadora:** se ve el modelo 3D interactivo y un QR para abrirlo en el celular.

## Estructura

| Ruta | Contenido |
| --- | --- |
| `index.html`, `css/`, `js/` | La página web |
| `models/ocelote.glb` | Modelo convertido del FBX (665 KB, comprimido con Draco, 6 animaciones) |
| `models/ocelote.usdz` | Versión para iPhone / iPad (AR Quick Look) con voz y animación |
| `vendor/model-viewer.min.js` | [`<model-viewer>`](https://modelviewer.dev) 4.4.0 de Google |
| `vendor/draco/` | Decodificador Draco (de three.js) para leer el modelo comprimido |
| `audio/ocelote.mp3` | Voz del Ocelote (va con la animación Hablar) |
| `qr/ocelote-qr.png` / `.svg` | Código QR que abre la página |
| `qr/imprimir.html` | Hoja lista para imprimir con el QR e instrucciones |
| `source/Ocelote_UNACH.fbx` | Modelo original |
| `tools/` | Scripts para reconvertir el modelo y regenerar el QR |

## Animaciones incluidas

`Idle` (reposo, en bucle), `Saludo`, `Hablar` (45 s), `Hablar_Loop`, `Celebrar` y `Caminar`.
Al cargar y al entrar en AR el Ocelote saluda y luego queda en reposo. Los botones de la
parte inferior cambian de animación.

## Audio

`audio/ocelote.mp3` es la voz del Ocelote (45 s). La animación `Hablar` dura exactamente lo
mismo y su mandíbula ya está sincronizada con la voz. Al tocar **💬 Hablar**, la voz suena
y la página corrige cualquier desfase entre audio y animación. El botón 🔊 silencia.

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

## iPhone / iPad (AR Quick Look)

Safari en iOS no admite AR dentro de la página (WebXR), así que el botón **Ver en tu espacio**
abre el visor de Apple con `models/ocelote.usdz`. Ese visor no muestra los botones de la
página ni reproduce su audio, así que el archivo trae la voz integrada y "comportamientos"
de Apple (el mismo esquema que usa Reality Composer):

- Al aparecer, el Ocelote dice su diálogo (animación Hablar + voz) y luego queda en reposo.
- Al tocarlo, vuelve a hablar.

En iPhone, los botones y la voz también funcionan en la vista 3D de la página.

Para regenerar el USDZ (requiere Python 3.13 y ffmpeg):

```bash
python3 -m venv venv && venv/bin/pip install bpy==5.2.4 usd-core
ffmpeg -i audio/ocelote.mp3 -c:a aac -b:a 128k voz.m4a
venv/bin/python tools/make_usdz.py source/Ocelote_UNACH.fbx models/ocelote.usdz --talk voz.m4a
```

Sin `--talk`, el script genera una secuencia de animaciones en bucle sin audio
(se elige con `--seq`, nombres separados por comas).
