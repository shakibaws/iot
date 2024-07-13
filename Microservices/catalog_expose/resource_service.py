import cherrypy
import json
import datetime

class CatalogExpose:
    exposed = True
    def __init__(self, data):
        self.deviceList = data['deviceList']
        self.vaseList = data['vaseList']
        self.userList = data['userList']

    def save_to_file(self):
        with open('Microservices/catalog_expose/resource_catalog.json', 'w') as file:
            json.dump({"deviceList": self.deviceList, "vaseList": self.vaseList, "userList": self.userList}, file)


    @cherrypy.tools.json_out()
    def GET(self, *args, **kwargs):
        print(args)
        if args[0] == 'listDevice':
            return self.deviceList
        elif args[0] == 'listVase':
            return self.vaseList
        elif args[0] == 'listUser':
            return self.userList
        elif args[0].startswith('device'):
            for device in self.deviceList:
                if device["device_id"] == args[1]:
                    return device
            return {}
        elif args[0].startswith('vase'):
            for vase in self.vaseList:
                if vase["vase_id"] == args[1]:
                    return vase
            return {}
        elif args[0].startswith('user'):
            for user in self.userList:
                if user["user_id"] == args[1]:
                    return user
            return {}
        else:
            return {"message": "Invalid resource"}

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self, *args, **kwargs):
        if args[0] == 'device':
            device = cherrypy.request.json
            this_time = datetime.datetime.now()
            device["lastUpdate"] = this_time.strftime("%Y-%m-%d %H:%M:%S")
            device["device_status"] = "active"
            found = False
            for i in self.deviceList:
                if i["device_id"] == device["device_id"]:
                    found = True
            if not found:
                for v in self.vaseList:
                    if v["temporary_code"] == device["activation_code"]:
                        device["vase_id"] = v["vase_id"]
                self.deviceList.append(device)
            self.save_to_file()
            return {"message": "Device added successfully"}
        elif args[0] == 'vase':
            vase = cherrypy.request.json
            this_id = int(self.vaseList[-1]["vase_id"]) + 1
            this_time = datetime.datetime.now()
            vase["vase_id"] = str(this_id)
            vase["lastUpdate"] = this_time.strftime("%Y-%m-%d %H:%M:%S")
            self.vaseList.append(vase)
            self.save_to_file()
            return {"message": "Vase added successfully",
                    "id": this_id}
        elif args[0] == 'user':
            user = cherrypy.request.json
            this_id = int(self.userList[-1]["user_id"]) + 1
            this_time = datetime.datetime.now()
            user["user_id"] = str(this_id)
            user["lastUpdate"] = this_time.strftime("%Y-%m-%d %H:%M:%S")
            self.userList.append(user)
            self.save_to_file()
            return {"message": "User added successfully",
                    "id": this_id}
        else:
            return {"message": "Invalid resource"}


    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def PUT(self, *args, **kwargs):
        if args[0].startswith('device'):
            device_id = args[1]
            device = cherrypy.request.json
            for i, d in enumerate(self.deviceList):
                if d["device_id"] == device_id:
                    self.deviceList[i] = device
                    self.save_to_file()
                    return {"message": "Device updated successfully"}
            return {"message": "Device not found"}
        elif args[0].startswith('vase'):
            vase_id = args[1]
            vase = cherrypy.request.json
            for i, v in enumerate(self.vaseList):
                if v["vase_id"] == vase_id:
                    self.vaseList[i] = vase
                    self.save_to_file()
                    return {"message": "Vase updated successfully"}
            return {"message": "Vase not found"}
        elif args[0].startswith('user'):
            user_id = args[1]
            user = cherrypy.request.json
            for i, v in enumerate(self.userList):
                if v["user_id"] == user_id:
                    self.userList[i] = user
                    self.save_to_file()
                    return {"message": "User updated successfully"}
            return {"message": "User not found"}
        else:
            return {"message": "Invalid resource"}

if __name__ == '__main__':
    with open('Microservices/catalog_expose/resource_catalog.json', 'r') as file:
        data = json.load(file)
        catalog = CatalogExpose(data)

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
