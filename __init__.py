# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from re import A
import bpy, threading, os, time, json, socket
from bpy.app.handlers import persistent
from .panel import RhinoBridgePanel
from .properties import RhinoBridgeProperties
from .operators import SocketManager, execute_queued_functions

bl_info = {
    "name" : "bl-rhinobridge",
    "author" : "Hiroaki Yamane",
    "description" : "",
    "blender" : (3, 0, 0),
    "version" : (0, 0, 1),
    "location" : "3D View > RhinoBridge",
    "warning" : "",
    "category" : "3D View"
}

@persistent
def load_plugin_(scene):
    try:
        bpy.ops.rhino.autoimport()
    except Exception as e:
        print( "rhinobridge Error::Could not start the plugin. Description: ", str(e) )

@bpy.app.handlers.persistent
def check_timers_timer():
    """Check if all timers are registered regularly.
    Prevents possible bugs from stopping the addon.
    Returns:
        float: time between executions
    """
    if not bpy.app.timers.is_registered(execute_queued_functions):
        bpy.app.timers.register(execute_queued_functions)
    return 5.


CLASSES = [ SocketManager, RhinoBridgePanel, RhinoBridgeProperties]

def register():
    for c in CLASSES:
        bpy.utils.register_class(c)
    bpy.types.Scene.rhinobridge_props = bpy.props.PointerProperty(type=RhinoBridgeProperties)
    bpy.app.handlers.load_post.append(load_plugin_)
    bpy.app.timers.register(check_timers_timer, persistent=True)
    if len(bpy.app.handlers.load_post) > 0:
        # Check if trying to register twice.
        if "load_plugin_" in bpy.app.handlers.load_post[0].__name__.lower() or load_plugin_ in bpy.app.handlers.load_post:
            return


def unregister():
    del bpy.types.Scene.rhinobridge_props
    for c in CLASSES:
        bpy.utils.unregister_class(c)
    bpy.app.timers.unregister(check_timers_timer)
    globals()['operator'] = None
    if len(bpy.app.handlers.load_post) > 0:
        # Check if trying to register twice.
        if "load_plugin_" in bpy.app.handlers.load_post[0].__name__.lower() or load_plugin_ in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.remove(load_plugin_)

if __name__ == "__main__":
    register()