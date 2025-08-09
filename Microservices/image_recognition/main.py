import json
import cherrypy
import requests
import time
import os
import datetime
import CustomerLogger
import sys


#Loads environment variables from a .env file into Python's environment.
from dotenv import load_dotenv
load_dotenv()

#It reads an environment variable—in this case, "API_KEY"—and returns its value
#API_KEY = "abc123" -> You’re telling the server:
#“Hi, I’m allowed to use this service — here’s my key: abc123.”

#An API key is like a password or membership card that allows you to access a web service (like the PlantNet API).

#It identifies you or your app

#It allows you to use the API service

#It helps track how many requests you make

#It prevents unauthorized users from using the API


API_KEY = "2b10lTgEgZpldkgnQzUJdIjcb"

service_name = "image_recognition"

if not API_KEY:
    #log_to_loki("info", "POST request received", service_name=service_name, user_id=user_id, request_id=request_id)
    raise ValueError("API_KEY is missing from environment variables")



#What is PROJECT?
#The API supports different databases of plants based on region.
#"all" = global database (more general)
#"weurope" = Western Europe plants only
#"canada" = Canadian plants only

PROJECT = "all" # try "weurope" or "canada"
api_endpoint = f"https://my-api.plantnet.org/v2/identify/{PROJECT}?api-key={API_KEY}"


class API:
    #this class can be accessed via HTTP
    #This class handles incoming requests.
    #exposed = True:
    #In CherryPy this class should be available via the web.
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


        #PlantNet gets a request like:
        #POST https://my-api.plantnet.org/v2/identify/all?api-key=abc123
        #with image file: leaf.jpg
        req = requests.Request('POST', url=api_endpoint, files=files)
        prepared = req.prepare()


        #A reusable connection object for making multiple HTTP requests
        s = requests.Session()
        response = s.send(prepared)
        self.logger.info(f"API request sent to {api_endpoint}")

        if response.status_code != 200:
            self.logger.error(F"API request failed:\n {response}")
            raise cherrypy.HTTPError(response.status_code, 'Error in API request')
        try:
            json_result = json.loads(response.text)  #Converts the response text (which is in JSON format) into a Python dictionary.
            if 'results' in json_result:
                
                #creates a dictionary (ret) that stores the plant recognition result from the API response
                ret ={
                    "result": {
                        "species": json_result['results'][0]['species']['scientificNameWithoutAuthor'],
                        "common_name": json_result['results'][0]['species']['commonNames'][0],
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
        # path = os.path.abspath('/app/logs/ERROR_imagerecognition.err')
        # with open(path, 'a') as file:
        #     date = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
        #     file.write(f"Crashed at : {date}")
        #     file.write(f"Unexpected error: {e}")
        print(e)
        print("EXITING...")
        sys.exit(1) 