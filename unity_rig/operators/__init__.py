from . import create_metarig
from . import generate_rig
from . import convert_rigify
from . import export_fbx
from . import select_bone


def register():
    create_metarig.register()
    generate_rig.register()
    convert_rigify.register()
    export_fbx.register()
    select_bone.register()


def unregister():
    select_bone.unregister()
    export_fbx.unregister()
    convert_rigify.unregister()
    generate_rig.unregister()
    create_metarig.unregister()
