import zukiPy
import asyncio
import json
import cherrypy
import requests
import time
import datetime

api_key ="zu-19f3b35168df0e7d15f07e6b4b69338b" #Get your API key from discord.gg/zukijourney
zukiAI = zukiPy.zukiCall(api_key)
image_recognition_service = "http://imagerecognition.duck.pictures"



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

        req = requests.Request('POST', url=image_recognition_service, files=files)
        prepared = req.prepare()

        s = requests.Session()
        response = s.send(prepared)
        if response.status_code != 200:
            raise cherrypy.HTTPError(response.status_code, 'Error in API request')
        try:
            json_result = json.loads(response.text)
            if 'result' in json_result:
                result=json_result['result']
                print(result)
                info = asyncio.run(self.call_get_info(result['species']))
                # Remove ```json and ``` from the string
                json_string = info.strip('```json').strip('```').strip()

                # Load the JSON data
                data = json.loads(json_string)
                return json.dumps(data)
            else:
                raise cherrypy.HTTPError(500, 'Invalid response from API')
        except json.JSONDecodeError:
            raise cherrypy.HTTPError(500, 'Invalid JSON response from API')
    

    async def call_get_info(self, name):
        chatresponse = await zukiAI.zuki_chat.sendMessage("S", f"Tell me ideal conditions(specify: ground/enviroment humidity, hours of exposition to sun, temperature) of this plant {name}. Respond in 50 words. Structure the answer as a json with soilHumidityMin:number, soilHumidityMax:number, hourOfSunMin:number, temperatureMin:number, temperatureMax:number, description:text(generalComprehensiveDescription in 40 words)")
        print("Chat Response:", chatresponse)
        return chatresponse
    

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
        'server.socket_port': 8081  # Specify your desired port here
    })
    webService=API()
    cherrypy.tree.mount(webService, '/', conf)
    cherrypy.engine.start()
    cherrypy.engine.block()
 
