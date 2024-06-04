import cherrypy
import json
import datetime

class ServiceCatalogExpose:
    exposed = True
    def __init__(self, data):
        self.serviceCatalog = data
        
    @cherrypy.tools.json_out()
    def GET(self, *args, **kwargs):
        if args:
            if(args[0] == 'topics'):
                return self.serviceCatalog.topics
            elif(args[0] == 'services'):
                return self.serviceCatalog.services
            elif(args[0] == 'broker'):
                return self.serviceCatalog.broker
            elif(args[0] == 'all'):
                return self.serviceCatalog
        

if __name__ == '__main__':
    with open('./service_catalog.json', 'r') as file:
        data = json.load(file)
        serviceCatalog = ServiceCatalogExpose(data)
        conf = {
        '/':{
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on' : True
        }
        }
        cherrypy.config.update({
            'server.socket_host': '0.0.0.0',
            'server.socket_port': 8082  # Specify your desired port here
        })
        cherrypy.tree.mount(serviceCatalog, '/', conf)
        cherrypy.engine.start()
        cherrypy.engine.block()
