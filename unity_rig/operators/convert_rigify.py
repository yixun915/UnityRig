"""Operator to convert an existing Rigify rig to Unity Humanoid format."""

import bpy

from ..bone_data import RIGIFY_TO_UNITY, BONE_LOOKUP, ALL_BONE_NAMES
from ..utils import ensure_object_mode, ensure_edit_mode


class UNITYRIG_OT_convert_rigify(bpy.types.Operator):
    """Convert a Rigify-generated rig to Unity Humanoid bone naming"""

    bl_idname = "unity_rig.convert_rigify"
    bl_label = "Convert Rigify to Unity"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj is None or obj.type != 'ARMATURE':
            return False
        # Check for Rigify signature: rig_id property or DEF- bones
        arm = obj.data
        if arm.get("rig_id"):
            return True
        return any(b.name.startswith("DEF-") for b in arm.bones)

    def execute(self, context):
        source_obj = context.active_object
        props = context.scene.unity_rig
        mode = props.rigify_conversion_mode

        if mode == 'DUPLICATE':
            return self._convert_duplicate(context, source_obj)
        else:
            return self._convert_in_place(context, source_obj)

    # -------------------------------------------------------------------
    # DUPLICATE mode: create a new armature with only the Unity bones
    # -------------------------------------------------------------------
    def _convert_duplicate(self, context, source_obj):
        ensure_object_mode()

        # Gather the Rigify DEF bones and map them
        mapping = self._build_mapping(source_obj)
        if not mapping:
            self.report({'ERROR'}, "No mappable DEF bones found in this armature.")
            return {'CANCELLED'}

        # Create new armature
        new_arm = bpy.data.armatures.new(f"{source_obj.name}_Unity")
        new_obj = bpy.data.objects.new(f"{source_obj.name}_Unity", new_arm)
        context.collection.objects.link(new_obj)
        new_obj.matrix_world = source_obj.matrix_world.copy()

        # Tag it
        new_arm["unity_rig_converted"] = True
        new_arm["unity_rig_generated"] = True

        # Enter edit mode on new armature
        context.view_layer.objects.active = new_obj
        new_obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')

        # Create bones in the new armature copying transforms from source
        # We need to read source bone data - switch back to read from source
        bpy.ops.object.mode_set(mode='OBJECT')

        # Collect source bone data (rest pose)
        source_bone_data = {}
        for bone in source_obj.data.bones:
            source_bone_data[bone.name] = {
                'head_local': bone.head_local.copy(),
                'tail_local': bone.tail_local.copy(),
                'roll': bone.get('roll', 0),
                'matrix_local': bone.matrix_local.copy(),
            }

        # Also get roll from edit bones
        context.view_layer.objects.active = source_obj
        bpy.ops.object.mode_set(mode='EDIT')
        for eb in source_obj.data.edit_bones:
            if eb.name in source_bone_data:
                source_bone_data[eb.name]['roll'] = eb.roll
        bpy.ops.object.mode_set(mode='OBJECT')

        # Switch to new armature edit mode
        context.view_layer.objects.active = new_obj
        bpy.ops.object.mode_set(mode='EDIT')
        new_edit_bones = new_arm.edit_bones

        # Track which Unity bones we've created and their source Rigify bone
        created = {}  # unity_name -> rigify_name

        # First pass: create bones (without parents)
        for rig_name, unity_name in mapping.items():
            if unity_name in created:
                # Skip duplicate mappings (e.g., thigh.L.001 also maps to LeftUpperLeg)
                # Keep the one without .001 suffix (the primary bone)
                if ".001" in rig_name:
                    continue
                # If current stored one has .001 and new one doesn't, replace
                if ".001" not in created[unity_name]:
                    continue

            if rig_name not in source_bone_data:
                continue

            data = source_bone_data[rig_name]
            eb = new_edit_bones.new(unity_name)
            eb.head = data['head_local']
            eb.tail = data['tail_local']
            eb.roll = data['roll']
            eb.use_deform = True
            created[unity_name] = rig_name

        # Second pass: set up parent relationships based on Unity hierarchy
        for unity_name in created:
            if unity_name not in BONE_LOOKUP:
                continue
            parent_name = BONE_LOOKUP[unity_name][0]  # parent from bone_data
            if parent_name and parent_name in new_edit_bones:
                new_edit_bones[unity_name].parent = new_edit_bones[parent_name]

        # Add Root bone if not present
        if "Root" not in new_edit_bones and "Hips" in new_edit_bones:
            hips = new_edit_bones["Hips"]
            root = new_edit_bones.new("Root")
            root.head = hips.head.copy()
            root.head.z = 0
            root.tail = root.head.copy()
            root.tail.z = 0.05
            root.use_deform = True
            hips.parent = root

        bpy.ops.object.mode_set(mode='OBJECT')

        # Transfer vertex groups from source meshes
        self._transfer_vertex_groups(source_obj, new_obj, mapping, created)

        # Reparent meshes to new armature
        self._reparent_meshes(context, source_obj, new_obj)

        # Transfer animations
        self._transfer_animations(source_obj, new_obj, mapping, created)

        bone_count = len(new_obj.data.bones)
        self.report({'INFO'},
                    f"Created Unity armature '{new_obj.name}' with {bone_count} bones. "
                    f"Mapped {len(created)} bones from Rigify.")
        return {'FINISHED'}

    # -------------------------------------------------------------------
    # IN_PLACE mode: rename bones directly in the existing armature
    # -------------------------------------------------------------------
    def _convert_in_place(self, context, source_obj):
        mapping = self._build_mapping(source_obj)
        if not mapping:
            self.report({'ERROR'}, "No mappable DEF bones found.")
            return {'CANCELLED'}

        ensure_object_mode()

        # Remove non-DEF bones (MCH, ORG, control bones)
        context.view_layer.objects.active = source_obj
        bpy.ops.object.mode_set(mode='EDIT')

        edit_bones = source_obj.data.edit_bones
        bones_to_remove = []
        for eb in edit_bones:
            if eb.name not in mapping:
                bones_to_remove.append(eb.name)

        for bname in bones_to_remove:
            eb = edit_bones.get(bname)
            if eb:
                edit_bones.remove(eb)

        bpy.ops.object.mode_set(mode='OBJECT')

        # Rename remaining DEF bones to Unity names
        # We need to handle conflicts: rename in two passes to avoid name collisions
        # Pass 1: rename to temporary names
        temp_map = {}
        for rig_name, unity_name in mapping.items():
            bone = source_obj.data.bones.get(rig_name)
            if bone:
                temp_name = f"__TEMP_{unity_name}"
                bone.name = temp_name
                temp_map[temp_name] = unity_name

        # Pass 2: rename from temp to final
        for temp_name, unity_name in temp_map.items():
            bone = source_obj.data.bones.get(temp_name)
            if bone:
                bone.name = unity_name

        # Fix hierarchy
        bpy.ops.object.mode_set(mode='EDIT')
        edit_bones = source_obj.data.edit_bones

        for unity_name in list(temp_map.values()):
            if unity_name not in BONE_LOOKUP:
                continue
            parent_name = BONE_LOOKUP[unity_name][0]
            eb = edit_bones.get(unity_name)
            if eb and parent_name and parent_name in edit_bones:
                eb.parent = edit_bones[parent_name]

        # Add Root if needed
        if "Root" not in edit_bones and "Hips" in edit_bones:
            hips = edit_bones["Hips"]
            root = edit_bones.new("Root")
            root.head = hips.head.copy()
            root.head.z = 0
            root.tail = root.head.copy()
            root.tail.z = 0.05
            root.use_deform = True
            hips.parent = root

        bpy.ops.object.mode_set(mode='OBJECT')

        # Rename vertex groups on child meshes
        for child in source_obj.children:
            if child.type == 'MESH':
                for rig_name, unity_name in mapping.items():
                    vg = child.vertex_groups.get(rig_name)
                    if vg:
                        vg.name = unity_name

        # Rename animation F-curves
        if source_obj.animation_data and source_obj.animation_data.action:
            action = source_obj.animation_data.action
            for fc in action.fcurves:
                for rig_name, unity_name in mapping.items():
                    old_path = f'pose.bones["{rig_name}"]'
                    new_path = f'pose.bones["{unity_name}"]'
                    if old_path in fc.data_path:
                        fc.data_path = fc.data_path.replace(old_path, new_path)

        # Tag
        source_obj.data["unity_rig_generated"] = True

        renamed = len([b for b in source_obj.data.bones if b.name in ALL_BONE_NAMES])
        self.report({'INFO'},
                    f"Converted in-place: {renamed} bones renamed to Unity convention.")
        return {'FINISHED'}

    # -------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------
    def _build_mapping(self, source_obj):
        """Build a mapping of source bone names -> Unity names, filtering to
        bones that actually exist in the armature."""
        mapping = {}
        seen_unity_names = set()

        for bone in source_obj.data.bones:
            if bone.name in RIGIFY_TO_UNITY:
                unity_name = RIGIFY_TO_UNITY[bone.name]
                # Prefer primary bones over .001 variants
                if unity_name in seen_unity_names:
                    if ".001" in bone.name:
                        continue
                mapping[bone.name] = unity_name
                seen_unity_names.add(unity_name)

        return mapping

    def _transfer_vertex_groups(self, source_obj, new_obj, mapping, created):
        """Copy and rename vertex groups from meshes parented to source."""
        # Build rig_name -> unity_name map from created dict (reversed)
        unity_to_rig = {v: k for k, v in created.items()}

        for child in source_obj.children:
            if child.type != 'MESH':
                continue

            for unity_name, rig_name in unity_to_rig.items():
                vg = child.vertex_groups.get(rig_name)
                if vg:
                    vg.name = unity_name

    def _reparent_meshes(self, context, source_obj, new_obj):
        """Reparent mesh children from source to new armature."""
        for child in list(source_obj.children):
            if child.type != 'MESH':
                continue

            # Update Armature modifier target
            for mod in child.modifiers:
                if mod.type == 'ARMATURE' and mod.object == source_obj:
                    mod.object = new_obj

            # Reparent
            child.parent = new_obj
            child.matrix_parent_inverse = new_obj.matrix_world.inverted()

    def _transfer_animations(self, source_obj, new_obj, mapping, created):
        """Transfer and remap animations from source to new armature."""
        if not source_obj.animation_data:
            return

        # created = {unity_name: rig_name}, we need {rig_name: unity_name}
        name_map = {rig_name: unity_name for unity_name, rig_name in created.items()}

        # Copy action
        source_action = source_obj.animation_data.action
        if source_action is None:
            return

        new_action = source_action.copy()
        new_action.name = f"{source_action.name}_Unity"

        # Remap F-curve data paths
        for fc in new_action.fcurves:
            for rig_name, unity_name in name_map.items():
                old_path = f'pose.bones["{rig_name}"]'
                new_path = f'pose.bones["{unity_name}"]'
                if old_path in fc.data_path:
                    fc.data_path = fc.data_path.replace(old_path, new_path)
                    break

        # Assign to new armature
        if new_obj.animation_data is None:
            new_obj.animation_data_create()
        new_obj.animation_data.action = new_action


classes = (
    UNITYRIG_OT_convert_rigify,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
