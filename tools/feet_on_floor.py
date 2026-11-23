# Mueve el rig para que los pies del Ocelote queden a la altura 0 (el piso en AR).
import bpy

def feet_on_floor():
    sc = bpy.context.scene
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    sc.frame_set(sc.frame_start)
    dg = bpy.context.evaluated_depsgraph_get()
    minz = None
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        z = min((ev.matrix_world @ v.co).z for v in me.vertices)
        ev.to_mesh_clear()
        minz = z if minz is None else min(minz, z)
    rig.location.z -= minz
    print(f'feet_on_floor: rig desplazado {-minz:+.3f} m')
