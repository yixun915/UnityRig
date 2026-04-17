"""Hand and finger rig component with curl/spread/fist controls."""

import math
from mathutils import Vector
from ..bone_data import FINGER_NAMES, ALL_BONES
from ..utils import (
    create_edit_bone,
    add_copy_rotation_constraint, add_custom_property,
    create_circle_widget, create_diamond_widget,
    set_bone_widget, set_bone_color, lock_bone_transforms,
)

_SEGMENT_NAMES = ["Proximal", "Intermediate", "Distal"]


def create_hand_bones(arm_obj, side):
    """Create finger control bones for one hand in EDIT mode.

    DEF finger bones keep their original hierarchy
    (Hand -> Proximal -> Intermediate -> Distal) for correct FBX export.
    CTRL finger bones form their own chain and DEF bones follow via constraints.

    side: 'Left' or 'Right'
    Returns list of (bone_name, collection_name) tuples.
    """
    edit_bones = arm_obj.data.edit_bones
    hand_bone = f"{side}Hand"
    assignments = []

    if hand_bone not in edit_bones:
        return assignments

    # Create a master fist control bone near the hand
    hand_eb = edit_bones[hand_bone]
    x_sign = 1 if side == "Left" else -1
    fist_pos = hand_eb.tail.copy() + Vector((0.02 * x_sign, 0.03, 0))

    fist_name = f"CTRL-Fist-{side}"
    create_edit_bone(
        arm_obj, fist_name,
        head=fist_pos,
        tail=fist_pos + Vector((0.03 * x_sign, 0, 0)),
        parent_name=hand_bone,
        use_deform=False,
    )
    assignments.append((fist_name, "CTRL.fingers"))

    # Spread control
    spread_pos = fist_pos + Vector((0, 0, 0.03))
    spread_name = f"CTRL-Spread-{side}"
    create_edit_bone(
        arm_obj, spread_name,
        head=spread_pos,
        tail=spread_pos + Vector((0.03 * x_sign, 0, 0)),
        parent_name=hand_bone,
        use_deform=False,
    )
    assignments.append((spread_name, "CTRL.fingers"))

    # Per-finger curl controls and individual joint controls
    for finger in FINGER_NAMES:
        prox_name = f"{side}{finger}Proximal"
        prox_eb = edit_bones.get(prox_name)
        if prox_eb is None:
            continue

        # Curl control - placed near the proximal bone
        curl_name = f"CTRL-Curl-{side}{finger}"
        curl_pos = prox_eb.head + Vector((0, 0.04, 0))
        create_edit_bone(
            arm_obj, curl_name,
            head=curl_pos,
            tail=curl_pos + Vector((0.02 * x_sign, 0, 0)),
            parent_name=hand_bone,
            use_deform=False,
        )
        assignments.append((curl_name, "CTRL.fingers"))

        # Individual joint CTRL bones — these form their own chain
        # (CTRL-Proximal -> CTRL-Intermediate -> CTRL-Distal)
        # DEF bones keep their original parents.
        prev_ctrl_parent = hand_bone
        for seg in _SEGMENT_NAMES:
            def_name = f"{side}{finger}{seg}"
            def_eb = edit_bones.get(def_name)
            if def_eb is None:
                continue

            ctrl_name = f"CTRL-{def_name}"
            create_edit_bone(
                arm_obj, ctrl_name,
                head=def_eb.head.copy(),
                tail=def_eb.tail.copy(),
                parent_name=prev_ctrl_parent,
                roll=def_eb.roll,
                use_deform=False,
            )
            assignments.append((ctrl_name, "CTRL.fingers"))
            prev_ctrl_parent = ctrl_name

            # DEF bone keeps its original parent — do NOT reparent.
            # Constraints in setup_hand_constraints() link DEF -> CTRL.

    return assignments


def setup_hand_constraints(arm_obj, side):
    """Set up finger constraints and drivers in POSE mode."""
    hand_bone = f"{side}Hand"
    fist_name = f"CTRL-Fist-{side}"
    spread_name = f"CTRL-Spread-{side}"

    # Add fist (master curl) property
    add_custom_property(arm_obj, fist_name, "fist",
                        default=0.0, min_val=0.0, max_val=1.0,
                        description="Master curl for all fingers (0=open, 1=fist)")

    # Add spread property
    add_custom_property(arm_obj, spread_name, "spread",
                        default=0.0, min_val=-1.0, max_val=1.0,
                        description="Fan fingers apart (-1=pinch, 1=spread)")

    for finger in FINGER_NAMES:
        curl_name = f"CTRL-Curl-{side}{finger}"
        pb_curl = arm_obj.pose.bones.get(curl_name)
        if pb_curl is None:
            continue

        # Add per-finger curl property
        add_custom_property(arm_obj, curl_name, "curl",
                            default=0.0, min_val=0.0, max_val=1.0,
                            description=f"{finger} curl (0=straight, 1=curled)")

        # Set up drivers on each joint's CTRL rotation
        curl_weights = {"Proximal": 0.7, "Intermediate": 0.9, "Distal": 0.5}
        if finger == "Thumb":
            curl_weights = {"Proximal": 0.4, "Intermediate": 0.6, "Distal": 0.5}

        for seg, weight in curl_weights.items():
            ctrl_name = f"CTRL-{side}{finger}{seg}"
            pb = arm_obj.pose.bones.get(ctrl_name)
            if pb is None:
                continue

            max_angle = math.radians(90) * weight
            _add_finger_curl_driver(
                arm_obj, ctrl_name,
                curl_bone=curl_name,
                fist_bone=fist_name,
                max_angle=max_angle,
            )

        # Spread driver on the proximal bone's Z rotation
        prox_ctrl = f"CTRL-{side}{finger}Proximal"
        if arm_obj.pose.bones.get(prox_ctrl):
            _add_finger_spread_driver(
                arm_obj, prox_ctrl,
                spread_bone=spread_name,
                finger_name=finger,
                side=side,
            )

    # DEF bones copy rotation from their CTRL counterparts
    for finger in FINGER_NAMES:
        for seg in _SEGMENT_NAMES:
            def_name = f"{side}{finger}{seg}"
            ctrl_name = f"CTRL-{def_name}"
            if (arm_obj.pose.bones.get(def_name) and
                    arm_obj.pose.bones.get(ctrl_name)):
                add_copy_rotation_constraint(
                    arm_obj, def_name, ctrl_name,
                    name="Follow Finger CTRL",
                )


def setup_hand_widgets(arm_obj, side):
    """Assign widgets to finger controls."""
    color = 'THEME01' if side == "Left" else 'THEME04'

    fist_name = f"CTRL-Fist-{side}"
    if arm_obj.pose.bones.get(fist_name):
        wgt = create_circle_widget(f"WGT_{fist_name}", radius=0.02, segments=8)
        set_bone_widget(arm_obj, fist_name, wgt)
        set_bone_color(arm_obj, fist_name, color)

    spread_name = f"CTRL-Spread-{side}"
    if arm_obj.pose.bones.get(spread_name):
        wgt = create_diamond_widget(f"WGT_{spread_name}", size=0.015)
        set_bone_widget(arm_obj, spread_name, wgt)
        set_bone_color(arm_obj, spread_name, color)

    for finger in FINGER_NAMES:
        curl_name = f"CTRL-Curl-{side}{finger}"
        if arm_obj.pose.bones.get(curl_name):
            wgt = create_diamond_widget(f"WGT_{curl_name}", size=0.01)
            set_bone_widget(arm_obj, curl_name, wgt)
            set_bone_color(arm_obj, curl_name, color)

    for finger in FINGER_NAMES:
        for seg in _SEGMENT_NAMES:
            ctrl_name = f"CTRL-{side}{finger}{seg}"
            if arm_obj.pose.bones.get(ctrl_name):
                wgt = create_circle_widget(f"WGT_{ctrl_name}", radius=0.008, segments=8)
                set_bone_widget(arm_obj, ctrl_name, wgt)
                set_bone_color(arm_obj, ctrl_name, color)
                lock_bone_transforms(arm_obj, ctrl_name,
                                     lock_loc=(True, True, True),
                                     lock_scale=(True, True, True))


# ---------------------------------------------------------------------------
# Internal driver helpers
# ---------------------------------------------------------------------------

def _add_finger_curl_driver(arm_obj, ctrl_bone, curl_bone, fist_bone, max_angle):
    """Drive a finger joint's X rotation from curl + fist properties.

    Expression: (curl + fist - curl*fist) * max_angle
    This blends both inputs without exceeding the max.
    """
    data_path = f'pose.bones["{ctrl_bone}"].rotation_euler[0]'

    try:
        fcurve = arm_obj.driver_add(data_path)
    except TypeError:
        return

    driver = fcurve.driver
    driver.type = 'SCRIPTED'
    driver.expression = f"(curl + fist - curl * fist) * {max_angle:.4f}"

    var_curl = driver.variables.new()
    var_curl.name = "curl"
    var_curl.type = 'SINGLE_PROP'
    var_curl.targets[0].id = arm_obj
    var_curl.targets[0].data_path = f'pose.bones["{curl_bone}"]["curl"]'

    var_fist = driver.variables.new()
    var_fist.name = "fist"
    var_fist.type = 'SINGLE_PROP'
    var_fist.targets[0].id = arm_obj
    var_fist.targets[0].data_path = f'pose.bones["{fist_bone}"]["fist"]'


def _add_finger_spread_driver(arm_obj, ctrl_bone, spread_bone, finger_name, side):
    """Drive a finger proximal Z rotation from the spread property."""
    spread_amounts = {
        "Thumb":  0.25,
        "Index":  0.12,
        "Middle": 0.0,
        "Ring":   -0.10,
        "Little": -0.20,
    }
    amount = spread_amounts.get(finger_name, 0)
    if amount == 0:
        return

    x_sign = 1 if side == "Left" else -1
    max_spread = math.radians(20) * amount * x_sign

    data_path = f'pose.bones["{ctrl_bone}"].rotation_euler[2]'

    try:
        fcurve = arm_obj.driver_add(data_path)
    except TypeError:
        return

    driver = fcurve.driver
    driver.type = 'SCRIPTED'
    driver.expression = f"var * {max_spread:.4f}"

    var = driver.variables.new()
    var.name = "var"
    var.type = 'SINGLE_PROP'
    var.targets[0].id = arm_obj
    var.targets[0].data_path = f'pose.bones["{spread_bone}"]["spread"]'
