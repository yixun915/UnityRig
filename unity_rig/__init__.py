bl_info = {
    "name": "Unity Rig",
    "author": "Mike Simon",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Unity Rig",
    "description": "Create Unity Humanoid-compatible rigs and convert Rigify rigs for Unity export",
    "category": "Rigging",
}

from . import operators
from . import ui


def register():
    operators.register()
    ui.register()


def unregister():
    ui.unregister()
    operators.unregister()


if __name__ == "__main__":
    register()
