# Unity Rig - Blender Addon

A Blender 4.x addon that creates **Unity Humanoid Avatar-compatible** animation rigs and converts existing **Rigify** rigs for Unity export.

Blender's Rigify produces complex multi-layer bone hierarchies that Unity's Humanoid system cannot auto-map. Unity Rig solves this from both directions: building new Unity-native rigs from scratch, and converting existing Rigify rigs to Unity's naming and hierarchy conventions.

## Features

- **Create Unity metarigs** with correct bone names and hierarchy for Unity's Humanoid Avatar
- **Full IK/FK switching** on arms and legs with blend sliders and snap operators
- **Finger controls** - 15 bones per hand with per-finger curl, master fist, and spread controls
- **Rigify conversion** - convert an existing Rigify rig to Unity format (duplicate or in-place)
- **One-click FBX export** with Unity-optimal settings
- **Eye tracking** and jaw controls
- **Shoulder controls** with independent rotation

## Requirements

- Blender 4.0 or later

## Installation

1. Download or build `unity_rig.zip`
2. In Blender: **Edit > Preferences > Add-ons**
3. Click **Install from Disk** and select `unity_rig.zip`
4. Enable the checkbox next to **Unity Rig**

## Usage

### Creating a New Rig

#### 1. Create the Metarig

From the 3D Viewport in Object Mode:

- **Add > Armature > Unity Humanoid (Metarig)**, or
- Open the **N-panel** (press `N`), go to the **Unity Rig** tab, and click **Create Unity Metarig**

Options (in the N-panel before creating):
- **Include Fingers** - adds 30 finger bones (5 fingers x 3 joints x 2 hands)
- **Include Eyes** - adds eye and jaw bones

This creates a T-pose armature with bones named exactly as Unity expects (Hips, Spine, Chest, LeftUpperArm, etc.).

#### 2. Fit the Metarig to Your Mesh

- **Scale** the armature in Object Mode (`S`) to roughly match your character's size
- Enter **Edit Mode** (`Tab`) and position individual bones to align with your mesh's joints
- Pay attention to: hip position, shoulder width, elbow/knee placement, hand and finger alignment

#### 3. Generate the Rig

In the N-panel under **Unity Rig > Create Rig**:

- Choose **Default Limb Mode** (IK or FK)
- Click **Generate Unity Rig**

This adds control bones, IK/FK constraints, drivers, widgets, and organizes everything into bone collections. The metarig becomes a full animation rig.

### Compatability

This workflow has been tested with Kevin Iglesias' free human movement animations.

### Animating

After generating, the rig has three bone layers (Blender bone collections):

| Collection | Contents | Visible |
|---|---|---|
| **DEF** | Deformation bones (Unity names, exported) | Hidden |
| **CTRL** | Animation controls (what you keyframe) | Visible |
| **MCH** | Mechanism bones (IK solver chain) | Hidden |

#### IK/FK Switching

Each limb has an IK/FK blend slider in the **N-panel > Unity Rig > IK/FK Controls** section:

- **0.0 = IK mode** - position the hand/foot target and pole target; the chain solves automatically
- **1.0 = FK mode** - rotate each joint (upper arm, lower arm, hand) individually
- Values between 0 and 1 blend between both

Use **Snap IK to FK** or **Snap FK to IK** to match one mode's pose to the other before switching.

#### Finger Controls

- **CTRL-Fist-Left/Right** - `fist` property curls all fingers at once (0 = open, 1 = closed)
- **CTRL-Spread-Left/Right** - `spread` property fans fingers apart
- **CTRL-Curl-{Side}{Finger}** - per-finger curl control
- **CTRL-{Side}{Finger}{Segment}** - individual joint rotation for fine-tuning

#### Other Controls

- **CTRL-Root** - moves the entire rig
- **CTRL-Hips** - hip translation and rotation
- **CTRL-Spine / Chest / UpperChest** - torso rotation
- **CTRL-Neck / Head** - neck and head rotation
- **CTRL-EyeTarget** - both eyes track this target
- **CTRL-LeftEyeTarget / CTRL-RightEyeTarget** - individual eye targets
- **CTRL-Jaw** - jaw rotation
- **CTRL-LeftShoulder / CTRL-RightShoulder** - shoulder rotation

### Converting a Rigify Rig

If you already have a character rigged with Rigify:

1. Select the Rigify armature
2. Open **N-panel > Unity Rig > Convert Rigify**
3. Choose a conversion mode:
   - **Duplicate** - creates a new clean armature with Unity bone names alongside the original (non-destructive)
   - **In-Place** - renames bones directly in the existing armature (destructive, no undo beyond Blender's undo stack)
4. Click **Convert Rigify to Unity**

The converter:
- Maps Rigify DEF bone names to Unity Humanoid names
- Rebuilds the parent hierarchy to match Unity's expectations
- Renames vertex groups on child meshes so skinning transfers
- Remaps animation F-curves to the new bone names

### Exporting to Unity

1. Select the rig armature
2. Open **N-panel > Unity Rig > Export to Unity**
3. Set options:
   - **Export Path** - where to save the `.fbx` file
   - **Export Animations** - include animation data
   - **Export Meshes** - include mesh children
4. Click **Export Unity FBX**

The export uses these Unity-optimal settings:
- Only deform bones are exported (CTRL and MCH bones are excluded)
- No leaf bones added
- Correct axis orientation for Unity (`Y`-up, `-Z`-forward)
- Scale set to `FBX_SCALE_ALL`

### Importing in Unity

1. Drag the `.fbx` file into your Unity project
2. Select the imported asset
3. In the **Inspector > Rig** tab, set **Animation Type** to **Humanoid**
4. Click **Apply** - Unity should auto-detect and map all bones (green checkmarks in the Avatar Configuration)


## Bone Hierarchy

```
Root
+-- Hips
    +-- Spine
    |   +-- Chest
    |       +-- UpperChest
    |           +-- Neck
    |           |   +-- Head
    |           |       +-- LeftEye / RightEye
    |           |       +-- Jaw
    |           +-- LeftShoulder -- LeftUpperArm -- LeftLowerArm -- LeftHand -- [fingers]
    |           +-- RightShoulder -- RightUpperArm -- RightLowerArm -- RightHand -- [fingers]
    +-- LeftUpperLeg -- LeftLowerLeg -- LeftFoot -- LeftToes
    +-- RightUpperLeg -- RightLowerLeg -- RightFoot -- RightToes
```

Each finger: `{Side}{Finger}Proximal > Intermediate > Distal`
Fingers: Thumb, Index, Middle, Ring, Little (5 per hand, 3 bones each)

## File Structure

```
unity_rig/
    __init__.py              # Addon registration
    bone_data.py             # Bone definitions, hierarchy, Rigify mapping
    utils.py                 # Bone creation, constraints, widgets, drivers
    operators/
        create_metarig.py    # Create Unity metarig template
        generate_rig.py      # Generate full rig from metarig
        convert_rigify.py    # Convert Rigify rig to Unity format
        export_fbx.py        # One-click Unity FBX export
    rig_components/
        root.py              # Root and Hips controls
        spine.py             # Spine chain controls
        head.py              # Head, neck, eyes, jaw
        limb.py              # IK/FK arms and legs
        hand.py              # Finger controls with curl/spread
    ui/
        panels.py            # N-panel interface
        properties.py        # Scene properties
```

## License

MIT
