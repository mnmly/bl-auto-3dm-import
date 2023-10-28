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
import queue
from bpy.app.handlers import persistent
from .panel import RhinoBridgePanel
from .properties import RhinoBridgeProperties

execution_queue = queue.Queue()

bl_info = {
    "name" : "bl-rhinobridge",
    "author" : "Hiroaki Yamane",
    "description" : "",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 1),
    "location" : "",
    "warning" : "",
    "category" : "Generic"
}

class Thread_Init(threading.Thread):
    
	#Initialize the thread and assign the method (i.e. importer) to be called when it receives JSON data.
    def __init__(self, importer):
        threading.Thread.__init__(self)
        self.importer = importer

	#Start the thread to start listing to the port.
    def run(self):
        try:
            run_livelink = True
            bpy.context.scene.rhinobridge_props.running = True
            host, port = 'localhost', bpy.context.scene.rhinobridge_props.port
            #Making a socket object.
            socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #Binding the socket to host and port number mentioned at the start.
            socket_.bind((host, port))

            #Run until the thread starts receiving data.
            while run_livelink:
                socket_.listen(5)
                #Accept connection request.
                client, addr = socket_.accept()
                data = ""
                buffer_size = 4096*2
                #Receive data from the client. 
                data = client.recv(buffer_size)
                if data == b'Bye RhinoBridge':
                    run_livelink = False
                    bpy.context.scene.rhinobridge_props.running = False
                    break

                #If any data is received over the port.
                if data != "":
                    self.TotalData = b""
                    self.TotalData += data #Append the previously received data to the Total Data.
                    #Keep running until the connection is open and we are receiving data.
                    while run_livelink:
                        #Keep receiving data from client.
                        data = client.recv(4096*2)
                        if data == b'Bye RhinoBridge':
                            run_livelink = False
                            bpy.context.scene.rhinobridge_props.running = False
                            break
                        #if we are getting data keep appending it to the Total data.
                        if data : self.TotalData += data
                        else:
                            #Once the data transmission is over call the importer method and send the collected TotalData.
                            self.importer(self.TotalData)
                            break
        except Exception as e:
            bpy.context.scene.rhinobridge_props.running = False
            print( "RhinoBridge Plugin Error initializing the thread. Error: ", str(e) )

class thread_checker(threading.Thread):
    
	#Initialize the thread and assign the method (i.e. importer) to be called when it receives JSON data.
    def __init__(self):
        threading.Thread.__init__(self)

	#Start the thread to start listing to the port.
    def run(self):
        try:
            run_checker = True
            while run_checker:
                time.sleep(3)
                for i in threading.enumerate():
                    if(i.getName() == "MainThread" and i.is_alive() == False):
                        host, port = 'localhost', 28889
                        s = socket.socket()
                        s.connect((host,port))
                        data = "Bye RhinoBridge"
                        s.send(data.encode())
                        s.close()
                        run_checker = False
                        break
        except Exception as e:
            print( "RhinoBridge Plugin Error initializing thread checker. Error: ", str(e) )
            pass

class Init_RhinoAutoImport():

    # This initialization method create the data structure to process our assets
    # later on in the initImportProcess method. The method loops on all assets
    # that have been sent by Bridge.
    def __init__(self):
        print("Initialized import class...")
        try:
            # Check if there's any incoming data
            if globals()['RhinoAutoImport_DataSet'] != None:
                # print(globals()['RhinoAutoImport_DataSet'])
                self.data = json.loads(globals()['RhinoAutoImport_DataSet'])
                filepath = self.data['filepath']
                def my_fn():
                    print(filepath)
                    bpy.ops.import_3dm.some_data(filepath=filepath, import_named_views=False, import_instances=True, update_materials=False)

                run_in_main_thread(my_fn)

        except Exception as e:
            print( "RhinoBridge Plugin Error initializing the import process. Error: ", str(e) )
        globals()['RhinoAutoImport_DataSet'] = None
    

def run_in_main_thread(function):
    execution_queue.put(function)

def execute_queued_functions():
    while not execution_queue.empty():
        function = execution_queue.get()
        function()
    return 1.0


class RHINOBRIDGE_OT_socketstop(bpy.types.Operator):
    bl_idname = "rhinobridge.socketstop"
    bl_label = "RhinoBridge Socket Stop"

    def execute(self, context):

        try:
            host, port = 'localhost', context.scene.rhinobridge_props.port
            s = socket.socket()
            s.connect((host,port))
            data = "Bye RhinoBridge"
            s.send(data.encode())
            s.close()
            return {'FINISHED'}

        except Exception as e:
            print( "RhinoBridge Plugin Error failing to stop thread. Error: ", str(e) )
            return {"FAILED"}

class RHINOBRIDGE_OT_socketstart(bpy.types.Operator):

    bl_idname = "rhino.autoimport"
    bl_label = "RhinoBridge Socket Start"
    socketCount = 0

    def execute(self, context):

        try:
            globals()['RhinoAutoImport_DataSet'] = None
            self.thread_ = threading.Thread(target = self.socketMonitor)
            self.thread_.start()
            bpy.app.timers.register(self.newDataMonitor)
            return {'FINISHED'}
        except Exception as e:
            print( "RhinoBridge Plugin Error starting blender plugin. Error: ", str(e) )
            return {"FAILED"}

    def newDataMonitor(self):
        try:
            if globals()['RhinoAutoImport_DataSet'] != None:
                Init_RhinoAutoImport()
                globals()['RhinoAutoImport_DataSet'] = None       
        except Exception as e:
            print( "RhinoBridge Plugin Error starting blender plugin (newDataMonitor). Error: ", str(e) )
            return {"FAILED"}
        return 1.0


    def socketMonitor(self):
        try:
            #Making a thread object
            threadedServer = Thread_Init(self.importer)
            #Start the newly created thread.
            threadedServer.start()
            #Making a thread object
            thread_checker_ = thread_checker()
            #Start the newly created thread.
            thread_checker_.start()
        except Exception as e:
            print( "RhinoBridge Plugin Error starting blender plugin (socketMonitor). Error: ", str(e) )
            return {"FAILED"}

    def importer (self, recv_data):
        try:
            globals()['RhinoAutoImport_DataSet'] = recv_data
        except Exception as e:
            print( "RhinoBridge Plugin Error starting blender plugin (importer). Error: ", str(e) )
            return {"FAILED"}

@persistent
def load_plugin_(scene):
    print('LOADING PLUGIN')
    try:
        bpy.ops.rhino.autoimport()
    except Exception as e:
        print( "rhino.autoimport Error::Could not start the plugin. Description: ", str(e) )

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


CLASSES = [ RHINOBRIDGE_OT_socketstart, RHINOBRIDGE_OT_socketstop, RhinoBridgePanel, RhinoBridgeProperties]

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
    if len(bpy.app.handlers.load_post) > 0:
        # Check if trying to register twice.
        if "load_plugin_" in bpy.app.handlers.load_post[0].__name__.lower() or load_plugin_ in bpy.app.handlers.load_post:
            bpy.app.handlers.load_post.remove(load_plugin_)