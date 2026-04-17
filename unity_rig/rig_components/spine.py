"""Spine/torso rig component."""

from mathutils import Vector
from ..utils import (
    create_edit_bone, add_copy_rotation_constraint,
    create_circle_widget, set_bone_widget, set_bone_color,
    lock_bone_transforms,
)

# Spine DEF bones in order
SPINE_CHAIN = ["Spine", "Chest", "UpperChest"]


def create_spine_bones(arm_obj):
    """Create spine control bones in EDIT mode.

    DEF bones keep their original hierarchy (Hips->Spine->Chest->UpperChest).
    CTRL bones form their own chain (CTRL-Hips->CTRL-Spine->CTRL-Chest->CTRL-UpperChest).

    Returns list of (bone_name, collection_name) tuples.
    """
    edit_bones = arm_obj.data.edit_bones
    assignments = []

    prev_ctrl = "CTRL-Hips"

    for def_name in SPINE_CHAIN:
        def_bone = edit_bones.get(def_name)
        if def_bone is None:
            continue

        ctrl_name = f"CTRL-{def_name}"
        create_edit_bone(
            arm_obj, ctrl_name,
            head=def_bone.head.copy(),
            tail=def_bone.tail.copy(),
            parent_name=prev_ctrl,
            use_deform=False,
        )
        assignments.append((ctrl_name, "CTRL"))

        # DEF bone keeps its original parent — do NOT reparent.
        # Constraints in setup_spine_constraints() link DEF -> CTRL.

        prev_ctrl = ctrl_name

    return assignments


def setup_spine_constraints(arm_obj):
    """Set up spine constraints in POSE mode."""
    for def_name in SPINE_CHAIN:
        ctrl_name = f"CTRL-{def_name}"
        pb = arm_obj.pose.bones.get(ctrl_name)
        if pb is None:
            continue
        add_copy_rotation_constraint(arm_obj, def_name, ctrl_name,
                                     name="Follow Spine CTRL")


def setup_spine_widgets(arm_obj):
    """Create and assign widgets for spine controls."""
    sizes = {"Spine": 0.15, "Chest": 0.17, "UpperChest": 0.16}

    for def_name in SPINE_CHAIN:
        ctrl_name = f"CTRL-{def_name}"
        pb = arm_obj.pose.bones.get(ctrl_name)
        if pb is None:
            continue

        radius = sizes.get(def_name, 0.15)
        wgt = create_circle_widget(f"WGT_{ctrl_name}", radius=radius, segments=16)
        set_bone_widget(arm_obj, ctrl_name, wgt)
        set_bone_color(arm_obj, ctrl_name, 'THEME09')
        lock_bone_transforms(arm_obj, ctrl_name,
                             lock_loc=(True, True, True),
                             lock_rot=(False, False, False),
                             lock_scale=(True, True, True))
