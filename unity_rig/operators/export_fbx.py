"""One-click FBX export optimized for Unity Humanoid import."""

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper

from ..bone_data import ALL_BONE_NAMES


class UNITYRIG_OT_export_fbx(bpy.types.Operator, ExportHelper):
    """Export the Unity Rig as FBX with optimal settings for Unity Humanoid"""

    bl_idname = "unity_rig.export_fbx"
    bl_label = "Export Unity FBX"
    bl_options = {'REGISTER'}

    filename_ext = ".fbx"

    filter_glob: StringProperty(
        default="*.fbx",
        options={'HIDDEN'},
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj is not None and obj.type == 'ARMATURE')

    def execute(self, context):
        arm_obj = context.active_object
        props = context.scene.unity_rig

        # Select armature and its mesh children for export
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        arm_obj.select_set(True)
        context.view_layer.objects.active = arm_obj

        object_types = {'ARMATURE'}
        if props.export_meshes:
            object_types.add('MESH')
            for child in arm_obj.children:
                if child.type == 'MESH':
                    child.select_set(True)

        # Determine export path
        filepath = self.filepath
        if not filepath:
            filepath = bpy.path.abspath(props.export_path)

        # Ensure .fbx extension
        if not filepath.lower().endswith('.fbx'):
            filepath += '.fbx'

        # Pre-export: ensure all DEF bones have use_deform=True
        # and all non-DEF bones have use_deform=False
        for bone in arm_obj.data.bones:
            if bone.name in ALL_BONE_NAMES:
                bone.use_deform = True
            elif not bone.name.startswith("DEF-"):
                # Also keep any bones explicitly marked as deform
                # (e.g. from Rigify conversion)
                pass

        # Export FBX with Unity-optimal settings
        try:
            bpy.ops.export_scene.fbx(
                filepath=filepath,
                use_selection=True,
                object_types=object_types,

                # Armature settings
                use_armature_deform_only=True,  # Only export deform bones
                add_leaf_bones=False,            # Unity doesn't need leaf bones
                primary_bone_axis='Y',
                secondary_bone_axis='X',
                armature_nodetype='NULL',

                # Transform settings
                apply_unit_scale=True,
                apply_scale_options='FBX_SCALE_ALL',
                axis_forward='-Z',
                axis_up='Y',
                global_scale=1.0,

                # Mesh settings
                use_mesh_modifiers=True,
                mesh_smooth_type='FACE',
                use_tspace=True,

                # Animation settings
                bake_anim=props.export_animations,
                bake_anim_use_all_bones=True,
                bake_anim_use_nla_strips=False,
                bake_anim_use_all_actions=False,
                bake_anim_force_startend_keying=True,
                bake_anim_simplify_factor=1.0,

                # Other
                path_mode='AUTO',
                embed_textures=False,
                batch_mode='OFF',
                use_batch_own_dir=False,
                use_metadata=True,
            )
        except Exception as e:
            self.report({'ERROR'}, f"FBX export failed: {e}")
            return {'CANCELLED'}

        self.report({'INFO'},
                    f"Exported Unity FBX to: {filepath}\n"
                    "Import in Unity and set Animation Type to 'Humanoid' "
                    "in the Rig tab of the import settings.")
        return {'FINISHED'}

    def invoke(self, context, event):
        # Use the stored export path as default, or open file browser
        props = context.scene.unity_rig
        if props.export_path and props.export_path != "//export.fbx":
            self.filepath = bpy.path.abspath(props.export_path)
        else:
            arm_name = context.active_object.name.replace(" ", "_")
            self.filepath = f"{arm_name}.fbx"
        return super().invoke(context, event)


classes = (
    UNITYRIG_OT_export_fbx,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
