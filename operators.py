import bpy
import socket
import json
import time
import queue
import threading

execution_queue = queue.Queue()

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


class RHINOBRIDGE_SocketStop(bpy.types.Operator):
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


class RHINOBRIDGE_SocketStart(bpy.types.Operator):

    bl_idname = "rhinobridge.socketstart"
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


class SocketManager(bpy.types.Operator):

    bl_idname = "rhinobridge.socketmanager"
    bl_label = "RhinoBridge Socket Manager"


    def execute(self, context):
        if context.scene.rhinobridge_props.running:
            return self.stop_socket(context)
        else:
            return self.start_socket(context)
    
    def stop_socket(self, context):
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
            return {"CANCELLED"}
 
    def start_socket(self, context):
        try:
            globals()['RhinoAutoImport_DataSet'] = None
            self.thread_ = threading.Thread(target = self.socketMonitor)
            self.thread_.start()
            bpy.app.timers.register(self.newDataMonitor)
            return {'FINISHED'}
        except Exception as e:
            print( "RhinoBridge Plugin Error starting blender plugin. Error: ", str(e) )
            return {"CANCELLED"}

    def newDataMonitor(self):
        try:
            if globals()['RhinoAutoImport_DataSet'] != None:
                Init_RhinoAutoImport()
                globals()['RhinoAutoImport_DataSet'] = None       
        except Exception as e:
            print( "RhinoBridge Plugin Error starting blender plugin (newDataMonitor). Error: ", str(e) )
            bpy.context.scene.rhinobridge_props.running = False
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

