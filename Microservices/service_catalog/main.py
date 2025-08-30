import cherrypy
import json
import datetime
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import CustomerLogger
import os
import sys

class ServiceCatalogExpose:
    exposed = True

    def __init__(self, url):
        cred = credentials.Certificate("firebase_key.json")
        firebase_admin.initialize_app(cred, {
            'databaseURL': url 
        })
        self.firebase_ref = db.reference('service_catalog/')
        self.logger = CustomerLogger.CustomLogger("service_catalog")

    @cherrypy.tools.json_out()
    def GET(self, *args, **kwargs):
        if args:
            key = args[0].lower()
            if key == 'all':
                self.logger.info("GET request received - all")
                return self.firebase_ref.get()
            elif key == 'mqtt':
                return self.firebase_ref.child('mqtt_broker').child('broker_address').get()
            else:
                try:
                    self.logger.info(f"GET request received - {key}")
                    return self.firebase_ref.child(key).get()
                except Exception as e:
                    self.logger.error(f"GET request received - {key} - {e}")
                    print(e)
        else:
            self.logger.error("GET request received: Invalid resource")
            return self.firebase_ref.get()
        
    @cherrypy.tools.json_out()
    def POST(self, *args, **kwargs):
        if args[0]:
            if args[0] == 'publicip':
                new_address = cherrypy.request.body.read()
                print("New address")
                print(new_address)
                new_address = json.loads(new_address)
                self.firebase_ref.child('mqtt_broker').update({"broker_address": new_address['publicip']})
                return "Success"
        return "Wrong url"

if __name__ == '__main__':
    try:
        serviceCatalog = ServiceCatalogExpose('https://iotvase-default-rtdb.europe-west1.firebasedatabase.app')
        conf = {
            '/': {
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                'tools.sessions.on': True
            }
        }
        cherrypy.config.update({
            'server.socket_host': '0.0.0.0',
            'server.socket_port': 5001
        })
        cherrypy.tree.mount(serviceCatalog, '/', conf)
        cherrypy.engine.start()
        cherrypy.engine.block()
    except Exception as e:
        print("ERROR OCCUREDD, DUMPING INFO...")
        path = os.path.abspath('./logs/ERROR_servicecatalog.err')
        with open(path, 'a') as file:
            date = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
            file.write(f"Crashed at : {date}")
            file.write(f"Unexpected error: {e}")
        print(e)
        print("EXITING...")
        sys.exit(1) 