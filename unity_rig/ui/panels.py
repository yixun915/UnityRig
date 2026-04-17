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

        for limb_label, ctrl_bone_name in [
            ("Left Arm",  "CTRL-IK-LeftHand"),
            ("Right Arm", "CTRL-IK-RightHand"),
            ("Left Leg",  "CTRL-IK-LeftFoot"),
            ("Right Leg", "CTRL-IK-RightFoot"),
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
            row = box.row(align=True)
            op = row.operator("unity_rig.snap_ik_to_fk", text="Snap IK→FK")
            op.limb_bone = ctrl_bone_name
            op = row.operator("unity_rig.snap_fk_to_ik", text="Snap FK→IK")
            op.limb_bone = ctrl_bone_name


classes = (
    UNITYRIG_PT_main,
    UNITYRIG_PT_create,
    UNITYRIG_PT_convert,
    UNITYRIG_PT_export,
    UNITYRIG_PT_ikfk,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
