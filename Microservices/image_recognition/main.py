import json
import cherrypy
import requests
import time
import datetime

API_KEY = "2b10YWTxsXkQEIEACOiGUATOwu"  # Set you API_KEY here
PROJECT = "all" # try "weurope" or "canada"
api_endpoint = f"https://my-api.plantnet.org/v2/identify/{PROJECT}?api-key={API_KEY}"

class API:
    exposed=True
    @cherrypy.tools.json_out()
    @cherrypy.tools.response_headers(headers=[('Access-Control-Allow-Origin', '*'),
                                                ('Access-Control-Allow-Methods', 'POST, OPTIONS, GET'),
                                                ('Access-Control-Allow-Headers', 'Content-Type')])
    def __init__(self):
        pass
    def GET(self):
        return 'GET successfully'
    
    def POST(self, **params):
        print('POST')
        files = []
        if not  isinstance(params['images'], list):
            params['images']=[params['images']]

        print(params['images'])

        if len(params['images']) == 0:
            raise cherrypy.HTTPError(400, 'No images provided')
                
        for image in params['images']:
            if not image.file:
                print('error here')
                raise cherrypy.HTTPError(400, 'Immagine non fornita')

            # Read the image data from form-data
            image_data = image.file.read()
            files.append(('images', ("image.jpg", image_data)))
            print(len(files))

        # Ensure files list is not empty
        if not files:
            raise cherrypy.HTTPError(400, 'No images provided')

        req = requests.Request('POST', url=api_endpoint, files=files)
        prepared = req.prepare()

        s = requests.Session()
        response = s.send(prepared)
        if response.status_code != 200:
            raise cherrypy.HTTPError(response.status_code, 'Error in API request')
        try:
            json_result = json.loads(response.text)
            if 'results' in json_result:
                return json.dumps(json_result['results'][0])
            else:
                raise cherrypy.HTTPError(500, 'Invalid response from API')
        except json.JSONDecodeError:
            raise cherrypy.HTTPError(500, 'Invalid JSON response from API')
    

    def OPTIONS(self, *args, **kwargs):
        pass
    

if __name__ == '__main__':
    
    conf = {
        '/':{
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on' : True,
            'tools.response_headers.on': True,
        }
    }
    cherrypy.config.update({
       'server.socket_host': '0.0.0.0',
        'server.socket_port': 8080  # Specify your desired port here
    })
    webService=API()
    cherrypy.tree.mount(webService, '/', conf)
    cherrypy.engine.start()
    cherrypy.engine.block()