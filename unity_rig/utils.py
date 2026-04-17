"""Shared utility functions for bone creation, constraints, and drivers."""

import bpy
from mathutils import Vector


def ensure_edit_mode(armature_obj):
    """Switch to edit mode on the given armature, selecting it first."""
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='EDIT')


def ensure_pose_mode(armature_obj):
    """Switch to pose mode on the given armature."""
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='POSE')


def ensure_object_mode():
    """Switch to object mode."""
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')


def get_or_create_bone_collection(armature, name, visible=True):
    """Get or create a bone collection on the armature (Blender 4.x API)."""
    colls = armature.data.collections
    coll = colls.get(name)
    if coll is None:
        coll = colls.new(name=name)
    coll.is_visible = visible
    return coll


def create_edit_bone(armature, name, head, tail, parent_name=None, roll=0,
                     use_deform=False, collection_name=None, use_connect=False):
    """Create an edit bone. Must be called in EDIT mode.

    Returns the new EditBone.
    """
    edit_bones = armature.data.edit_bones
    bone = edit_bones.new(name)
    bone.head = head
    bone.tail = tail
    bone.roll = roll
    bone.use_deform = use_deform
    bone.use_connect = use_connect

    if parent_name and parent_name in edit_bones:
        bone.parent = edit_bones[parent_name]

    return bone


def assign_bone_collection(armature, bone_name, collection_name):
    """Assign a bone to a collection. Can be called in EDIT or OBJECT mode."""
    coll = armature.data.collections.get(collection_name)
    if coll is None:
        return
    # In Blender 4.x, we assign via the bone's collections
    bone = armature.data.bones.get(bone_name)
    if bone is None:
        return
    # Remove from all other collections first, then add to target
    for c in armature.data.collections:
        if bone_name in [b.name for b in c.bones]:
            c.unassign(bone)
    coll.assign(bone)


def assign_bone_collections_batch(armature, assignments):
    """Assign multiple bones to collections.

    assignments: dict of {collection_name: [bone_name, ...]}
    Must be called in OBJECT or POSE mode (needs data bones, not edit bones).
    """
    for coll_name, bone_names in assignments.items():
        coll = armature.data.collections.get(coll_name)
        if coll is None:
            continue
        for bname in bone_names:
            bone = armature.data.bones.get(bname)
            if bone is not None:
                coll.assign(bone)


def add_copy_rotation_constraint(armature_obj, bone_name, target_bone,
                                 influence=1.0, name="Copy Rotation"):
    """Add a Copy Rotation constraint to a pose bone."""
    pb = armature_obj.pose.bones.get(bone_name)
    if pb is None:
        return None
    con = pb.constraints.new('COPY_ROTATION')
    con.name = name
    con.target = armature_obj
    con.subtarget = target_bone
    con.influence = influence
    return con


def add_copy_location_constraint(armature_obj, bone_name, target_bone,
                                 influence=1.0, name="Copy Location"):
    """Add a Copy Location constraint to a pose bone."""
    pb = armature_obj.pose.bones.get(bone_name)
    if pb is None:
        return None
    con = pb.constraints.new('COPY_LOCATION')
    con.name = name
    con.target = armature_obj
    con.subtarget = target_bone
    con.influence = influence
    return con


def add_copy_transforms_constraint(armature_obj, bone_name, target_bone,
                                   influence=1.0, name="Copy Transforms"):
    """Add a Copy Transforms constraint to a pose bone."""
    pb = armature_obj.pose.bones.get(bone_name)
    if pb is None:
        return None
    con = pb.constraints.new('COPY_TRANSFORMS')
    con.name = name
    con.target = armature_obj
    con.subtarget = target_bone
    con.influence = influence
    return con


def add_ik_constraint(armature_obj, bone_name, target_bone=None,
                      pole_target_bone=None, chain_count=2,
                      pole_angle=0, name="IK"):
    """Add an Inverse Kinematics constraint to a pose bone."""
    pb = armature_obj.pose.bones.get(bone_name)
    if pb is None:
        return None
    con = pb.constraints.new('IK')
    con.name = name
    if target_bone:
        con.target = armature_obj
        con.subtarget = target_bone
    con.chain_count = chain_count
    if pole_target_bone:
        con.pole_target = armature_obj
        con.pole_subtarget = pole_target_bone
        con.pole_angle = pole_angle
    return con


def add_track_to_constraint(armature_obj, bone_name, target_bone,
                            track_axis='TRACK_NEGATIVE_Z', up_axis='UP_Y',
                            influence=1.0, name="Track To"):
    """Add a Track To constraint to a pose bone."""
    pb = armature_obj.pose.bones.get(bone_name)
    if pb is None:
        return None
    con = pb.constraints.new('TRACK_TO')
    con.name = name
    con.target = armature_obj
    con.subtarget = target_bone
    con.track_axis = track_axis
    con.up_axis = up_axis
    con.influence = influence
    return con


def add_limit_rotation_constraint(armature_obj, bone_name, owner_space='LOCAL',
                                  use_limit_x=False, min_x=0, max_x=0,
                                  use_limit_y=False, min_y=0, max_y=0,
                                  use_limit_z=False, min_z=0, max_z=0,
                                  name="Limit Rotation"):
    """Add a Limit Rotation constraint."""
    pb = armature_obj.pose.bones.get(bone_name)
    if pb is None:
        return None
    con = pb.constraints.new('LIMIT_ROTATION')
    con.name = name
    con.owner_space = owner_space
    con.use_limit_x = use_limit_x
    con.min_x = min_x
    con.max_x = max_x
    con.use_limit_y = use_limit_y
    con.min_y = min_y
    con.max_y = max_y
    con.use_limit_z = use_limit_z
    con.min_z = min_z
    con.max_z = max_z
    return con


def add_custom_property(armature_obj, bone_name, prop_name, default=0.0,
                        min_val=0.0, max_val=1.0, description=""):
    """Add a custom property to a pose bone with min/max and UI settings."""
    pb = armature_obj.pose.bones.get(bone_name)
    if pb is None:
        return
    pb[prop_name] = default

    # Set up the property with RNA path for UI
    id_props = pb.id_properties_ui(prop_name)
    id_props.update(min=min_val, max=max_val, soft_min=min_val, soft_max=max_val,
                    description=description)


def add_driver(armature_obj, target_bone, data_path, driven_property_idx,
               driver_bone, driver_prop, expression=None):
    """Add a driver to a constraint or bone property.

    target_bone: the bone whose property is being driven
    data_path: full data path from the pose bone (e.g. 'constraints["IK"].influence')
    driven_property_idx: array index (-1 for non-array)
    driver_bone: name of the bone with the driving custom property
    driver_prop: name of the custom property
    expression: optional expression string; if None, uses 'var' directly
    """
    pb = armature_obj.pose.bones.get(target_bone)
    if pb is None:
        return None

    full_path = f'pose.bones["{target_bone}"].{data_path}'

    if driven_property_idx >= 0:
        fcurve = armature_obj.data.driver_add(full_path, driven_property_idx)
    else:
        # Try on the object first
        try:
            fcurve = armature_obj.driver_add(full_path)
        except TypeError:
            fcurve = armature_obj.data.driver_add(full_path)

    driver = fcurve.driver

    if expression:
        driver.type = 'SCRIPTED'
        driver.expression = expression
    else:
        driver.type = 'AVERAGE'

    var = driver.variables.new()
    var.name = "var"
    var.type = 'SINGLE_PROP'
    var.targets[0].id = armature_obj
    var.targets[0].data_path = f'pose.bones["{driver_bone}"]["{driver_prop}"]'

    return fcurve


def create_widget_mesh(name, verts, edges):
    """Create a simple wireframe mesh to use as a bone custom shape."""
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, edges, [])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    # Put widget objects in a hidden collection
    widget_coll = bpy.data.collections.get("_UR_Widgets")
    if widget_coll is None:
        widget_coll = bpy.data.collections.new("_UR_Widgets")
        bpy.context.scene.collection.children.link(widget_coll)
        widget_coll.hide_viewport = True
    widget_coll.objects.link(obj)
    return obj


def create_cube_widget(name="WGT_Cube", size=0.1):
    """Create a cube wireframe widget."""
    s = size
    verts = [
        (-s, -s, -s), (s, -s, -s), (s, s, -s), (-s, s, -s),
        (-s, -s,  s), (s, -s,  s), (s, s,  s), (-s, s,  s),
    ]
    edges = [
        (0,1),(1,2),(2,3),(3,0),
        (4,5),(5,6),(6,7),(7,4),
        (0,4),(1,5),(2,6),(3,7),
    ]
    return create_widget_mesh(name, verts, edges)


def create_circle_widget(name="WGT_Circle", radius=0.15, segments=16):
    """Create a circle wireframe widget."""
    import math
    verts = []
    edges = []
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        verts.append((radius * math.cos(angle), radius * math.sin(angle), 0))
        edges.append((i, (i + 1) % segments))
    return create_widget_mesh(name, verts, edges)


def create_sphere_widget(name="WGT_Sphere", radius=0.08, rings=3, segments=8):
    """Create a sphere wireframe widget (3 circles)."""
    import math
    verts = []
    edges = []
    idx = 0
    for ring in range(rings):
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            if ring == 0:  # XY plane
                verts.append((radius * math.cos(angle), radius * math.sin(angle), 0))
            elif ring == 1:  # XZ plane
                verts.append((radius * math.cos(angle), 0, radius * math.sin(angle)))
            else:  # YZ plane
                verts.append((0, radius * math.cos(angle), radius * math.sin(angle)))
            edges.append((idx + i, idx + (i + 1) % segments))
        idx += segments
    return create_widget_mesh(name, verts, edges)


def create_diamond_widget(name="WGT_Diamond", size=0.1):
    """Create a diamond/octahedron wireframe widget."""
    s = size
    verts = [
        (0, 0, s), (s, 0, 0), (0, s, 0),
        (-s, 0, 0), (0, -s, 0), (0, 0, -s),
    ]
    edges = [
        (0,1),(0,2),(0,3),(0,4),
        (5,1),(5,2),(5,3),(5,4),
        (1,2),(2,3),(3,4),(4,1),
    ]
    return create_widget_mesh(name, verts, edges)


def create_arrow_widget(name="WGT_Arrow", length=0.2, width=0.06):
    """Create an arrow wireframe widget pointing along Y."""
    w = width
    l = length
    verts = [
        (0, 0, 0), (0, l * 0.6, 0),           # shaft
        (-w, l * 0.6, 0), (w, l * 0.6, 0),     # arrowhead base
        (0, l, 0),                               # arrowhead tip
    ]
    edges = [(0,1), (2,4), (3,4), (2,3)]
    return create_widget_mesh(name, verts, edges)


def set_bone_widget(armature_obj, bone_name, widget_obj):
    """Assign a custom shape widget to a pose bone."""
    pb = armature_obj.pose.bones.get(bone_name)
    if pb is not None:
        pb.custom_shape = widget_obj


def lock_bone_transforms(armature_obj, bone_name,
                         lock_loc=(False, False, False),
                         lock_rot=(False, False, False),
                         lock_scale=(True, True, True)):
    """Lock specific transform channels on a pose bone."""
    pb = armature_obj.pose.bones.get(bone_name)
    if pb is None:
        return
    for i in range(3):
        pb.lock_location[i] = lock_loc[i]
        pb.lock_rotation[i] = lock_rot[i]
        pb.lock_scale[i] = lock_scale[i]


def set_bone_color(armature_obj, bone_name, color_palette):
    """Set a bone's color using Blender 4.x bone color API.

    color_palette: one of 'DEFAULT', 'THEME01' .. 'THEME20', 'CUSTOM'
    """
    pb = armature_obj.pose.bones.get(bone_name)
    if pb is not None:
        pb.color.palette = color_palette
