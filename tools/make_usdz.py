# Genera USDZ animados para AR Quick Look (iPhone / iPad) a partir del FBX.
#
# Uso:
#   python make_usdz.py entrada.fbx salida.usdz                       # secuencia en bucle
#   python make_usdz.py entrada.fbx salida.usdz --seq Hablar --audio voz.mp3
#
# Requiere: pip install bpy==5.2.4 usd-core   (Python 3.13)
import argparse, os, shutil, sys, tempfile, zipfile
import bpy

ap = argparse.ArgumentParser()
ap.add_argument('fbx'); ap.add_argument('out')
ap.add_argument('--seq', default='Saludo,Idle,Idle,Celebrar,Idle,Idle',
                help='animaciones a encadenar, separadas por comas')
ap.add_argument('--audio', help='audio (mp3/m4a/wav) que se reproduce junto con la animación')
args = ap.parse_args(sys.argv[1:])

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=os.path.abspath(args.fbx))
sc = bpy.context.scene
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
acts = {a.name.split('|')[-1]: a for a in bpy.data.actions}

# Quick Look reproduce una sola línea de tiempo en bucle: encadenamos animaciones con NLA.
ad = rig.animation_data or rig.animation_data_create()
ad.action = None
track = ad.nla_tracks.new(); track.name = 'Secuencia'
frame = 1
for name in args.seq.split(','):
    a = acts[name]
    start, end = a.frame_range
    strip = track.strips.new(name, int(frame), a)
    strip.blend_in = strip.blend_out = 0
    strip.extrapolation = 'NOTHING'
    frame += (end - start)  # el último cuadro de cada clip coincide con el primero del siguiente
sc.frame_start, sc.frame_end = 1, int(frame)

for m in bpy.data.materials:
    bsdf = m.node_tree and m.node_tree.nodes.get('Principled BSDF')
    if bsdf and 'metal' in m.name.lower():
        bsdf.inputs['Metallic'].default_value = 0.85

tmp = tempfile.mkdtemp()
usdc = os.path.join(tmp, 'ocelote.usdc')
bpy.ops.wm.usd_export(filepath=usdc, export_animation=True, export_armatures=True,
    only_deform_bones=True, export_materials=True, generate_preview_surface=True,
    convert_orientation=True, export_global_forward_selection='NEGATIVE_Z', export_global_up_selection='Y',
    export_lights=False, export_cameras=False, triangulate_meshes=True,
    convert_scene_units='METERS', root_prim_path='/root')

from pxr import Sdf, Usd, UsdMedia, UsdUtils

if args.audio:
    audio_name = 'voz' + os.path.splitext(args.audio)[1].lower()
    shutil.copy(args.audio, os.path.join(tmp, audio_name))
    stage = Usd.Stage.Open(usdc)
    sa = UsdMedia.SpatialAudio.Define(stage, '/root/Voz')
    sa.CreateFilePathAttr(Sdf.AssetPath(audio_name))
    sa.CreateAuralModeAttr(UsdMedia.Tokens.nonSpatial)
    sa.CreatePlaybackModeAttr(UsdMedia.Tokens.loopFromStage)  # se repite junto con la animación
    sa.CreateStartTimeAttr(Sdf.TimeCode(stage.GetStartTimeCode()))
    sa.CreateEndTimeAttr(Sdf.TimeCode(stage.GetEndTimeCode()))
    sa.CreateGainAttr(1.0)
    stage.GetRootLayer().Save()

out = os.path.abspath(args.out)
if os.path.exists(out): os.remove(out)
ok = UsdUtils.CreateNewARKitUsdzPackage(Sdf.AssetPath(usdc), out)
print('usdz', ok, out)
print('files:', [i.filename for i in zipfile.ZipFile(out).infolist()])
shutil.rmtree(tmp)
