#!/usr/bin/env bash
# Genera models/ocelote.glb desde el FBX.
# Uso: tools/build.sh source/ocelotechido_promo.fbx models/ocelote.glb
# Requiere: Python con bpy==5.2.4 (variable PY, por defecto python3) y `npm install` en tools/
set -euo pipefail
PY=${PY:-python3}
HERE="$(cd "$(dirname "$0")" && pwd)"
IN="$(realpath "$1")"; OUT="$(realpath -m "$2")"
T=$(mktemp -d)
"$PY" "$HERE/make_glb.py" "$IN" "$T/raw.glb"
cd "$HERE"
npx gltf-transform resample "$T/raw.glb" "$T/a.glb"
npx gltf-transform prune "$T/a.glb" "$T/b.glb"
npx gltf-transform resize "$T/b.glb" "$T/c.glb" --width 2048 --height 2048 --pattern "*BaseColor*"
npx gltf-transform resize "$T/c.glb" "$T/d.glb" --width 1024 --height 1024 --pattern "*Normal*"
npx gltf-transform draco "$T/d.glb" "$OUT"
rm -rf "$T"
