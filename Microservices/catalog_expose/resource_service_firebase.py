import cherrypy
import json
import datetime
import uuid
import requests
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

class CatalogExpose:
    exposed = True
    def __init__(self):
        cred = credentials.Certificate("firebase_key.json")
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://smartvase-effeb-default-rtdb.europe-west1.firebasedatabase.app' 
        })
        self.firebase_ref = db.reference('resource_catalog/')

    @cherrypy.tools.json_out()
    def GET(self, *args, **kwargs):
        print(args)
        if args[0] == 'listDevice':
            return self.listDevice()
        elif args[0] == 'listVase':
            return self.listVase()
        elif args[0] == 'listUser':
            return self.listUser()
        
        elif args[0].startswith('device') and args[1]:
            d_id = args[1]
            return self.firebase_ref.child('deviceList').order_by_child("device_id").equal_to(d_id).get()
        elif args[0].startswith('vaseByDevice') and args[1]:
            d_id = args[1]
            return self.firebase_ref.child('vaseList').order_by_child("device_id").equal_to(d_id).get()
        elif args[0].startswith('vase') and args[1]:
            v_id = args[1]
            return self.firebase_ref.child('vaseList').order_by_child("vase_id").equal_to(v_id).get()
        elif args[0].startswith('user') and args[1]:
            u_id = args[1]
            return self.firebase_ref.child('userList').order_by_child("user_id").equal_to(u_id).get()

        else:
            return {"message": "Invalid resource"}

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self, *args, **kwargs):
        if args[0] == 'device':
            print('Post on device')
            device = cherrypy.request.json
            this_time = datetime.datetime.now()
            device["lastUpdate"] = this_time.strftime("%Y-%m-%d %H:%M:%S")
            device["device_status"] = "active"
            found = False
            print(self.firebase_ref.child('deviceList').order_by_child("device_id").equal_to(device['device_id']).get())

            """ if self.firebase_ref.child('deviceList').order_by_child("device_id").equal_to(device['device_id']).get():
                print("Device already exist")
                found = True """
            if not found:
                if self.firebase_ref.child('userList').order_by_child("user_id").equal_to(device["user_id"]).get():
                    print("User exist")
                    url = "https://api.thingspeak.com/channels.json"
                    data = {
                        'api_key': 'G1PY1LU9KSDV5LEB',
                        'name': 'test_channel3',
                        'public_flag': 'true',  
                        'field1': 'temperature',
                        'field2': 'soil_moisture',
                        'field3': 'light_level',
                        'field4': 'watertank_level'
                    }
                    # Send the POST request
                    response = requests.post(url, data=data)

                    # Print the response
                    if (response.status_code!=200):
                        return
                    channelId = response.json()['id'] 
                    api_keys = response.json()["api_keys"]
                    write_key=""
                    read_key=""
                    for key in api_keys:
                        if key["write_flag"]==True:
                            write_key=key["api_key"]
                        else:
                            read_key=key["api_key"]
                    device['channel_id']= channelId
                    device['write_key']= write_key
                    device['read_key']= read_key
                    self.firebase_ref.child('deviceList').push(device)
                    return {"message": "Device added successfully"}
        elif args[0] == 'vase':
            vase = cherrypy.request.json
            uuid4 = uuid.uuid4()
            this_id = uuid4.int
            this_time = datetime.datetime.now()
            vase["vase_id"] = str(this_id)
            vase["lastUpdate"] = this_time.strftime("%Y-%m-%d %H:%M:%S")
            flag = 0 
            if self.firebase_ref.child('deviceList').order_by_child("device_id").equal_to(vase['device_id']).get():
                flag = 1
            if flag == 0:
                return {"message": "Something went wrong"}
            self.firebase_ref.child('vaseList').push(vase)
            return {"message": "Vase added successfully",
                    "id": this_id}
        elif args[0] == 'user':
            user = cherrypy.request.json
            uuid4 = uuid.uuid4()
            this_id = uuid4.int
            this_time = datetime.datetime.now()
            user["user_id"] = str(this_id)
            user["lastUpdate"] = this_time.strftime("%Y-%m-%d %H:%M:%S")
            self.firebase_ref.child('userList').push(user)
            return {"message": "User added successfully",
                    "id": this_id}
        else:
            print("Post invalid")
            return {"message": "Invalid resource"}


    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def PUT(self, *args, **kwargs):
        if args[0].startswith('device'):
            device_id = args[1]
            device = cherrypy.request.json
            if self.firebase_ref.child('deviceList').order_by_child("device_id").equal_to(device_id).set(device):
                return {"message": "Device updated successfully"}
            return {"message": "Device not found"}
        elif args[0].startswith('vase'):
            vase_id = args[1]
            vase = cherrypy.request.json
            if self.firebase_ref.child('vaseList').order_by_child("vase_id").equal_to(vase_id).set(vase):
                return {"message": "Vase updated successfully"}
            return {"message": "Vase not found"}
        elif args[0].startswith('user'):
            user_id = args[1]
            user = cherrypy.request.json
            if self.firebase_ref.child('userList').order_by_child("user_id").equal_to(user_id).set(user):
                return {"message": "User updated successfully"}
            return {"message": "User not found"}
        else:
            return {"message": "Invalid resource"}

    def listDevice(self):
        return list(self.firebase_ref.child('deviceList').get().values())
    def listUser(self):
        return list(self.firebase_ref.child('userList').get().values())
    def listVase(self):
        return list(self.firebase_ref.child('vaseList').get().values())

if __name__ == '__main__':
    catalog = CatalogExpose()

    conf = {
    '/':{
        'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        'tools.sessions.on' : True
    }
    }
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 5000  # Specify your desired port here
    })
    cherrypy.tree.mount(catalog, '/', conf)
    cherrypy.engine.start()
    cherrypy.engine.block()
