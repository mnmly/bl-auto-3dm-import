import bpy

class RhinoBridgeProperties(bpy.types.PropertyGroup):
    port: bpy.props.IntProperty(default=28889)
    running: bpy.props.BoolProperty()