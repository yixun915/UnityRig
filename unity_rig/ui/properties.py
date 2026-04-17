"""Scene and object properties for the Unity Rig addon."""

import bpy
from bpy.props import (
    BoolProperty, EnumProperty, FloatProperty, StringProperty, PointerProperty,
)


class UNITYRIG_SceneProperties(bpy.types.PropertyGroup):
    """Properties stored on the scene for Unity Rig operations."""

    include_fingers: BoolProperty(
        name="Include Fingers",
        description="Include finger bones in the rig (30 bones total)",
        default=True,
    )

    include_eyes: BoolProperty(
        name="Include Eyes",
        description="Include eye and jaw bones",
        default=True,
    )

    # Rig generation options
    ik_fk_default: EnumProperty(
        name="Default Limb Mode",
        description="Default IK/FK mode for generated limbs",
        items=[
            ('IK', "IK", "Start in Inverse Kinematics mode"),
            ('FK', "FK", "Start in Forward Kinematics mode"),
        ],
        default='IK',
    )

    # Export options
    export_path: StringProperty(
        name="Export Path",
        description="FBX export file path",
        default="//export.fbx",
        subtype='FILE_PATH',
    )

    export_animations: BoolProperty(
        name="Export Animations",
        description="Include animation data in FBX export",
        default=True,
    )

    export_meshes: BoolProperty(
        name="Export Meshes",
        description="Include mesh objects in FBX export",
        default=True,
    )

    # Rigify conversion options
    rigify_conversion_mode: EnumProperty(
        name="Conversion Mode",
        description="How to convert the Rigify rig",
        items=[
            ('DUPLICATE', "Duplicate",
             "Create a new Unity-compatible armature alongside the Rigify rig"),
            ('IN_PLACE', "In-Place",
             "Rename bones in the existing armature (destructive)"),
        ],
        default='DUPLICATE',
    )

    rigify_keep_controls: BoolProperty(
        name="Keep Rigify Controls",
        description="Preserve Rigify control bones when converting (Duplicate mode only)",
        default=False,
    )


classes = (
    UNITYRIG_SceneProperties,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.unity_rig = PointerProperty(type=UNITYRIG_SceneProperties)


def unregister():
    del bpy.types.Scene.unity_rig
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
