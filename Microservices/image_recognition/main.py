import json
import cherrypy
import requests
import time
import os
import datetime
import CustomerLogger
import sys


from dotenv import load_dotenv
load_dotenv()


API_KEY = os.getenv("API_KEY")

service_name = "image_recognition"

if not API_KEY:
    raise ValueError("API_KEY is missing from environment variables")



PROJECT = "all" 
api_endpoint = f"https://my-api.plantnet.org/v2/identify/{PROJECT}?api-key={API_KEY}"


class API:
   
    exposed=True                        

    @cherrypy.tools.json_out()
    @cherrypy.tools.response_headers(headers=[('Access-Control-Allow-Origin', '*'),
                                                ('Access-Control-Allow-Methods', 'POST, OPTIONS, GET'),
                                                ('Access-Control-Allow-Headers', 'Content-Type')])     ###?????????

    def __init__(self):
        self.logger = CustomerLogger.CustomLogger("image_recognition")

    def GET(self):
        return 'GET successfully'
    
    def POST(self, **params):
        self.logger.info("POST request received")
        files = []                                         #Prepares an empty list to hold the images
        if not  isinstance(params['images'], list):
            params['images']=[params['images']]

        if len(params['images']) == 0:
            self.logger.error("No parameters provided")
            raise cherrypy.HTTPError(400, "No parameters provided")
                
        for image in params['images']:
            if not image.file:
                self.logger.error("No images provided")
                raise cherrypy.HTTPError(400, 'No images provided')

            # Read the image data from form-data
            image_data = image.file.read()
            files.append(('images', ("image.jpg", image_data)))

        # Ensure files list is not empty
        #If somehow no image got read correctly, throw an error.
        if not files:
            self.logger.error("The image provided is not readable")
            raise cherrypy.HTTPError(400, 'Impossible to decode the image')


     
        req = requests.Request('POST', url=api_endpoint, files=files)
        prepared = req.prepare()


        s = requests.Session()
        response = s.send(prepared)
        self.logger.info(f"API request sent to {api_endpoint}")

        if response.status_code != 200:
            self.logger.error(F"API request failed:\n {response}")
            raise cherrypy.HTTPError(response.status_code, 'Error in API request')
        try:
            json_result = json.loads(response.text)  
            if 'results' in json_result:
                ret ={
                    "result": {
                        "species": json_result['results'][0]['species']['scientificNameWithoutAuthor'],
                        "common_name": json_result['results'][0]['species']['commonNames'],
                        "confidence": json_result['results'][0]['score'],
                    },
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                self.logger.info("API request successful")
                return json.dumps(ret)
            else:
                self.logger.error("API failed: impossible to find 'results' in the response")
                raise cherrypy.HTTPError(400, "impossible to find 'results' in the response")
        except json.JSONDecodeError:
            self.logger.error("Invalid JSON response from API")
            raise cherrypy.HTTPError(400, 'Invalid JSON response from API')
    

    def OPTIONS(self, *args, **kwargs):  #Used for CORS preflight requests
        pass
    

if __name__ == '__main__':
    try:

        conf = {
            '/':{
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),  #Allows you to map HTTP methods like GET, POST, OPTIONS directly to class methods (GET(self), POST(self)).
                'tools.sessions.on' : True,
                'tools.response_headers.on': True,
            }
        }
        cherrypy.config.update({
        'server.socket_host': 'localhost',
            'server.socket_port': 5006  # Specify your desired port here
        })
        webService=API()
        cherrypy.tree.mount(webService, '/', conf)
        cherrypy.engine.start()
        cherrypy.engine.block()
    except Exception as e:
        print("ERROR OCCUREDD, DUMPING INFO...")
        path = os.path.abspath('./logs/ERROR_imagerecognition.err')
        with open(path, 'a') as file:
            date = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
            file.write(f"Crashed at : {date}")
            file.write(f"Unexpected error: {e}")
        print(e)
        print("EXITING...")
        sys.exit(1) 