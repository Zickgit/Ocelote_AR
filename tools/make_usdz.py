# Genera un USDZ animado para AR Quick Look (iOS) a partir del FBX.
# Uso: python make_usdz.py entrada.fbx salida.usdz
import bpy, sys
fbx, out = sys.argv[-2], sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)
sc = bpy.context.scene
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
acts = {a.name.split('|')[-1]: a for a in bpy.data.actions}

# Quick Look reproduce una sola línea de tiempo en bucle: encadenamos animaciones con NLA.
SEQUENCE = ['Saludo', 'Idle', 'Idle', 'Celebrar', 'Idle', 'Idle']
ad = rig.animation_data or rig.animation_data_create()
ad.action = None
track = ad.nla_tracks.new(); track.name = 'Secuencia'
frame = 1
for name in SEQUENCE:
    a = acts[name]
    start, end = a.frame_range
    strip = track.strips.new(name, int(frame), a)
    strip.blend_in = strip.blend_out = 0
    strip.extrapolation = 'NOTHING'
    frame += (end - start)  # el último cuadro de cada clip coincide con el primero del siguiente
sc.frame_start, sc.frame_end = 1, int(frame)
print('frames', sc.frame_start, sc.frame_end, 'fps', sc.render.fps)
for o in bpy.data.objects: print(o.name, tuple(round(v, 4) for v in o.scale), tuple(round(v, 3) for v in o.rotation_euler))

# Materiales: color base viene en espacio lineal, igual que Blender; solo ajustamos el metal.
for m in bpy.data.materials:
    bsdf = m.node_tree and m.node_tree.nodes.get('Principled BSDF')
    if bsdf and 'metal' in m.name.lower():
        bsdf.inputs['Metallic'].default_value = 0.85

bpy.ops.wm.usd_export(filepath=out, export_animation=True, export_armatures=True,
    only_deform_bones=True, export_materials=True, generate_preview_surface=True,
    convert_orientation=True, export_global_forward_selection='NEGATIVE_Z', export_global_up_selection='Y',
    export_lights=False, export_cameras=False, triangulate_meshes=True,
    convert_scene_units='METERS', root_prim_path='/root')
print('wrote', out)
