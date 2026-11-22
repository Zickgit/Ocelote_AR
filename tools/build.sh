#!/usr/bin/env bash
# usage: build.sh input.fbx output.glb
set -euo pipefail
T=$(mktemp -d)
node "$(dirname "$0")/convert.mjs" "$1" "$T/raw.glb"
npx gltf-transform weld "$T/raw.glb" "$T/w.glb"
npx gltf-transform resample "$T/w.glb" "$T/r.glb"
npx gltf-transform prune "$T/r.glb" "$T/p.glb"
npx gltf-transform draco "$T/p.glb" "$2"
rm -rf "$T"
