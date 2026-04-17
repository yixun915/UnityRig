from . import properties
from . import panels


def register():
    properties.register()
    panels.register()


def unregister():
    panels.unregister()
    properties.unregister()
