import fs from 'fs';
import * as THREE from 'three';
import { FBXLoader } from 'three/examples/jsm/loaders/FBXLoader.js';
import { GLTFExporter } from 'three/examples/jsm/exporters/GLTFExporter.js';

// Minimal FileReader polyfill for GLTFExporter in Node
globalThis.FileReader = class {
  readAsArrayBuffer(blob) { blob.arrayBuffer().then(r => { this.result = r; this.onloadend && this.onloadend(); }); }
  readAsDataURL(blob) { blob.arrayBuffer().then(r => { this.result = 'data:' + (blob.type || 'application/octet-stream') + ';base64,' + Buffer.from(r).toString('base64'); this.onloadend && this.onloadend(); }); }
};

const [inp, out] = process.argv.slice(2);
const buf = fs.readFileSync(inp);
const root = new FBXLoader().parse(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength), '');

// Phong (FBX) -> PBR standard materials
const cache = new Map();
const toStd = (m) => {
  if (cache.has(m.uuid)) return cache.get(m.uuid);
  const metal = /metal/i.test(m.name);
  // Blender's FBX exporter writes shininess = ((1 - roughness) * 10)^2
  const rough = Math.min(1, Math.max(0.05, 1 - Math.sqrt(m.shininess) / 10));
  // Blender writes base colors in linear space; FBXLoader assumed sRGB, so undo that conversion
  const color = m.color.clone().convertLinearToSRGB();
  const s = new THREE.MeshStandardMaterial({ name: m.name, color, roughness: rough, metalness: metal ? 0.85 : 0.0 });
  cache.set(m.uuid, s); return s;
};
root.traverse(o => { if (o.isMesh) o.material = Array.isArray(o.material) ? o.material.map(toStd) : toStd(o.material); });

// Merge many small material groups into one group per material (fewer draw calls)
root.traverse(o => {
  if (!o.isMesh || !o.geometry.groups.length) return;
  const g = o.geometry, n = g.attributes.position.count;
  const idx = g.index ? g.index.array : Array.from({ length: n }, (_, i) => i);
  const byMat = new Map();
  for (const gr of g.groups) {
    const arr = byMat.get(gr.materialIndex) || []; byMat.set(gr.materialIndex, arr);
    for (let i = gr.start; i < gr.start + gr.count; i++) arr.push(idx[i]);
  }
  const out = []; g.clearGroups();
  for (const [mi, arr] of [...byMat.entries()].sort((a, b) => a[0] - b[0])) { g.addGroup(out.length, arr.length, mi); out.push(...arr); }
  g.setIndex(out);
});

// Clean clip names: "Ocelote_Rig|Saludo" -> "Saludo"
const clips = root.animations.map(c => { c.name = c.name.split('|').pop(); return c; });
// Put Idle first so viewers that autoplay the first clip show a calm loop
clips.sort((a, b) => (b.name === 'Idle') - (a.name === 'Idle'));

new GLTFExporter().parse(root, (glb) => {
  fs.writeFileSync(out, Buffer.from(glb));
  console.log('wrote', out, (glb.byteLength / 1e6).toFixed(2), 'MB', clips.map(c => c.name));
}, (e) => { console.error(e); process.exit(1); }, { binary: true, animations: clips, onlyVisible: true });
