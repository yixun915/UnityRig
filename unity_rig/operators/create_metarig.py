"""Operator to create a Unity Humanoid metarig template."""

import bpy
from bpy.props import BoolProperty
from mathutils import Vector

from ..bone_data import UNITY_BONES, FINGER_BONES, BONE_COLLECTIONS
from ..utils import (
    ensure_object_mode, ensure_edit_mode,
    get_or_create_bone_collection, create_edit_bone,
    assign_bone_collections_batch,
    create_circle_widget, create_cube_widget, create_sphere_widget,
    set_bone_widget, set_bone_color,
)


class UNITYRIG_OT_create_metarig(bpy.types.Operator):
    """Create a Unity Humanoid metarig template for positioning"""

    bl_idname = "unity_rig.create_metarig"
    bl_label = "Create Unity Metarig"
    bl_options = {'REGISTER', 'UNDO'}

    include_fingers: BoolProperty(default=True)
    include_eyes: BoolProperty(default=True)

    def execute(self, context):
        props = context.scene.unity_rig
        include_fingers = props.include_fingers
        include_eyes = props.include_eyes

        ensure_object_mode()

        # Create armature
        arm_data = bpy.data.armatures.new("UnityRig_Metarig")
        arm_obj = bpy.data.objects.new("UnityRig_Metarig", arm_data)
        context.collection.objects.link(arm_obj)
        context.view_layer.objects.active = arm_obj
        arm_obj.select_set(True)

        # Tag as a Unity Rig metarig
        arm_data["unity_rig_metarig"] = True

        # Create bone collections.
        # NOTE: DEF is normally hidden on the generated rig, but during metarig
        # editing the user needs to see and position these bones, so force it
        # visible here. generate_rig will hide it again when it runs.
        for coll_name, coll_props in BONE_COLLECTIONS.items():
            visible = True if coll_name == "DEF" else coll_props["visible"]
            get_or_create_bone_collection(arm_obj, coll_name, visible)

        # --- Edit mode: create bones ---
        ensure_edit_mode(arm_obj)

        bones_to_create = list(UNITY_BONES)

        # Filter optional bones
        if not include_eyes:
            skip_names = {"LeftEye", "RightEye", "Jaw"}
            bones_to_create = [b for b in bones_to_create if b[0] not in skip_names]

        if include_fingers:
            bones_to_create += FINGER_BONES

        created_bones = []
        for name, parent, head, tail_offset, roll, is_required in bones_to_create:
            tail = head + tail_offset
            bone = create_edit_bone(
                arm_obj, name,
                head=head, tail=tail,
                parent_name=parent,
                roll=roll,
                use_deform=True,  # metarig bones are all deform for now
            )
            created_bones.append(name)

        # Set connected flag for chain bones (child head == parent tail)
        edit_bones = arm_obj.data.edit_bones
        for eb in edit_bones:
            if eb.parent is not None:
                if (eb.head - eb.parent.tail).length < 0.001:
                    eb.use_connect = True

        # --- Back to object mode for collection assignment and widgets ---
        bpy.ops.object.mode_set(mode='OBJECT')

        # Assign all metarig bones to DEF collection
        assign_bone_collections_batch(arm_obj, {
            "DEF": created_bones,
        })

        # Create widgets for visual feedback in pose mode
        self._assign_metarig_widgets(arm_obj, created_bones, include_fingers)

        # Set viewport display
        arm_obj.show_in_front = True
        arm_data.display_type = 'OCTAHEDRAL'

        self.report({'INFO'}, f"Created Unity metarig with {len(created_bones)} bones. "
                              "Position bones in Edit Mode to fit your mesh, then Generate Rig.")
        return {'FINISHED'}

    def _assign_metarig_widgets(self, arm_obj, bone_names, include_fingers):
        """Assign color coding to metarig bones for visual clarity."""
        # Color scheme: center=THEME09 (yellow), left=THEME01 (red), right=THEME04 (green)
        center_bones = {"Root", "Hips", "Spine", "Chest", "UpperChest",
                        "Neck", "Head", "Jaw"}
        left_prefix = "Left"
        right_prefix = "Right"

        for bname in bone_names:
            if bname in center_bones:
                set_bone_color(arm_obj, bname, 'THEME09')
            elif bname.startswith(left_prefix):
                set_bone_color(arm_obj, bname, 'THEME01')
            elif bname.startswith(right_prefix):
                set_bone_color(arm_obj, bname, 'THEME04')


def menu_func(self, context):
    """Draw callback for the Add > Armature menu entry."""
    self.layout.operator(
        UNITYRIG_OT_create_metarig.bl_idname,
        text="Unity Humanoid (Metarig)",
        icon='ARMATURE_DATA',
    )


classes = (
    UNITYRIG_OT_create_metarig,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_armature_add.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_armature_add.remove(menu_func)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
