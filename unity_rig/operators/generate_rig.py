"""Operator to generate a full animation rig from a Unity metarig."""

import bpy
from bpy.props import StringProperty

from ..bone_data import BONE_COLLECTIONS, ALL_BONE_NAMES, LIMB_DEFS
from ..rig_components import root, spine, limb, head, hand
from ..utils import (
    ensure_object_mode, ensure_edit_mode, ensure_pose_mode,
    get_or_create_bone_collection, assign_bone_collections_batch,
)


class UNITYRIG_OT_generate_rig(bpy.types.Operator):
    """Generate a full animation rig from the positioned metarig"""

    bl_idname = "unity_rig.generate_rig"
    bl_label = "Generate Unity Rig"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj is not None
                and obj.type == 'ARMATURE'
                and obj.data.get("unity_rig_metarig") is not None)

    def execute(self, context):
        arm_obj = context.active_object
        props = context.scene.unity_rig
        ik_fk_default = props.ik_fk_default

        # Ensure we have bone collections
        ensure_object_mode()
        for coll_name, coll_props in BONE_COLLECTIONS.items():
            get_or_create_bone_collection(arm_obj, coll_name, coll_props["visible"])

        # ---------------------------------------------------------------
        # EDIT MODE: Create all control and mechanism bones
        # ---------------------------------------------------------------
        ensure_edit_mode(arm_obj)

        all_assignments = []  # (bone_name, collection_name)

        # Root + Hips
        all_assignments += root.create_root_bones(arm_obj)

        # Spine
        all_assignments += spine.create_spine_bones(arm_obj)

        # Head / Neck / Eyes / Jaw
        all_assignments += head.create_head_bones(arm_obj)

        # Limbs (IK/FK arms and legs)
        for limb_key in LIMB_DEFS:
            all_assignments += limb.create_limb_bones(arm_obj, limb_key)

        # Fingers
        include_fingers = props.include_fingers
        if include_fingers:
            for side in ["Left", "Right"]:
                all_assignments += hand.create_hand_bones(arm_obj, side)

        # Mark DEF bones
        for eb in arm_obj.data.edit_bones:
            if eb.name in ALL_BONE_NAMES:
                eb.use_deform = True
            else:
                eb.use_deform = False

        # ---------------------------------------------------------------
        # OBJECT MODE: Assign bone collections
        # ---------------------------------------------------------------
        bpy.ops.object.mode_set(mode='OBJECT')

        # Build collection assignment dict
        coll_dict = {}
        for bone_name, coll_name in all_assignments:
            coll_dict.setdefault(coll_name, []).append(bone_name)

        # DEF bones
        coll_dict.setdefault("DEF", [])
        for bname in ALL_BONE_NAMES:
            if arm_obj.data.bones.get(bname):
                coll_dict["DEF"].append(bname)

        assign_bone_collections_batch(arm_obj, coll_dict)

        # ---------------------------------------------------------------
        # POSE MODE: Set up constraints, drivers, and widgets
        # ---------------------------------------------------------------
        ensure_pose_mode(arm_obj)

        root.setup_root_constraints(arm_obj)
        spine.setup_spine_constraints(arm_obj)
        head.setup_head_constraints(arm_obj)

        for limb_key in LIMB_DEFS:
            limb.setup_limb_constraints(arm_obj, limb_key, ik_fk_default)

        if include_fingers:
            for side in ["Left", "Right"]:
                hand.setup_hand_constraints(arm_obj, side)

        # Widgets (still in pose mode)
        root.setup_root_widgets(arm_obj)
        spine.setup_spine_widgets(arm_obj)
        head.setup_head_widgets(arm_obj)

        for limb_key in LIMB_DEFS:
            limb.setup_limb_widgets(arm_obj, limb_key)

        if include_fingers:
            for side in ["Left", "Right"]:
                hand.setup_hand_widgets(arm_obj, side)

        # ---------------------------------------------------------------
        # Finalize
        # ---------------------------------------------------------------
        bpy.ops.object.mode_set(mode='OBJECT')

        # Tag as generated
        arm_obj.data["unity_rig_generated"] = True
        # Remove metarig tag (it's now a full rig)
        if "unity_rig_metarig" in arm_obj.data:
            del arm_obj.data["unity_rig_metarig"]

        # Set viewport display
        arm_obj.data.display_type = 'WIRE'
        arm_obj.show_in_front = True

        bone_count = len(arm_obj.data.bones)
        self.report({'INFO'},
                    f"Unity Rig generated: {bone_count} bones. "
                    f"Default mode: {ik_fk_default}. "
                    "Use the IK/FK panel to switch modes.")
        return {'FINISHED'}


class UNITYRIG_OT_snap_ik_to_fk(bpy.types.Operator):
    """Snap IK controls to match current FK pose"""

    bl_idname = "unity_rig.snap_ik_to_fk"
    bl_label = "Snap IK to FK"
    bl_options = {'REGISTER', 'UNDO'}

    limb_bone: StringProperty()

    def execute(self, context):
        arm_obj = context.active_object
        limb_key = self._resolve_limb_key(self.limb_bone)
        if limb_key:
            limb.snap_ik_to_fk(arm_obj, limb_key)
        return {'FINISHED'}

    def _resolve_limb_key(self, bone_name):
        for key, data in LIMB_DEFS.items():
            ik_name = f"CTRL-IK-{data['end']}"
            if bone_name == ik_name:
                return key
        return None


class UNITYRIG_OT_snap_fk_to_ik(bpy.types.Operator):
    """Snap FK controls to match current IK pose"""

    bl_idname = "unity_rig.snap_fk_to_ik"
    bl_label = "Snap FK to IK"
    bl_options = {'REGISTER', 'UNDO'}

    limb_bone: StringProperty()

    def execute(self, context):
        arm_obj = context.active_object
        limb_key = self._resolve_limb_key(self.limb_bone)
        if limb_key:
            limb.snap_fk_to_ik(arm_obj, limb_key)
        return {'FINISHED'}

    def _resolve_limb_key(self, bone_name):
        for key, data in LIMB_DEFS.items():
            ik_name = f"CTRL-IK-{data['end']}"
            if bone_name == ik_name:
                return key
        return None


classes = (
    UNITYRIG_OT_generate_rig,
    UNITYRIG_OT_snap_ik_to_fk,
    UNITYRIG_OT_snap_fk_to_ik,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
