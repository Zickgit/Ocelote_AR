# Genera USDZ animados para AR Quick Look (iPhone / iPad) a partir del FBX.
#
# Uso:
#   python make_usdz.py entrada.fbx salida.usdz                       # secuencia en bucle
#   python make_usdz.py entrada.fbx salida.usdz --talk voz.m4a           # habla con voz (interactivo)
#
# Modo --talk: AR Quick Look solo reproduce audio mediante los "behaviors" de Apple
# (esquema Preliminary_* de Reality Composer). Al aparecer, el Ocelote habla con su voz
# y después queda en reposo; al tocarlo, vuelve a hablar.
#
# Requiere: pip install bpy==5.2.4 usd-core   (Python 3.13)
import argparse, os, shutil, sys, tempfile, zipfile
import bpy

ap = argparse.ArgumentParser()
ap.add_argument('fbx'); ap.add_argument('out')
ap.add_argument('--seq', default='Saludo,Idle,Idle,Celebrar,Idle,Idle',
                help='animaciones a encadenar, separadas por comas')
ap.add_argument('--talk', metavar='AUDIO', help='audio (m4a/mp3/wav) de la animación Hablar; activa el modo interactivo')
args = ap.parse_args(sys.argv[1:])
if args.talk:
    args.seq = 'Hablar,Idle'

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
segments = {}  # nombre -> (inicio, duración) en segundos
for name in args.seq.split(','):
    a = acts[name]
    start, end = a.frame_range
    strip = track.strips.new(name, int(frame), a)
    strip.blend_in = strip.blend_out = 0
    strip.extrapolation = 'NOTHING'
    segments.setdefault(name, ((frame - 1) / sc.render.fps, (end - start) / sc.render.fps))
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

from pxr import Sdf, Usd, UsdUtils

def action(stage, path, kind, **attrs):
    """Crea un Preliminary_Action de AR Quick Look."""
    prim = stage.DefinePrim(path, 'Preliminary_Action')
    prim.CreateAttribute('info:id', Sdf.ValueTypeNames.Token, variability=Sdf.VariabilityUniform).Set(kind)
    for k, (typ, val) in attrs.items():
        if typ == 'rel':
            prim.CreateRelationship(k).SetTargets([Sdf.Path(v) for v in val])
        else:
            prim.CreateAttribute(k, typ, variability=Sdf.VariabilityUniform).Set(val)
    return prim.GetPath()

def trigger(stage, path, kind, **attrs):
    prim = stage.DefinePrim(path, 'Preliminary_Trigger')
    prim.CreateAttribute('info:id', Sdf.ValueTypeNames.Token, variability=Sdf.VariabilityUniform).Set(kind)
    for k, (typ, val) in attrs.items():
        if typ == 'rel':
            prim.CreateRelationship(k).SetTargets([Sdf.Path(v) for v in val])
        else:
            prim.CreateAttribute(k, typ, variability=Sdf.VariabilityUniform).Set(val)
    return prim.GetPath()

def behavior(stage, path, triggers, actions):
    prim = stage.DefinePrim(path, 'Preliminary_Behavior')
    prim.CreateRelationship('triggers').SetTargets(triggers)
    prim.CreateRelationship('actions').SetTargets(actions)
    prim.CreateAttribute('exclusive', Sdf.ValueTypeNames.Bool, variability=Sdf.VariabilityUniform).Set(True)

stage = Usd.Stage.Open(usdc)
root = stage.GetPrimAtPath('/root')
root.AddAppliedSchema('Preliminary_AnchoringAPI')
root.CreateAttribute('preliminary:anchoring:type', Sdf.ValueTypeNames.Token, variability=Sdf.VariabilityUniform).Set('plane')
root.CreateAttribute('preliminary:planeAnchoring:alignment', Sdf.ValueTypeNames.Token, variability=Sdf.VariabilityUniform).Set('horizontal')

if args.talk:
    audio_name = 'voz' + os.path.splitext(args.talk)[1].lower()
    shutil.copy(args.talk, os.path.join(tmp, audio_name))
    T, V, B, I = Sdf.ValueTypeNames.Token, Sdf.ValueTypeNames.Double, Sdf.ValueTypeNames.Bool, Sdf.ValueTypeNames.Int
    model = '/root/Ocelote_Rig'
    (h0, hd), (i0, idur) = segments['Hablar'], segments['Idle']

    def talk_then_idle(base):
        """Hablar + voz en paralelo, luego Idle en bucle."""
        anim = action(stage, base + '/AnimHablar', 'StartAnimation', affectedObjects=('rel', [model]),
                      start=(V, h0), duration=(V, hd), animationSpeed=(V, 1.0), reversed=(B, False),
                      reverses=(B, False), multiplePerformOperation=(T, 'allow'))
        voz = action(stage, base + '/Voz', 'Audio', affectedObjects=('rel', [model]),
                     audio=(Sdf.ValueTypeNames.Asset, Sdf.AssetPath(audio_name)), type=(T, 'play'),
                     gain=(V, 1.0), auralMode=(T, 'nonSpatial'), multiplePerformOperation=(T, 'allow'))
        hablar = action(stage, base + '/Hablar', 'Group', actions=('rel', [str(anim), str(voz)]),
                        type=(T, 'parallel'), loops=(B, False), performCount=(I, 1))
        idle_anim = action(stage, base + '/AnimIdle', 'StartAnimation', affectedObjects=('rel', [model]),
                           start=(V, i0), duration=(V, idur), animationSpeed=(V, 1.0), reversed=(B, False),
                           reverses=(B, False), multiplePerformOperation=(T, 'allow'))
        idle = action(stage, base + '/Reposo', 'Group', actions=('rel', [str(idle_anim)]),
                      type=(T, 'serial'), loops=(B, True), performCount=(I, 0))
        return action(stage, base + '/Secuencia', 'Group', actions=('rel', [str(hablar), str(idle)]),
                      type=(T, 'serial'), loops=(B, False), performCount=(I, 1))

    stage.DefinePrim('/root/Comportamientos', 'Scope')
    t_enter = trigger(stage, '/root/Comportamientos/AlAparecer/Trigger', 'SceneTransition', type=(T, 'enter'))
    behavior(stage, '/root/Comportamientos/AlAparecer', [t_enter], [talk_then_idle('/root/Comportamientos/AlAparecer')])
    t_tap = trigger(stage, '/root/Comportamientos/AlTocar/Trigger', 'TapGesture', affectedObjects=('rel', [model]))
    behavior(stage, '/root/Comportamientos/AlTocar', [t_tap], [talk_then_idle('/root/Comportamientos/AlTocar')])

stage.GetRootLayer().Save()

out = os.path.abspath(args.out)
if os.path.exists(out): os.remove(out)
ok = UsdUtils.CreateNewARKitUsdzPackage(Sdf.AssetPath(usdc), out)
print('usdz', ok, out)
print('files:', [i.filename for i in zipfile.ZipFile(out).infolist()])
shutil.rmtree(tmp)
