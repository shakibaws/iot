import json
import cherrypy
import requests
import time
import os

API_KEY = os.getenv("API_KEY")

service_name = "image_recognition"

if not API_KEY:
    #log_to_loki("info", "POST request received", service_name=service_name, user_id=user_id, request_id=request_id)
    raise ValueError("API_KEY is missing from environment variables")

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
        #log_to_loki("info", "POST request received", service_name=service_name, user_id=user_id, request_id=request_id)
        files = []
        if not  isinstance(params['images'], list):
            params['images']=[params['images']]

        if len(params['images']) == 0:
            #log_to_loki("error", "No images provided", service_name=service_name, service_name=service_name, user_id=user_id, request_id=request_id)
            raise cherrypy.HTTPError(400, 'No images provided')
                
        for image in params['images']:
            if not image.file:
                #log_to_loki("error", "No images provided", service_name=service_name, service_name=service_name, user_id=user_id, request_id=request_id)
                raise cherrypy.HTTPError(400, 'Immagine non fornita')

            # Read the image data from form-data
            image_data = image.file.read()
            files.append(('images', ("image.jpg", image_data)))
            print(len(files))

        # Ensure files list is not empty
        if not files:
            #log_to_loki("error", "Image not provided or invalid object", service_name=service_name, service_name=service_name, user_id=user_id, request_id=request_id)
            raise cherrypy.HTTPError(400, 'No images provided')

        req = requests.Request('POST', url=api_endpoint, files=files)
        prepared = req.prepare()

        s = requests.Session()
        response = s.send(prepared)
        #log_to_loki("info", f"Identification request sent", service_name=service_name, service_name=service_name, user_id=user_id, request_id=request_id)

        if response.status_code != 200:
            #log_to_loki("error", f"API request failed with response {response}", service_name=service_name, service_name=service_name, user_id=user_id, request_id=request_id)
            raise cherrypy.HTTPError(response.status_code, 'Error in API request')
        try:
            json_result = json.loads(response.text)
            if 'results' in json_result:
                ret ={
                    "result": {
                        "species": json_result['results'][0]['species']['scientificNameWithoutAuthor'],
                        "common_name": json_result['results'][0]['species']['commonNames'][0],
                        "confidence": json_result['results'][0]['score'],
                    },
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                #log_to_loki("info", f"Plant identified correctly", service_name=service_name, service_name=service_name, user_id=user_id, request_id=request_id)
                return json.dumps(ret)
            else:
                #log_to_loki("error", "failed to process Plantnet data", service_name=service_name, service_name=service_name, user_id=user_id, request_id=request_id)
                raise cherrypy.HTTPError(500, 'Invalid response from API')
        except json.JSONDecodeError:
            #log_to_loki("error", "Failed to parse JSON response", service_name=service_name, service_name=service_name, user_id=user_id, request_id=request_id)
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
        'server.socket_port': 8085  # Specify your desired port here
    })
    webService=API()
    cherrypy.tree.mount(webService, '/', conf)
    cherrypy.engine.start()
    cherrypy.engine.block()