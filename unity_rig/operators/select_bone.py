"""Select a rig control by name from the N-panel."""

import bpy


class UNITYRIG_OT_select_bone(bpy.types.Operator):
    """Select this control and make it active. Shift-click to extend the selection"""
    bl_idname = "unity_rig.select_bone"
    bl_label = "Select Control"
    bl_options = {'REGISTER', 'UNDO'}

    bone_name: bpy.props.StringProperty(name="Bone", default="")
    extend: bpy.props.BoolProperty(name="Extend", default=False, options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'ARMATURE'

    def invoke(self, context, event):
        self.extend = event.shift
        return self.execute(context)

    def execute(self, context):
        obj = context.active_object
        pbone = obj.pose.bones.get(self.bone_name)
        if pbone is None:
            self.report({'WARNING'}, "No bone named %s" % self.bone_name)
            return {'CANCELLED'}

        if obj.mode != 'POSE':
            bpy.ops.object.mode_set(mode='POSE')

        bone = pbone.bone
        # A hidden or unselectable bone cannot be picked, so clear both flags and
        # reveal whichever collection holds it.
        bone.hide = False
        bone.hide_select = False
        for coll in bone.collections:
            if not coll.is_visible:
                coll.is_visible = True

        # Selection lives on PoseBone, not Bone; the active bone is still a Bone.
        if not self.extend:
            for other in obj.pose.bones:
                other.select = False

        pbone.select = True
        obj.data.bones.active = bone
        return {'FINISHED'}


def register():
    bpy.utils.register_class(UNITYRIG_OT_select_bone)


def unregister():
    bpy.utils.unregister_class(UNITYRIG_OT_select_bone)
