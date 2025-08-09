import cherrypy
import json
import datetime
import uuid
import requests
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import CustomerLogger
import os
import sys


class CatalogExpose:
    exposed = True
    def __init__(self):
        cred = credentials.Certificate("firebase_key.json")
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://iotvase-default-rtdb.europe-west1.firebasedatabase.app' 
        })
        self.firebase_ref = db.reference('resource_catalog/')
        self.logger = CustomerLogger.CustomLogger("resource_service", "user_id_test")


    @cherrypy.tools.json_out()
    def GET(self, *args, **kwargs):
        print(args)
        if args[0] == 'listDevice':
            return self.listDevice()
        elif args[0] == 'listVase':
            return self.listVase()
        elif args[0] == 'listUser':
            return self.listUser()
        
        elif args[0] == 'listDeviceByUser':
            print("listDeviceByUser")
            u_id = args[1]
            result = self.firebase_ref.child('deviceList').order_by_child("user_id").equal_to(u_id).get().values()
            self.logger.info("GET request received: listDeviceByUser")
            return list(result)
        
        elif args[0] == 'listVaseByUser':
            print("listVaseByUser")
            u_id = args[1]
            result = self.firebase_ref.child('vaseList').order_by_child("user_id").equal_to(u_id).get().values()
            self.logger.info("GET request received: listDeviceByUser")
            return list(result)

        elif args[0].startswith('device') and args[1]:
            d_id = args[1]
            result = self.firebase_ref.child('deviceList').order_by_child("device_id").equal_to(d_id).get().values()
            self.logger.info("GET request received: getDeviceById")
            return next(iter(result), None)
        elif args[0].startswith('vaseByDevice') and args[1]:
            d_id = args[1]
            result = self.firebase_ref.child('vaseList').order_by_child("device_id").equal_to(d_id).get().values()
            self.logger.info("GET request received: getVaseByDevice")
            return next(iter(result), None)
        elif args[0].startswith('vase') and args[1]:
            v_id = args[1]
            result = self.firebase_ref.child('vaseList').order_by_child("vase_id").equal_to(v_id).get().values()
            self.logger.info("GET request received: getVaseById")
            return next(iter(result), None)
        elif args[0].startswith('user') and args[1]:
            u_id = args[1]
            result = self.firebase_ref.child('userList').order_by_child("user_id").equal_to(u_id).get().values()
            self.logger.info("GET request received: getUserById")
            return next(iter(result), None)
        elif args[0] == ('getData') and args[1] and kwargs['days']:
            v_id = str(args[1])
            days = kwargs['days']
            result = self.firebase_ref.child('resourceData').child(v_id).get()
            self.logger.info("GET request received: geData")
            ret = {}
            if not result:
                return {}
            for key,value in result.items():
                # Get the current date and calculate the cutoff date
                now = datetime.datetime.now()
                cutoff_date = now - datetime.timedelta(days=int(days))
                ret[key]=[]

                # Iterate through the dates in the water_pump data
                for k, date_str in value.items():
                    # Parse the date string
                    try:
                        date_obj = datetime.datetime.strptime(date_str, "%d/%m/%Y-%H:%M")
                        # Check if the date is within the range
                        if cutoff_date <= date_obj <= now:
                            ret[key].append(date_str)
                    except ValueError:
                        self.logger.error(f"Invalid date format: {date_str}")

            return ret
        else:
            self.logger.error("GET request received: Invalid resource")
            return {"message": "Invalid resource"}

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self, *args, **kwargs):
        if args[0] == 'device':
            self.logger.info("POST request received: addDevice")
            device = cherrypy.request.json
            this_time = datetime.datetime.now()
            device["lastUpdate"] = this_time.strftime("%Y-%m-%d %H:%M:%S")
            device["device_status"] = "active"
            found = False
            result = self.firebase_ref.child('deviceList').order_by_child("device_id").equal_to(device['device_id']).get().values()
            if next(iter(result), None):
                found = True
            if not found:
                if self.firebase_ref.child('userList').order_by_child("user_id").equal_to(device["user_id"]).get():
                    print("User exist")
                    url = "https://api.thingspeak.com/channels.json"
                    data = {
                        'api_key': 'GHTRZQWCOGMCHXHE',
                        'name': device['device_id'],
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
                        self.logger.error("Error in creating channel")
                        raise cherrypy.HTTPError(response.status_code, "Error in creating channel")
                    else:
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
                        self.logger.info("Device added successfully")
                        return {"message": "Device added successfully"}
        elif args[0] == 'vase':
            self.logger.info("POST request received: addVase")
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
                self.logger.error(f"No devices found with the given device_id + {vase['device_id']}")
                return {"message": "No devices found with the given device_id"}
            self.firebase_ref.child('vaseList').push(vase)
            self.logger.info("Vase added successfully")
            return {"message": "Vase added successfully",
                    "id": this_id}
        elif args[0] == 'user':
            self.logger.info("POST request received: addUser")
            user = cherrypy.request.json
            uuid4 = uuid.uuid4()
            this_id = uuid4.int
            this_time = datetime.datetime.now()
            user["user_id"] = str(this_id)
            user["lastUpdate"] = this_time.strftime("%Y-%m-%d %H:%M:%S")
            self.firebase_ref.child('userList').push(user)
            self.logger.info("User added successfully")
            return {"message": "User added successfully",
                    "id": this_id}
        elif args[0] == 'postData':
            self.logger.info("POST request received: data")
            data = cherrypy.request.json
            if args[1] and args[2] and data[args[2]]:
                vase_id = str(args[1])
                self.firebase_ref.child("resourceData").child(vase_id).child(args[2]).push(data[args[2]])
                return {"message": "Data added successfully"}
            else:
                return{"message": "Invalid data format"}
        else:
            self.logger.error("Invalid resource")
            return {"message": "Invalid resource"}


    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def PUT(self, *args, **kwargs):
        if args[0].startswith('device'):
            self.logger.info("PUT request received: updateDevice")
            device_id = args[1]
            device = cherrypy.request.json
            if self.firebase_ref.child('deviceList').order_by_child("device_id").equal_to(device_id).set(device):
                self.logger.info("Device updated successfully")
                return {"message": "Device updated successfully"}
            else:
                self.logger.error("Device not found")
                return {"message": "Device not found"}
        elif args[0].startswith('vase'):
            self.logger.info("PUT request received: updateVase")
            vase_id = args[1]
            vase = cherrypy.request.json
            key_to_update = list(self.firebase_ref.child('vaseList').order_by_child("vase_id").equal_to(vase_id).get().keys())[0]
            if key_to_update:
                self.firebase_ref.child('vaseList').child(key_to_update).update(vase)
                self.logger.info("Vase updated successfully")
                return {"message": "Vase updated successfully"}
            else:
                self.logger.error("Vase not found")
                return {"message": "Vase not found"}
        elif args[0].startswith('user'):
            self.logger.info("PUT request received: updateUser")
            user_id = args[1]
            user = cherrypy.request.json
            if self.firebase_ref.child('userList').order_by_child("user_id").equal_to(user_id).set(user):
                self.logger.info("User updated successfully")
                return {"message": "User updated successfully"}
            else:
                self.logger.error("User not found")
                return {"message": "User not found"}
        else:
            self.logger.error("Invalid resource")
            return {"message": "Invalid resource"}

    def listDevice(self):
        return list(self.firebase_ref.child('deviceList').get().values())
    def listUser(self):
        return list(self.firebase_ref.child('userList').get().values())
    def listVase(self):
        return list(self.firebase_ref.child('vaseList').get().values())

if __name__ == '__main__':
    try:
        catalog = CatalogExpose()

        conf = {
        '/':{
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on' : True
        }
        }
        cherrypy.config.update({
            'server.socket_host': 'localhost',
            'server.socket_port': 5002  # Specify your desired port here
        })
        cherrypy.tree.mount(catalog, '/', conf)
        cherrypy.engine.start()
        cherrypy.engine.block()
    except Exception as e:
        print("ERROR OCCUREDD, DUMPING INFO...")
        path = os.path.abspath('/app/logs/ERROR_resourcecatalog.err')
        with open(path, 'a') as file:
            date = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
            file.write(f"Crashed at : {date}")
            file.write(f"Unexpected error: {e}")
        print("EXITING...")
        sys.exit(1) 