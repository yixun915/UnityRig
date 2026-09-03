"""Set hand-shape properties (fist / spread / curl) from the N-panel."""

import bpy


HAND_POSES = {
    'OPEN':   {"fist": 0.0, "spread": 0.0, "curl": 0.0},
    'FIST':   {"fist": 0.9, "spread": -0.2, "curl": 0.0},
    'RELAX':  {"fist": 0.30, "spread": 0.10, "curl": 0.0},
    'SPREAD': {"fist": 0.0, "spread": 1.0, "curl": 0.0},
    'PINCH':  {"fist": 0.0, "spread": -1.0, "curl": 0.0},
}

FINGERS = ("Thumb", "Index", "Middle", "Ring", "Little")


class UNITYRIG_OT_hand_pose(bpy.types.Operator):
    """Apply a preset hand shape. Per-finger curl is reset to zero"""
    bl_idname = "unity_rig.hand_pose"
    bl_label = "Hand Pose"
    bl_options = {'REGISTER', 'UNDO'}

    side: bpy.props.EnumProperty(
        name="Side",
        items=[('Left', "Left", ""), ('Right', "Right", ""), ('BOTH', "Both", "")],
        default='Left',
    )
    pose: bpy.props.EnumProperty(
        name="Pose",
        items=[(k, k.title(), "") for k in HAND_POSES],
        default='OPEN',
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'ARMATURE'

    def _apply(self, obj, side, values):
        touched = 0
        targets = [(f"CTRL-Fist-{side}", "fist"), (f"CTRL-Spread-{side}", "spread")]
        targets += [(f"CTRL-Curl-{side}{f}", "curl") for f in FINGERS]
        for bone_name, key in targets:
            pb = obj.pose.bones.get(bone_name)
            if pb is None or key not in pb:
                continue
            pb[key] = values[key]
            touched += 1
        return touched

    def execute(self, context):
        obj = context.active_object
        values = HAND_POSES[self.pose]
        sides = ("Left", "Right") if self.side == 'BOTH' else (self.side,)
        total = sum(self._apply(obj, s, values) for s in sides)
        if not total:
            self.report({'WARNING'}, "No hand controls found on this rig")
            return {'CANCELLED'}
        # Custom properties drive constraints, so the depsgraph needs a nudge.
        obj.update_tag()
        context.view_layer.update()
        return {'FINISHED'}


def register():
    bpy.utils.register_class(UNITYRIG_OT_hand_pose)


def unregister():
    bpy.utils.unregister_class(UNITYRIG_OT_hand_pose)
