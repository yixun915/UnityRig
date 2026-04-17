"""Unity Humanoid bone definitions, hierarchy, default positions, and Rigify mapping."""

from mathutils import Vector

# ---------------------------------------------------------------------------
# Unity Humanoid bone table
# Each entry: (bone_name, parent_name, head_pos, tail_offset, roll, is_required)
# Positions are for a default T-pose, ~1.7 m tall character, centred at origin.
# head_pos is absolute; tail_offset is relative to head.
# ---------------------------------------------------------------------------

UNITY_BONES = [
    # --- Core / Torso ---
    ("Root",       None,          Vector((0, 0, 0)),        Vector((0, 0.05, 0)),   0,    False),
    ("Hips",       "Root",        Vector((0, 0, 1.0)),      Vector((0, 0, 0.1)),    0,    True),
    ("Spine",      "Hips",        Vector((0, 0, 1.1)),      Vector((0, 0, 0.12)),   0,    True),
    ("Chest",      "Spine",       Vector((0, 0, 1.22)),     Vector((0, 0, 0.12)),   0,    False),
    ("UpperChest", "Chest",       Vector((0, 0, 1.34)),     Vector((0, 0, 0.10)),   0,    False),

    # --- Head ---
    ("Neck",       "UpperChest",  Vector((0, 0, 1.44)),     Vector((0, 0, 0.08)),   0,    False),
    ("Head",       "Neck",        Vector((0, 0, 1.52)),     Vector((0, 0, 0.16)),   0,    True),
    ("LeftEye",    "Head",        Vector((0.03, -0.07, 1.65)), Vector((0, -0.02, 0)), 0,  False),
    ("RightEye",   "Head",        Vector((-0.03, -0.07, 1.65)), Vector((0, -0.02, 0)), 0, False),
    ("Jaw",        "Head",        Vector((0, -0.03, 1.56)), Vector((0, -0.05, -0.02)), 0, False),

    # --- Left Arm ---
    ("LeftShoulder",  "UpperChest",  Vector((0.04, 0, 1.42)),  Vector((0.10, 0, 0)),  0, False),
    ("LeftUpperArm",  "LeftShoulder", Vector((0.14, 0, 1.42)), Vector((0.28, 0, 0)),  0, True),
    ("LeftLowerArm",  "LeftUpperArm", Vector((0.42, 0, 1.42)), Vector((0.25, 0, 0)),  0, True),
    ("LeftHand",      "LeftLowerArm", Vector((0.67, 0, 1.42)), Vector((0.08, 0, 0)),  0, True),

    # --- Right Arm ---
    ("RightShoulder", "UpperChest",   Vector((-0.04, 0, 1.42)), Vector((-0.10, 0, 0)), 0, False),
    ("RightUpperArm", "RightShoulder", Vector((-0.14, 0, 1.42)), Vector((-0.28, 0, 0)), 0, True),
    ("RightLowerArm", "RightUpperArm", Vector((-0.42, 0, 1.42)), Vector((-0.25, 0, 0)), 0, True),
    ("RightHand",     "RightLowerArm", Vector((-0.67, 0, 1.42)), Vector((-0.08, 0, 0)), 0, True),

    # --- Left Leg ---
    ("LeftUpperLeg",  "Hips",         Vector((0.09, 0, 1.0)),  Vector((0, 0, -0.42)), 0, True),
    ("LeftLowerLeg",  "LeftUpperLeg", Vector((0.09, 0, 0.58)), Vector((0, 0, -0.40)), 0, True),
    ("LeftFoot",      "LeftLowerLeg", Vector((0.09, 0, 0.18)), Vector((0, -0.12, -0.05)), 0, True),
    ("LeftToes",      "LeftFoot",     Vector((0.09, -0.12, 0.13)), Vector((0, -0.06, 0)), 0, False),

    # --- Right Leg ---
    ("RightUpperLeg", "Hips",          Vector((-0.09, 0, 1.0)),  Vector((0, 0, -0.42)), 0, True),
    ("RightLowerLeg", "RightUpperLeg", Vector((-0.09, 0, 0.58)), Vector((0, 0, -0.40)), 0, True),
    ("RightFoot",     "RightLowerLeg", Vector((-0.09, 0, 0.18)), Vector((0, -0.12, -0.05)), 0, True),
    ("RightToes",     "RightFoot",     Vector((-0.09, -0.12, 0.13)), Vector((0, -0.06, 0)), 0, False),
]

# ---------------------------------------------------------------------------
# Finger bone data
# (bone_name, parent_name, head_pos, tail_offset, roll, is_required)
# Positions relative to the hand bone for the LEFT side.
# Right side is mirrored (negate X).
# ---------------------------------------------------------------------------

_FINGER_DEFS = [
    # (finger_name, base_offsets: [(dx, dy, dz), ...], rolls)
    # 3 segments each: Proximal, Intermediate, Distal
    ("Thumb",  [
        (0.02, -0.01, -0.01),   # proximal head offset from hand
        (0.025, -0.02, -0.005), # proximal tail / intermediate head offset
        (0.02, -0.015, 0),      # intermediate tail / distal head offset
        (0.018, -0.01, 0),      # distal tail offset
    ]),
    ("Index",  [
        (0.08, -0.01, 0.005),
        (0.035, -0.005, 0),
        (0.025, -0.003, 0),
        (0.02, -0.002, 0),
    ]),
    ("Middle", [
        (0.08, -0.005, 0),
        (0.038, -0.003, 0),
        (0.028, -0.002, 0),
        (0.022, -0.002, 0),
    ]),
    ("Ring",   [
        (0.078, 0, -0.005),
        (0.035, -0.002, 0),
        (0.025, -0.002, 0),
        (0.02, -0.001, 0),
    ]),
    ("Little", [
        (0.075, 0.005, -0.01),
        (0.028, -0.001, 0),
        (0.02, -0.001, 0),
        (0.015, -0.001, 0),
    ]),
]

_SEGMENT_NAMES = ["Proximal", "Intermediate", "Distal"]


def _build_finger_bones():
    """Generate finger bone entries for both hands."""
    bones = []
    for side, x_sign in [("Left", 1), ("Right", -1)]:
        hand_bone = f"{side}Hand"
        # Find hand position from UNITY_BONES
        hand_head = None
        for name, parent, head, tail_off, roll, req in UNITY_BONES:
            if name == hand_bone:
                hand_head = head.copy()
                break
        if hand_head is None:
            continue

        for finger_name, offsets in _FINGER_DEFS:
            # Accumulate positions
            pos = hand_head.copy()
            parent = hand_bone
            for seg_idx, seg_name in enumerate(_SEGMENT_NAMES):
                bone_name = f"{side}{finger_name}{seg_name}"
                dx, dy, dz = offsets[seg_idx]
                pos = pos + Vector((dx * x_sign, dy, dz))
                # Tail offset
                next_dx, next_dy, next_dz = offsets[seg_idx + 1]
                tail_off = Vector((next_dx * x_sign, next_dy, next_dz))
                bones.append((bone_name, parent, pos.copy(), tail_off, 0, False))
                parent = bone_name
    return bones


FINGER_BONES = _build_finger_bones()

# Complete bone list
ALL_BONES = UNITY_BONES + FINGER_BONES

# Quick lookup: bone_name -> (parent, head, tail_offset, roll, required)
BONE_LOOKUP = {
    name: (parent, head, tail_off, roll, req)
    for name, parent, head, tail_off, roll, req in ALL_BONES
}

# Just the names in hierarchy order
ALL_BONE_NAMES = [b[0] for b in ALL_BONES]

# Required bones (Unity won't accept Humanoid without these)
REQUIRED_BONES = [name for name, parent, head, tail_off, roll, req in ALL_BONES if req]

# ---------------------------------------------------------------------------
# Rigify DEF bone -> Unity bone mapping
# Covers the standard Rigify Human metarig.  The spine mapping assumes the
# default 4-segment spine (spine, spine.001 .. spine.003) plus 1 neck and
# 1 head.  We also handle the common 6-spine variant.
# ---------------------------------------------------------------------------

RIGIFY_TO_UNITY = {
    # Spine (default 4-segment: spine=Hips, .001=Spine, .002=Chest, .003=UpperChest)
    "DEF-spine":         "Hips",
    "DEF-spine.001":     "Spine",
    "DEF-spine.002":     "Chest",
    "DEF-spine.003":     "UpperChest",
    "DEF-spine.004":     "Neck",
    "DEF-spine.005":     "Head",
    # Alternate: 6-segment spine (some metarigs add extra segments)
    "DEF-spine.006":     "Head",  # fallback if 6 segments

    # Left leg
    "DEF-thigh.L":       "LeftUpperLeg",
    "DEF-thigh.L.001":   "LeftUpperLeg",  # Rigify sometimes splits thigh
    "DEF-shin.L":        "LeftLowerLeg",
    "DEF-shin.L.001":    "LeftLowerLeg",
    "DEF-foot.L":        "LeftFoot",
    "DEF-toe.L":         "LeftToes",

    # Right leg
    "DEF-thigh.R":       "RightUpperLeg",
    "DEF-thigh.R.001":   "RightUpperLeg",
    "DEF-shin.R":        "RightLowerLeg",
    "DEF-shin.R.001":    "RightLowerLeg",
    "DEF-foot.R":        "RightFoot",
    "DEF-toe.R":         "RightToes",

    # Left arm
    "DEF-shoulder.L":    "LeftShoulder",
    "DEF-upper_arm.L":   "LeftUpperArm",
    "DEF-upper_arm.L.001": "LeftUpperArm",
    "DEF-forearm.L":     "LeftLowerArm",
    "DEF-forearm.L.001": "LeftLowerArm",
    "DEF-hand.L":        "LeftHand",

    # Right arm
    "DEF-shoulder.R":    "RightShoulder",
    "DEF-upper_arm.R":   "RightUpperArm",
    "DEF-upper_arm.R.001": "RightUpperArm",
    "DEF-forearm.R":     "RightLowerArm",
    "DEF-forearm.R.001": "RightLowerArm",
    "DEF-hand.R":        "RightHand",

    # Left hand fingers
    "DEF-thumb.01.L":      "LeftThumbProximal",
    "DEF-thumb.02.L":      "LeftThumbIntermediate",
    "DEF-thumb.03.L":      "LeftThumbDistal",
    "DEF-f_index.01.L":    "LeftIndexProximal",
    "DEF-f_index.02.L":    "LeftIndexIntermediate",
    "DEF-f_index.03.L":    "LeftIndexDistal",
    "DEF-f_middle.01.L":   "LeftMiddleProximal",
    "DEF-f_middle.02.L":   "LeftMiddleIntermediate",
    "DEF-f_middle.03.L":   "LeftMiddleDistal",
    "DEF-f_ring.01.L":     "LeftRingProximal",
    "DEF-f_ring.02.L":     "LeftRingIntermediate",
    "DEF-f_ring.03.L":     "LeftRingDistal",
    "DEF-f_pinky.01.L":    "LeftLittleProximal",
    "DEF-f_pinky.02.L":    "LeftLittleIntermediate",
    "DEF-f_pinky.03.L":    "LeftLittleDistal",

    # Right hand fingers
    "DEF-thumb.01.R":      "RightThumbProximal",
    "DEF-thumb.02.R":      "RightThumbIntermediate",
    "DEF-thumb.03.R":      "RightThumbDistal",
    "DEF-f_index.01.R":    "RightIndexProximal",
    "DEF-f_index.02.R":    "RightIndexIntermediate",
    "DEF-f_index.03.R":    "RightIndexDistal",
    "DEF-f_middle.01.R":   "RightMiddleProximal",
    "DEF-f_middle.02.R":   "RightMiddleIntermediate",
    "DEF-f_middle.03.R":   "RightMiddleDistal",
    "DEF-f_ring.01.R":     "RightRingProximal",
    "DEF-f_ring.02.R":     "RightRingIntermediate",
    "DEF-f_ring.03.R":     "RightRingDistal",
    "DEF-f_pinky.01.R":    "RightLittleProximal",
    "DEF-f_pinky.02.R":    "RightLittleIntermediate",
    "DEF-f_pinky.03.R":    "RightLittleDistal",
}

# Reverse lookup: Unity name -> list of Rigify names that map to it
UNITY_TO_RIGIFY = {}
for rig_name, unity_name in RIGIFY_TO_UNITY.items():
    UNITY_TO_RIGIFY.setdefault(unity_name, []).append(rig_name)

# ---------------------------------------------------------------------------
# Bone collection definitions for Blender 4.x
# ---------------------------------------------------------------------------

BONE_COLLECTIONS = {
    "DEF":           {"visible": False, "description": "Deformation bones (exported to Unity)"},
    "CTRL":          {"visible": True,  "description": "Main animation controls"},
    "CTRL.fingers":  {"visible": True,  "description": "Finger controls"},
    "MCH":           {"visible": False, "description": "Mechanism bones (hidden)"},
}

# ---------------------------------------------------------------------------
# Limb definitions used by the rig generator
# ---------------------------------------------------------------------------

LIMB_DEFS = {
    "arm_L": {
        "side": "Left",
        "upper": "LeftUpperArm",
        "lower": "LeftLowerArm",
        "end":   "LeftHand",
        "pole_offset": Vector((0, 0.4, 0)),   # elbow pole behind
        "ik_offset": Vector((0, 0, 0)),
        "chain_length": 3,
    },
    "arm_R": {
        "side": "Right",
        "upper": "RightUpperArm",
        "lower": "RightLowerArm",
        "end":   "RightHand",
        "pole_offset": Vector((0, 0.4, 0)),
        "ik_offset": Vector((0, 0, 0)),
        "chain_length": 3,
    },
    "leg_L": {
        "side": "Left",
        "upper": "LeftUpperLeg",
        "lower": "LeftLowerLeg",
        "end":   "LeftFoot",
        "pole_offset": Vector((0, -0.4, 0)),  # knee pole in front
        "ik_offset": Vector((0, 0, 0)),
        "chain_length": 3,
    },
    "leg_R": {
        "side": "Right",
        "upper": "RightUpperLeg",
        "lower": "RightLowerLeg",
        "end":   "RightFoot",
        "pole_offset": Vector((0, -0.4, 0)),
        "ik_offset": Vector((0, 0, 0)),
        "chain_length": 3,
    },
}

# Fingers grouped by side for the hand component
FINGER_NAMES = ["Thumb", "Index", "Middle", "Ring", "Little"]
