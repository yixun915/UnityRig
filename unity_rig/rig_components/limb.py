"""IK/FK limb rig component for arms and legs."""

import math
from mathutils import Vector
from ..bone_data import LIMB_DEFS
from ..utils import (
    create_edit_bone,
    add_copy_rotation_constraint, add_copy_location_constraint,
    add_copy_transforms_constraint, add_ik_constraint,
    add_custom_property, add_driver,
    create_cube_widget, create_sphere_widget, create_diamond_widget,
    create_circle_widget,
    set_bone_widget, set_bone_color, lock_bone_transforms,
)


def create_limb_bones(arm_obj, limb_key):
    """Create IK/FK control and mechanism bones for a limb in EDIT mode.

    DEF bones keep their original hierarchy for FBX export.
    FK/MCH/IK bones form their own chains.
    For arms, a CTRL-Shoulder bone is also created.

    limb_key: one of 'arm_L', 'arm_R', 'leg_L', 'leg_R'
    Returns list of (bone_name, collection_name) tuples.
    """
    limb = LIMB_DEFS[limb_key]
    side = limb["side"]
    upper_name = limb["upper"]
    lower_name = limb["lower"]
    end_name = limb["end"]

    edit_bones = arm_obj.data.edit_bones
    def_upper = edit_bones.get(upper_name)
    def_lower = edit_bones.get(lower_name)
    def_end = edit_bones.get(end_name)

    if not all([def_upper, def_lower, def_end]):
        return []

    assignments = []
    is_arm = "arm" in limb_key

    # --- Shoulder CTRL (arms only) ---
    shoulder_ctrl_name = None
    if is_arm:
        shoulder_name = f"{side}Shoulder"
        def_shoulder = edit_bones.get(shoulder_name)
        if def_shoulder:
            shoulder_ctrl_name = f"CTRL-{shoulder_name}"
            # Parent to the last spine CTRL
            spine_parent = None
            for name in ["CTRL-UpperChest", "CTRL-Chest", "CTRL-Spine"]:
                if name in edit_bones:
                    spine_parent = name
                    break
            create_edit_bone(
                arm_obj, shoulder_ctrl_name,
                head=def_shoulder.head.copy(),
                tail=def_shoulder.tail.copy(),
                parent_name=spine_parent,
                roll=def_shoulder.roll,
                use_deform=False,
            )
            assignments.append((shoulder_ctrl_name, "CTRL"))

    # Determine parent for FK and MCH chains
    chain_parent = shoulder_ctrl_name or _find_limb_parent_ctrl(edit_bones, limb_key)

    # --- FK chain ---
    fk_parent = chain_parent

    for def_name in [upper_name, lower_name, end_name]:
        def_bone = edit_bones[def_name]
        fk_name = f"CTRL-FK-{def_name}"
        create_edit_bone(
            arm_obj, fk_name,
            head=def_bone.head.copy(),
            tail=def_bone.tail.copy(),
            parent_name=fk_parent,
            roll=def_bone.roll,
            use_deform=False,
        )
        assignments.append((fk_name, "CTRL"))
        fk_parent = fk_name

    # --- IK mechanism chain ---
    mch_parent = chain_parent

    for def_name in [upper_name, lower_name, end_name]:
        def_bone = edit_bones[def_name]
        mch_name = f"MCH-IK-{def_name}"
        mch_bone = create_edit_bone(
            arm_obj, mch_name,
            head=def_bone.head.copy(),
            tail=def_bone.tail.copy(),
            parent_name=mch_parent,
            roll=def_bone.roll,
            use_deform=False,
        )
        if mch_parent and mch_parent.startswith("MCH-IK-"):
            mch_bone.use_connect = True
        assignments.append((mch_name, "MCH"))
        mch_parent = mch_name

    # --- IK target ---
    ik_target_name = f"CTRL-IK-{end_name}"
    create_edit_bone(
        arm_obj, ik_target_name,
        head=def_end.head.copy(),
        tail=def_end.tail.copy(),
        parent_name="CTRL-Root",
        roll=def_end.roll,
        use_deform=False,
    )
    assignments.append((ik_target_name, "CTRL"))

    # --- Pole target ---
    pole_offset = limb["pole_offset"]
    pole_pos = def_lower.head + pole_offset
    pole_name = f"CTRL-Pole-{def_name_for_pole(limb_key)}"
    create_edit_bone(
        arm_obj, pole_name,
        head=pole_pos,
        tail=pole_pos + Vector((0, 0, 0.05)),
        parent_name="CTRL-Root",
        use_deform=False,
    )
    assignments.append((pole_name, "CTRL"))

    # DEF bones keep their original hierarchy — do NOT reparent.

    return assignments


def setup_limb_constraints(arm_obj, limb_key, ik_fk_default='IK'):
    """Set up IK/FK constraints and drivers for a limb in POSE mode.

    ik_fk_default: 'IK' (0.0) or 'FK' (1.0) for the initial blend value
    """
    limb = LIMB_DEFS[limb_key]
    side = limb["side"]
    upper_name = limb["upper"]
    lower_name = limb["lower"]
    end_name = limb["end"]
    chain_length = limb["chain_length"]
    is_arm = "arm" in limb_key

    ik_target = f"CTRL-IK-{end_name}"
    pole_target = f"CTRL-Pole-{def_name_for_pole(limb_key)}"
    mch_end = f"MCH-IK-{end_name}"

    # --- Shoulder constraint (arms only) ---
    if is_arm:
        shoulder_name = f"{side}Shoulder"
        shoulder_ctrl = f"CTRL-{shoulder_name}"
        if (arm_obj.pose.bones.get(shoulder_name) and
                arm_obj.pose.bones.get(shoulder_ctrl)):
            add_copy_rotation_constraint(
                arm_obj, shoulder_name, shoulder_ctrl,
                name="Follow Shoulder CTRL",
            )

    # --- IK constraint on MCH chain end ---
    pole_angle = math.radians(-90) if is_arm else math.radians(90)

    add_ik_constraint(
        arm_obj, mch_end, target_bone=ik_target,
        pole_target_bone=pole_target,
        chain_count=chain_length,
        pole_angle=pole_angle,
        name="IK",
    )

    # --- IK/FK blend property on the IK target bone ---
    default_val = 0.0 if ik_fk_default == 'IK' else 1.0
    add_custom_property(arm_obj, ik_target, "ik_fk_blend",
                        default=default_val, min_val=0.0, max_val=1.0,
                        description="0=IK, 1=FK")

    # --- DEF bones: blend between MCH-IK (IK result) and CTRL-FK ---
    for def_name in [upper_name, lower_name, end_name]:
        mch_name = f"MCH-IK-{def_name}"
        fk_name = f"CTRL-FK-{def_name}"

        # Copy Rotation from MCH-IK (IK result) - driven by (1 - ik_fk_blend)
        add_copy_rotation_constraint(
            arm_obj, def_name, mch_name,
            influence=1.0, name="IK Rotation",
        )

        # Copy Rotation from FK CTRL - driven by ik_fk_blend
        add_copy_rotation_constraint(
            arm_obj, def_name, fk_name,
            influence=0.0, name="FK Rotation",
        )

        # Driver: IK influence = 1 - var
        _add_constraint_driver(
            arm_obj, def_name, "IK Rotation",
            ik_target, "ik_fk_blend",
            expression="1 - var",
        )

        # Driver: FK influence = var
        _add_constraint_driver(
            arm_obj, def_name, "FK Rotation",
            ik_target, "ik_fk_blend",
            expression="var",
        )


def setup_limb_widgets(arm_obj, limb_key):
    """Create and assign widgets for limb controls."""
    limb = LIMB_DEFS[limb_key]
    side = limb["side"]
    upper_name = limb["upper"]
    lower_name = limb["lower"]
    end_name = limb["end"]
    is_arm = "arm" in limb_key

    color = 'THEME01' if side == "Left" else 'THEME04'

    # Shoulder (arms only)
    if is_arm:
        shoulder_ctrl = f"CTRL-{side}Shoulder"
        if arm_obj.pose.bones.get(shoulder_ctrl):
            wgt = create_circle_widget(f"WGT_{shoulder_ctrl}", radius=0.05, segments=10)
            set_bone_widget(arm_obj, shoulder_ctrl, wgt)
            set_bone_color(arm_obj, shoulder_ctrl, color)
            lock_bone_transforms(arm_obj, shoulder_ctrl,
                                 lock_loc=(True, True, True),
                                 lock_scale=(True, True, True))

    # FK controls - circles
    for def_name in [upper_name, lower_name, end_name]:
        fk_name = f"CTRL-FK-{def_name}"
        if arm_obj.pose.bones.get(fk_name):
            wgt = create_circle_widget(f"WGT_{fk_name}", radius=0.06, segments=12)
            set_bone_widget(arm_obj, fk_name, wgt)
            set_bone_color(arm_obj, fk_name, color)
            lock_bone_transforms(arm_obj, fk_name,
                                 lock_loc=(True, True, True),
                                 lock_scale=(True, True, True))

    # IK target - cube
    ik_name = f"CTRL-IK-{end_name}"
    if arm_obj.pose.bones.get(ik_name):
        wgt = create_cube_widget(f"WGT_{ik_name}", size=0.04)
        set_bone_widget(arm_obj, ik_name, wgt)
        set_bone_color(arm_obj, ik_name, color)

    # Pole target - diamond
    pole_name = f"CTRL-Pole-{def_name_for_pole(limb_key)}"
    if arm_obj.pose.bones.get(pole_name):
        wgt = create_diamond_widget(f"WGT_{pole_name}", size=0.025)
        set_bone_widget(arm_obj, pole_name, wgt)
        set_bone_color(arm_obj, pole_name, color)


# ---------------------------------------------------------------------------
# IK/FK Snapping helpers (called by operators)
# ---------------------------------------------------------------------------

def snap_ik_to_fk(arm_obj, limb_key):
    """Snap IK controls to match current FK pose."""
    limb = LIMB_DEFS[limb_key]
    end_name = limb["end"]
    lower_name = limb["lower"]

    ik_target = f"CTRL-IK-{end_name}"
    fk_end = f"CTRL-FK-{end_name}"
    pole_name = f"CTRL-Pole-{def_name_for_pole(limb_key)}"
    fk_lower = f"CTRL-FK-{lower_name}"

    pb_ik = arm_obj.pose.bones.get(ik_target)
    pb_fk_end = arm_obj.pose.bones.get(fk_end)
    pb_pole = arm_obj.pose.bones.get(pole_name)
    pb_fk_lower = arm_obj.pose.bones.get(fk_lower)

    if pb_ik and pb_fk_end:
        pb_ik.matrix = pb_fk_end.matrix.copy()

    if pb_pole and pb_fk_lower:
        pole_offset = limb["pole_offset"]
        pb_pole.location = pb_fk_lower.head + pole_offset


def snap_fk_to_ik(arm_obj, limb_key):
    """Snap FK controls to match current IK pose."""
    limb = LIMB_DEFS[limb_key]
    upper_name = limb["upper"]
    lower_name = limb["lower"]
    end_name = limb["end"]

    for def_name in [upper_name, lower_name, end_name]:
        mch_name = f"MCH-IK-{def_name}"
        fk_name = f"CTRL-FK-{def_name}"

        pb_mch = arm_obj.pose.bones.get(mch_name)
        pb_fk = arm_obj.pose.bones.get(fk_name)

        if pb_mch and pb_fk:
            pb_fk.matrix = pb_mch.matrix.copy()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def def_name_for_pole(limb_key):
    """Get a readable name for the pole target bone."""
    mapping = {
        "arm_L": "LeftElbow",
        "arm_R": "RightElbow",
        "leg_L": "LeftKnee",
        "leg_R": "RightKnee",
    }
    return mapping[limb_key]


def _find_limb_parent_ctrl(edit_bones, limb_key):
    """Find the appropriate parent CTRL bone for a limb's FK/MCH chains.

    For arms without a shoulder, falls back to the last spine CTRL.
    For legs, parents to CTRL-Hips.
    """
    if "arm" in limb_key:
        for name in ["CTRL-UpperChest", "CTRL-Chest", "CTRL-Spine"]:
            if name in edit_bones:
                return name
    else:
        return "CTRL-Hips"
    return "CTRL-Root"


def _add_constraint_driver(arm_obj, bone_name, constraint_name,
                           driver_bone, driver_prop, expression):
    """Add a driver to a constraint's influence property.

    Uses constraint name (not index) in the data path for robustness.
    """
    pb = arm_obj.pose.bones.get(bone_name)
    if pb is None:
        return

    con = pb.constraints.get(constraint_name)
    if con is None:
        return

    data_path = f'pose.bones["{bone_name}"].constraints["{constraint_name}"].influence'

    fcurve = arm_obj.driver_add(data_path)
    driver = fcurve.driver
    driver.type = 'SCRIPTED'
    driver.expression = expression

    var = driver.variables.new()
    var.name = "var"
    var.type = 'SINGLE_PROP'
    var.targets[0].id = arm_obj
    var.targets[0].data_path = f'pose.bones["{driver_bone}"]["{driver_prop}"]'
