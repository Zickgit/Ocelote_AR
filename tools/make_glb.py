# Convierte el FBX del Ocelote a GLB para la web (model-viewer / Scene Viewer).
# Uso: python make_glb.py entrada.fbx salida.glb      (requiere: pip install bpy==5.2.4)
# Después se optimiza con glTF-Transform (ver tools/build.sh).
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from feet_on_floor import feet_on_floor
fbx, out = sys.argv[-2], sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)
feet_on_floor()
bpy.ops.export_scene.gltf(
    filepath=out, export_format='GLB',
    export_animations=True, export_animation_mode='ACTIVE_ACTIONS',  # huesos + gestos en una sola animación
    export_morph=True, export_morph_animation=True, export_morph_normal=False,
    export_skins=True, export_yup=True, export_apply=False,
    export_image_format='JPEG', export_image_quality=88, export_cameras=False, export_lights=False)
print('wrote', out)
