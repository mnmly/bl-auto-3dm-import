import bpy

class RhinoBridgePanel(bpy.types.Panel):

    bl_idname = 'VIEW3D_PT_rhinobridge'
    bl_label = 'RhinoBridge Panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'RhinoBridge'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.rhinobridge_props
        layout.prop(props, 'port')

        row = layout.row()
        operator = row.operator("rhinobridge.socketmanager", text="Stop" if props.running else 'Start')
        if not ('operator' in globals()):
            globals()['operator'] = operator