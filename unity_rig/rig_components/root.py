"""Root and Hips rig component."""

from mathutils import Vector
from ..utils import (
    create_edit_bone, add_copy_transforms_constraint,
    create_circle_widget, set_bone_widget, set_bone_color,
    lock_bone_transforms,
)


def create_root_bones(arm_obj):
    """Create root and hip control bones in EDIT mode.

    IMPORTANT: DEF bones keep their original hierarchy for FBX export.
    CTRL bones form their own chain.  Constraints link DEF -> CTRL.

    Returns list of (bone_name, collection_name) tuples.
    """
    edit_bones = arm_obj.data.edit_bones

    def_root = edit_bones.get("Root")
    def_hips = edit_bones.get("Hips")
    if def_root is None or def_hips is None:
        return []

    assignments = []

    # CTRL-Root: master control at origin
    create_edit_bone(
        arm_obj, "CTRL-Root",
        head=def_root.head.copy(),
        tail=def_root.head + Vector((0, 0.3, 0)),
        parent_name=None,
        use_deform=False,
    )
    assignments.append(("CTRL-Root", "CTRL"))

    # CTRL-Hips: hip control, parented to CTRL-Root
    create_edit_bone(
        arm_obj, "CTRL-Hips",
        head=def_hips.head.copy(),
        tail=def_hips.tail.copy(),
        parent_name="CTRL-Root",
        use_deform=False,
    )
    assignments.append(("CTRL-Hips", "CTRL"))

    # DEF bones keep their original parents (Root->None, Hips->Root)
    # Constraints will make them follow the CTRL bones.

    return assignments


def setup_root_constraints(arm_obj):
    """Set up constraints for root/hips in POSE mode."""
    add_copy_transforms_constraint(arm_obj, "Root", "CTRL-Root", name="Follow Root")
    add_copy_transforms_constraint(arm_obj, "Hips", "CTRL-Hips", name="Follow Hips")


def setup_root_widgets(arm_obj):
    """Create and assign widgets for root controls."""
    root_wgt = create_circle_widget("WGT_Root", radius=0.35, segments=24)
    set_bone_widget(arm_obj, "CTRL-Root", root_wgt)
    set_bone_color(arm_obj, "CTRL-Root", 'THEME09')
    lock_bone_transforms(arm_obj, "CTRL-Root",
                         lock_rot=(False, False, False),
                         lock_loc=(False, False, False),
                         lock_scale=(True, True, True))

    hips_wgt = create_circle_widget("WGT_Hips", radius=0.2, segments=16)
    set_bone_widget(arm_obj, "CTRL-Hips", hips_wgt)
    set_bone_color(arm_obj, "CTRL-Hips", 'THEME09')
    lock_bone_transforms(arm_obj, "CTRL-Hips",
                         lock_rot=(False, False, False),
                         lock_loc=(False, False, False),
                         lock_scale=(True, True, True))
