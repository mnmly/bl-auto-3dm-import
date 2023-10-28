import bpy

class RhinoBridgePanel(bpy.types.Panel):
    
    bl_idname = 'VIEW3D_PT_rhinobridge_panel'
    bl_label = 'RhinoBridge Panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.rhinobridge_props

        layout.prop(props, 'port')
        layout.label(text='Hello there' if props.running else "hi")
        row = layout.row()
        if props.running:
            row.operator('rhinobridge.socketstop') 
        else:
            row.operator('rhinobridge.socketstart') 