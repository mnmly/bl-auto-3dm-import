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
        state = scene.rhinobridge
        layout.prop(state, 'port')

        row = layout.row()
        operator = row.operator("rhinobridge.socketmanager", text="Stop" if state.running else 'Start')
        if not ('operator' in globals()):
            globals()['operator'] = operator