"""Head, neck, eyes, and jaw rig component."""

from mathutils import Vector
from ..utils import (
    create_edit_bone,
    add_copy_rotation_constraint, add_track_to_constraint,
    create_circle_widget, create_sphere_widget, create_diamond_widget,
    set_bone_widget, set_bone_color,
    lock_bone_transforms,
)


def create_head_bones(arm_obj):
    """Create head/neck control bones in EDIT mode.

    DEF bones keep their original hierarchy for FBX export.
    CTRL bones form their own chain.

    Returns list of (bone_name, collection_name) tuples.
    """
    edit_bones = arm_obj.data.edit_bones
    assignments = []

    # Find the last spine CTRL to parent neck CTRL to
    spine_parent = None
    for name in ["CTRL-UpperChest", "CTRL-Chest", "CTRL-Spine"]:
        if name in edit_bones:
            spine_parent = name
            break

    # Neck control
    def_neck = edit_bones.get("Neck")
    if def_neck:
        create_edit_bone(
            arm_obj, "CTRL-Neck",
            head=def_neck.head.copy(),
            tail=def_neck.tail.copy(),
            parent_name=spine_parent,
            use_deform=False,
        )
        assignments.append(("CTRL-Neck", "CTRL"))
        # DEF Neck keeps its original parent (UpperChest)

    # Head control
    def_head = edit_bones.get("Head")
    if def_head:
        neck_ctrl = "CTRL-Neck" if "CTRL-Neck" in edit_bones else spine_parent
        create_edit_bone(
            arm_obj, "CTRL-Head",
            head=def_head.head.copy(),
            tail=def_head.tail.copy(),
            parent_name=neck_ctrl,
            use_deform=False,
        )
        assignments.append(("CTRL-Head", "CTRL"))
        # DEF Head keeps its original parent (Neck)

    # Eye target (single target both eyes look at)
    def_left_eye = edit_bones.get("LeftEye")
    def_right_eye = edit_bones.get("RightEye")
    if def_left_eye and def_right_eye:
        eye_mid = (def_left_eye.head + def_right_eye.head) / 2
        target_pos = eye_mid + Vector((0, -0.5, 0))  # in front of face
        create_edit_bone(
            arm_obj, "CTRL-EyeTarget",
            head=target_pos,
            tail=target_pos + Vector((0, -0.05, 0)),
            parent_name="CTRL-Head",
            use_deform=False,
        )
        assignments.append(("CTRL-EyeTarget", "CTRL"))

        # Individual eye targets (children of main target)
        for side, def_eye in [("Left", def_left_eye), ("Right", def_right_eye)]:
            offset_x = def_eye.head.x - eye_mid.x
            ind_pos = target_pos + Vector((offset_x, 0, 0))
            create_edit_bone(
                arm_obj, f"CTRL-{side}EyeTarget",
                head=ind_pos,
                tail=ind_pos + Vector((0, -0.03, 0)),
                parent_name="CTRL-EyeTarget",
                use_deform=False,
            )
            assignments.append((f"CTRL-{side}EyeTarget", "CTRL"))

    # Jaw control
    def_jaw = edit_bones.get("Jaw")
    if def_jaw:
        create_edit_bone(
            arm_obj, "CTRL-Jaw",
            head=def_jaw.head.copy(),
            tail=def_jaw.tail.copy(),
            parent_name="CTRL-Head",
            use_deform=False,
        )
        assignments.append(("CTRL-Jaw", "CTRL"))
        # DEF Jaw keeps its original parent (Head)

    return assignments


def setup_head_constraints(arm_obj):
    """Set up head/neck constraints in POSE mode."""
    if arm_obj.pose.bones.get("CTRL-Neck"):
        add_copy_rotation_constraint(arm_obj, "Neck", "CTRL-Neck",
                                     name="Follow Neck CTRL")

    if arm_obj.pose.bones.get("CTRL-Head"):
        add_copy_rotation_constraint(arm_obj, "Head", "CTRL-Head",
                                     name="Follow Head CTRL")

    # Eyes track to their individual targets
    for side in ["Left", "Right"]:
        target = f"CTRL-{side}EyeTarget"
        eye_bone = f"{side}Eye"
        if (arm_obj.pose.bones.get(eye_bone) and
                arm_obj.pose.bones.get(target)):
            add_track_to_constraint(
                arm_obj, eye_bone, target,
                track_axis='TRACK_NEGATIVE_Y',
                up_axis='UP_Z',
                name="Track Eye Target",
            )

    if arm_obj.pose.bones.get("CTRL-Jaw"):
        add_copy_rotation_constraint(arm_obj, "Jaw", "CTRL-Jaw",
                                     name="Follow Jaw CTRL")


def setup_head_widgets(arm_obj):
    """Create and assign head/neck widgets."""
    if arm_obj.pose.bones.get("CTRL-Neck"):
        wgt = create_circle_widget("WGT_Neck", radius=0.08, segments=12)
        set_bone_widget(arm_obj, "CTRL-Neck", wgt)
        set_bone_color(arm_obj, "CTRL-Neck", 'THEME09')
        lock_bone_transforms(arm_obj, "CTRL-Neck",
                             lock_loc=(True, True, True),
                             lock_scale=(True, True, True))

    if arm_obj.pose.bones.get("CTRL-Head"):
        wgt = create_circle_widget("WGT_Head", radius=0.12, segments=16)
        set_bone_widget(arm_obj, "CTRL-Head", wgt)
        set_bone_color(arm_obj, "CTRL-Head", 'THEME09')
        lock_bone_transforms(arm_obj, "CTRL-Head",
                             lock_loc=(True, True, True),
                             lock_scale=(True, True, True))

    if arm_obj.pose.bones.get("CTRL-EyeTarget"):
        wgt = create_sphere_widget("WGT_EyeTarget", radius=0.03)
        set_bone_widget(arm_obj, "CTRL-EyeTarget", wgt)
        set_bone_color(arm_obj, "CTRL-EyeTarget", 'THEME03')

    for side in ["Left", "Right"]:
        tgt = f"CTRL-{side}EyeTarget"
        if arm_obj.pose.bones.get(tgt):
            wgt = create_diamond_widget(f"WGT_{tgt}", size=0.015)
            set_bone_widget(arm_obj, tgt, wgt)
            color = 'THEME01' if side == "Left" else 'THEME04'
            set_bone_color(arm_obj, tgt, color)

    if arm_obj.pose.bones.get("CTRL-Jaw"):
        wgt = create_circle_widget("WGT_Jaw", radius=0.04, segments=8)
        set_bone_widget(arm_obj, "CTRL-Jaw", wgt)
        set_bone_color(arm_obj, "CTRL-Jaw", 'THEME09')
        lock_bone_transforms(arm_obj, "CTRL-Jaw",
                             lock_loc=(True, True, True),
                             lock_scale=(True, True, True))
