# Genera el USDZ para AR Quick Look (iPhone / iPad) a partir del FBX.
#
# Uso:
#   python make_usdz.py entrada.fbx salida.usdz --audio voz.m4a
#
# Requiere: pip install bpy==5.2.4 usd-core   (Python 3.13)
#
# AR Quick Look no muestra botones de la página y solo reproduce audio mediante los
# "behaviors" de Apple (esquema Preliminary_* de Reality Composer). Este script agrega:
#   - al aparecer en tu espacio: animación + voz
#   - al tocar al Ocelote: animación + voz desde el inicio
import argparse, os, shutil, sys, tempfile, zipfile
import bpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from feet_on_floor import feet_on_floor

ap = argparse.ArgumentParser()
ap.add_argument('fbx'); ap.add_argument('out')
ap.add_argument('--audio', help='voz (m4a/mp3/wav) sincronizada con la animación')
args = ap.parse_args(sys.argv[1:])

tmp = tempfile.mkdtemp()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=os.path.abspath(args.fbx))
feet_on_floor()
sc = bpy.context.scene
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
start, end = rig.animation_data.action.frame_range
sc.frame_start, sc.frame_end = int(start), int(end)
fps = sc.render.fps

# Texturas más ligeras para el celular: color 2048 px, normal 1024 px, en JPEG.
os.makedirs(os.path.join(tmp, 'textures'))
sc.render.image_settings.quality = 88
for img in bpy.data.images:
    if img.size[0] == 0:
        continue
    size = 1024 if 'normal' in img.name.lower() else 2048
    if img.size[0] > size:
        img.scale(size, size)
    path = os.path.join(tmp, 'textures', img.name + '.jpg')
    img.save(filepath=path, quality=88) if bpy.app.version >= (4, 0, 0) else img.save_render(path)
    img.filepath = path
    img.source = 'FILE'
    if img.packed_file:
        img.unpack(method='REMOVE')
    img.filepath = path

usdc = os.path.join(tmp, 'ocelote.usdc')
bpy.ops.wm.usd_export(filepath=usdc, export_animation=True, export_armatures=True,
    only_deform_bones=True, export_shapekeys=True, export_materials=True, generate_preview_surface=True,
    export_textures_mode='KEEP', relative_paths=True,
    convert_orientation=True, export_global_forward_selection='NEGATIVE_Z', export_global_up_selection='Y',
    export_lights=False, export_cameras=False, triangulate_meshes=True,
    convert_scene_units='METERS', root_prim_path='/root')

from pxr import Sdf, Usd, UsdSkel, UsdUtils

stage = Usd.Stage.Open(usdc)
root = stage.GetPrimAtPath('/root')

# Blender guarda cada gesto con todos los puntos de la malla; dejamos solo los que se mueven.
from pxr import Vt
for p in stage.Traverse():
    if p.IsA(UsdSkel.BlendShape):
        bs = UsdSkel.BlendShape(p)
        offs = bs.GetOffsetsAttr().Get()
        idx = bs.GetPointIndicesAttr().Get() or list(range(len(offs)))
        keep = [i for i, o in enumerate(offs) if o.GetLength() > 1e-5]
        bs.GetOffsetsAttr().Set(Vt.Vec3fArray([offs[i] for i in keep]))
        bs.GetPointIndicesAttr().Set(Vt.IntArray([int(idx[i]) for i in keep]))
        if bs.GetNormalOffsetsAttr().HasAuthoredValue():
            nrm = bs.GetNormalOffsetsAttr().Get()
            bs.GetNormalOffsetsAttr().Set(Vt.Vec3fArray([nrm[i] for i in keep]))
U = Sdf.VariabilityUniform
T, V, B, I = Sdf.ValueTypeNames.Token, Sdf.ValueTypeNames.Double, Sdf.ValueTypeNames.Bool, Sdf.ValueTypeNames.Int

root.AddAppliedSchema('Preliminary_AnchoringAPI')
root.CreateAttribute('preliminary:anchoring:type', T, variability=U).Set('plane')
root.CreateAttribute('preliminary:planeAnchoring:alignment', T, variability=U).Set('horizontal')

def prim(path, type_name, **attrs):
    p = stage.DefinePrim(path, type_name)
    for k, (typ, val) in attrs.items():
        if typ == 'rel':
            p.CreateRelationship(k).SetTargets([Sdf.Path(str(v)) for v in val])
        else:
            p.CreateAttribute(k, typ, variability=U).Set(val)
    return p.GetPath()

skel_root = next(p for p in stage.Traverse() if p.IsA(UsdSkel.Root)).GetPath()
duration = (end - start) / fps

def promote(base):
    """Animación completa + voz, en paralelo."""
    acts = [prim(base + '/Animacion', 'Preliminary_Action', **{
        'info:id': (T, 'StartAnimation'), 'affectedObjects': ('rel', [skel_root]),
        'start': (V, 0.0), 'duration': (V, duration), 'animationSpeed': (V, 1.0),
        'reversed': (B, False), 'reverses': (B, False), 'multiplePerformOperation': (T, 'replace')})]
    if args.audio:
        acts.append(prim(base + '/Voz', 'Preliminary_Action', **{
            'info:id': (T, 'Audio'), 'affectedObjects': ('rel', [skel_root]),
            'audio': (Sdf.ValueTypeNames.Asset, Sdf.AssetPath(audio_name)), 'type': (T, 'play'),
            'gain': (V, 1.0), 'auralMode': (T, 'nonSpatial'), 'multiplePerformOperation': (T, 'replace')}))
    return prim(base + '/Promocionar', 'Preliminary_Action', **{
        'info:id': (T, 'Group'), 'actions': ('rel', acts), 'type': (T, 'parallel'),
        'loops': (B, False), 'performCount': (I, 1)})

if args.audio:
    audio_name = 'voz' + os.path.splitext(args.audio)[1].lower()
    shutil.copy(args.audio, os.path.join(tmp, audio_name))

stage.DefinePrim('/root/Comportamientos', 'Scope')
for name, trig in [('AlAparecer', dict(**{'info:id': (T, 'SceneTransition'), 'type': (T, 'enter')})),
                   ('AlTocar', dict(**{'info:id': (T, 'TapGesture'), 'affectedObjects': ('rel', [skel_root])}))]:
    base = '/root/Comportamientos/' + name
    stage.DefinePrim(base, 'Preliminary_Behavior')
    t = prim(base + '/Trigger', 'Preliminary_Trigger', **trig)
    a = promote(base)
    prim(base, 'Preliminary_Behavior', triggers=('rel', [t]), actions=('rel', [a]), exclusive=(B, True))
stage.GetRootLayer().Save()

out = os.path.abspath(args.out)
if os.path.exists(out):
    os.remove(out)
ok = UsdUtils.CreateNewARKitUsdzPackage(Sdf.AssetPath(usdc), out)
print('usdz', ok, out, f'{duration:.2f}s @ {fps}fps')
print('files:', [(i.filename, i.file_size) for i in zipfile.ZipFile(out).infolist()])
shutil.rmtree(tmp)
