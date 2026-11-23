# Ocelote UNACH · Realidad Aumentada

Página web que muestra al Ocelote de la UNACH en realidad aumentada (AR) usando la
cámara del celular. Se accede escaneando un código QR; no hace falta instalar ninguna app.

El Ocelote tiene una sola animación de promoción (45 s, con gestos faciales) sincronizada
con su voz.

- **Página web:** un botón **📣 Promocionar** reproduce la animación con la voz.
- **Android (Chrome):** AR dentro de la página (WebXR); al aparecer en tu espacio empieza a
  promocionar, y el botón sigue disponible. Si el teléfono no admite WebXR se abre Google
  Scene Viewer (sin voz).
- **iPhone / iPad (Safari):** AR Quick Look de Apple; al aparecer promociona con su voz y al
  tocarlo vuelve a empezar (ver detalles abajo).
- **Computadora:** se ve el modelo 3D y un QR para abrirlo en el celular.

## Estructura

| Ruta | Contenido |
| --- | --- |
| `index.html`, `css/`, `js/` | La página web |
| `models/ocelote.glb` | Modelo para la web y Android (5.6 MB, Draco, texturas JPEG 2048/1024) |
| `models/ocelote.usdz` | Modelo para iPhone / iPad (AR Quick Look) con voz y comportamientos |
| `vendor/model-viewer.min.js` | [`<model-viewer>`](https://modelviewer.dev) 4.4.0 de Google |
| `vendor/draco/` | Decodificador Draco (de three.js) para leer el modelo comprimido |
| `audio/ocelote.mp3` | Voz del Ocelote (45 s, sincronizada con la animación) |
| `qr/ocelote-qr.png` / `.svg` | Código QR que abre la página |
| `qr/imprimir.html` | Hoja lista para imprimir con el QR e instrucciones |
| `source/ocelotechido_promo.fbx` | Modelo original (Blender) |
| `tools/` | Scripts para reconvertir el modelo y regenerar el QR |

## Animación y audio

El FBX trae una animación (`Promo_UNACH`, 1351 cuadros a 30 fps = 45 s) que mueve el
esqueleto y 10 gestos faciales (shape keys: boca, parpadeo, ojos, orejas). El formato FBX no
guarda sonido, así que la voz va aparte en `audio/ocelote.mp3`; dura lo mismo y la boca
coincide con ella. Mientras suena, la página corrige cualquier desfase entre voz y animación.

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

Si actualizas el FBX en Blender, reemplaza `source/ocelotechido_promo.fbx` y ejecuta
(requiere Python 3.13, Node y ffmpeg):

```bash
python3 -m venv venv && venv/bin/pip install bpy==5.2.4 usd-core
(cd tools && npm install)

# Web / Android
PY=venv/bin/python tools/build.sh source/ocelotechido_promo.fbx models/ocelote.glb

# iPhone / iPad
ffmpeg -i audio/ocelote.mp3 -c:a aac -b:a 128k voz.m4a
venv/bin/python tools/make_usdz.py source/ocelotechido_promo.fbx models/ocelote.usdz --audio voz.m4a
```

Ambos scripts usan Blender (como librería de Python) para leer el FBX y colocan los pies del
Ocelote a la altura del piso. `build.sh` exporta el GLB y lo optimiza con glTF-Transform
(texturas a 2048/1024 px en JPEG y compresión Draco). Después de regenerar, sube el número
`?v=` de `src` / `ios-src` en `index.html` para que los celulares no usen la versión en caché.

## iPhone / iPad (AR Quick Look)

Safari en iOS no admite AR dentro de la página (WebXR), así que el botón **Ver en tu espacio**
abre el visor de Apple con `models/ocelote.usdz`. Ese visor no muestra los botones de la
página ni reproduce su audio, así que el archivo trae la voz integrada y "comportamientos"
de Apple (el mismo esquema que usa Reality Composer):

- Al aparecer en tu espacio, el Ocelote promociona (animación + gestos + voz).
- Al tocarlo, vuelve a empezar desde el inicio.
