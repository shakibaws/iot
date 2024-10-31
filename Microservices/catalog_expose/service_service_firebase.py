import cherrypy
import json
import datetime
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

class ServiceCatalogExpose:
    exposed = True

    def __init__(self, url):
        cred = credentials.Certificate("firebase_key.json")
        firebase_admin.initialize_app(cred, {
            'databaseURL': url 
        })
        self.firebase_ref = db.reference('service_catalog/')

    @cherrypy.tools.json_out()
    def GET(self, *args, **kwargs):
        if args:
            key = args[0].lower()
            if key == 'all':
                return self.firebase_ref.get()
            else:
                try:
                    return self.firebase_ref.child(key).get()
                except Exception as e:
                    print(e)
        else:
            return self.firebase_ref.get()


if __name__ == '__main__':
    serviceCatalog = ServiceCatalogExpose('https://smartvase-effeb-default-rtdb.europe-west1.firebasedatabase.app')
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True
        }
    }
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 8082  # Specify your desired port here
    })
    cherrypy.tree.mount(serviceCatalog, '/', conf)
    cherrypy.engine.start()
    cherrypy.engine.block()
