"""N-Panel UI for Unity Rig in the 3D Viewport."""

import bpy


class UNITYRIG_PT_main(bpy.types.Panel):
    bl_label = "Unity Rig"
    bl_idname = "UNITYRIG_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Unity Rig"

    def draw(self, context):
        layout = self.layout


class UNITYRIG_PT_create(bpy.types.Panel):
    bl_label = "Create Rig"
    bl_idname = "UNITYRIG_PT_create"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Unity Rig"
    bl_parent_id = "UNITYRIG_PT_main"

    def draw(self, context):
        layout = self.layout
        props = context.scene.unity_rig

        layout.label(text="Step 1: Create Metarig")
        col = layout.column(align=True)
        col.prop(props, "include_fingers")
        col.prop(props, "include_eyes")
        layout.operator("unity_rig.create_metarig", icon='ARMATURE_DATA')

        layout.separator()
        layout.label(text="Step 2: Position bones to fit mesh")
        layout.label(text="(use Edit Mode on the metarig)", icon='INFO')

        layout.separator()
        layout.label(text="Step 3: Generate Rig")
        col = layout.column(align=True)
        col.prop(props, "ik_fk_default")
        layout.operator("unity_rig.generate_rig", icon='CON_ARMATURE')


class UNITYRIG_PT_convert(bpy.types.Panel):
    bl_label = "Convert Rigify"
    bl_idname = "UNITYRIG_PT_convert"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Unity Rig"
    bl_parent_id = "UNITYRIG_PT_main"

    def draw(self, context):
        layout = self.layout
        props = context.scene.unity_rig

        layout.label(text="Convert a Rigify rig to Unity format")
        col = layout.column(align=True)
        col.prop(props, "rigify_conversion_mode")
        if props.rigify_conversion_mode == 'DUPLICATE':
            col.prop(props, "rigify_keep_controls")
        layout.operator("unity_rig.convert_rigify", icon='FILE_REFRESH')


class UNITYRIG_PT_export(bpy.types.Panel):
    bl_label = "Export to Unity"
    bl_idname = "UNITYRIG_PT_export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Unity Rig"
    bl_parent_id = "UNITYRIG_PT_main"

    def draw(self, context):
        layout = self.layout
        props = context.scene.unity_rig

        col = layout.column(align=True)
        col.prop(props, "export_path")
        col.prop(props, "export_animations")
        col.prop(props, "export_meshes")
        layout.operator("unity_rig.export_fbx", icon='EXPORT')


class UNITYRIG_PT_ikfk(bpy.types.Panel):
    """Panel shown only when a Unity Rig armature is selected, for IK/FK controls."""
    bl_label = "IK / FK Controls"
    bl_idname = "UNITYRIG_PT_ikfk"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Unity Rig"
    bl_parent_id = "UNITYRIG_PT_main"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'ARMATURE'
                and obj.data.get("unity_rig_generated") is not None)

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        active = obj.data.bones.active
        active_name = active.name if active else ""

        for limb_label, ctrl_bone_name, pole_bone_name in [
            ("Left Arm",  "CTRL-IK-LeftHand",  "CTRL-Pole-LeftElbow"),
            ("Right Arm", "CTRL-IK-RightHand", "CTRL-Pole-RightElbow"),
            ("Left Leg",  "CTRL-IK-LeftFoot",  "CTRL-Pole-LeftKnee"),
            ("Right Leg", "CTRL-IK-RightFoot", "CTRL-Pole-RightKnee"),
        ]:
            pb = obj.pose.bones.get(ctrl_bone_name)
            if pb is None:
                continue
            box = layout.box()
            row = box.row()
            row.label(text=limb_label)
            if "ik_fk_blend" in pb:
                row.prop(pb, '["ik_fk_blend"]', text="FK" if pb["ik_fk_blend"] > 0.5 else "IK",
                         slider=True)
            # Hunting for these two controls in a 156-bone rig is the slow part of
            # posing, so offer them directly. Shift-click adds to the selection.
            row = box.row(align=True)
            op = row.operator("unity_rig.select_bone", text="IK",
                              icon='CON_KINEMATIC',
                              depress=(active_name == ctrl_bone_name))
            op.bone_name = ctrl_bone_name
            sub = row.row(align=True)
            sub.enabled = obj.pose.bones.get(pole_bone_name) is not None
            op = sub.operator("unity_rig.select_bone", text="Pole",
                              icon='EMPTY_AXIS',
                              depress=(active_name == pole_bone_name))
            op.bone_name = pole_bone_name

            row = box.row(align=True)
            op = row.operator("unity_rig.snap_ik_to_fk", text="Snap IK→FK")
            op.limb_bone = ctrl_bone_name
            op = row.operator("unity_rig.snap_fk_to_ik", text="Snap FK→IK")
            op.limb_bone = ctrl_bone_name

        layout.separator()
        row = layout.row(align=True)
        for label, bname in [("Root", "CTRL-Root"), ("Hips", "CTRL-Hips"),
                             ("Chest", "CTRL-Chest"), ("Head", "CTRL-Head")]:
            sub = row.row(align=True)
            sub.enabled = obj.pose.bones.get(bname) is not None
            op = sub.operator("unity_rig.select_bone", text=label,
                              depress=(active_name == bname))
            op.bone_name = bname


class UNITYRIG_PT_hands(bpy.types.Panel):
    """Fist / spread presets and per-finger curl sliders."""
    bl_label = "Hands"
    bl_idname = "UNITYRIG_PT_hands"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Unity Rig"
    bl_parent_id = "UNITYRIG_PT_main"

    FINGERS = ("Thumb", "Index", "Middle", "Ring", "Little")

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'ARMATURE'
                and obj.pose.bones.get("CTRL-Fist-Left") is not None)

    def _side(self, layout, obj, side, label):
        box = layout.box()
        box.label(text=label)

        row = box.row(align=True)
        for pose, text in (('OPEN', "Open"), ('RELAX', "Relax"), ('FIST', "Fist")):
            op = row.operator("unity_rig.hand_pose", text=text)
            op.side = side
            op.pose = pose
        row = box.row(align=True)
        for pose, text in (('PINCH', "Pinch"), ('SPREAD', "Spread")):
            op = row.operator("unity_rig.hand_pose", text=text)
            op.side = side
            op.pose = pose

        col = box.column(align=True)
        for bone_name, key, text in ((f"CTRL-Fist-{side}", "fist", "Fist"),
                                     (f"CTRL-Spread-{side}", "spread", "Spread")):
            pb = obj.pose.bones.get(bone_name)
            if pb is not None and key in pb:
                col.prop(pb, '["%s"]' % key, text=text, slider=True)

        header, body = box.panel(idname="unity_rig_fingers_" + side, default_closed=True)
        header.label(text="Per Finger")
        if body is not None:
            col = body.column(align=True)
            for finger in self.FINGERS:
                pb = obj.pose.bones.get("CTRL-Curl-%s%s" % (side, finger))
                if pb is not None and "curl" in pb:
                    col.prop(pb, '["curl"]', text=finger, slider=True)

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        row = layout.row(align=True)
        for pose, text in (('OPEN', "Open Both"), ('FIST', "Fist Both")):
            op = row.operator("unity_rig.hand_pose", text=text)
            op.side = 'BOTH'
            op.pose = pose

        self._side(layout, obj, "Left", "Left Hand")
        self._side(layout, obj, "Right", "Right Hand")


classes = (
    UNITYRIG_PT_main,
    UNITYRIG_PT_create,
    UNITYRIG_PT_convert,
    UNITYRIG_PT_export,
    UNITYRIG_PT_ikfk,
    UNITYRIG_PT_hands,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
