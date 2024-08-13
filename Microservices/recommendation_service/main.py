import zukiPy
import asyncio
import json
import cherrypy
import requests
import time
import datetime

api_key ="zu-b85d7fe154596ae3eb84ee8177e492f6" #Get your API key from discord.gg/zukijourney
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
        if not isinstance(params['images'], list):
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
            print(response.text)
            raise cherrypy.HTTPError(response.status_code, 'Error in API request')
        try:
            json_result = json.loads(response.text)
            if 'result' in json_result:
                result=json_result['result']
                # info = asyncio.run(self.call_get_info(result['species']))

                req = {}
                req['question'] = f"Tell me ideal conditions of the plant {result['species']}. 
                    Using this JSON schema: Plant =" + " { 'plant_name':str, 'soil_moisture_min':num, 'soil_moisture_max':num, 'hours_sun_suggested':num, 'temperature_min':num, 'temperature_max':num, 'description':str(max 40 words)}."

                print("Sending request")
                #req['question'] = f"Tell me ideal conditions(specify: ground/enviroment humidity, hours of exposition to sun, temperature) of this plant {result['species']}. Answer everything in a json object. Structure the answer as a json object with the following field(use the same name) -->  plant_name:string, soil_moisture_min:number, soil_moisture_max:number, hours_sun_suggested:number, temperature_min:number, temperature_max:number, description:text(general comprehensive description in 40 words. Example of answer format: " + example_res
                response = requests.post('http://chat.duck.pictures/chat',  json=req)
                print(f"Response = {response.text}")
                # Step 1: Remove the surrounding double quotes
                #response_text = response.text.strip('"')

                # Step 2: Remove the ```json\n at the beginning and \n``` at the end
                #response_text = response_text.strip('```json\\n').rstrip('\\n```')

                # Step 3: Convert the cleaned string to a Python dictionary
                #response_dict = json.loads(response_text)
                #print(response_dict)
                #response_text = response_text.strip()
                #json.loads(response_text)

                # Load the JSON data
                # data = json.loads(content)
                return response.json()
            else:
                raise cherrypy.HTTPError(500, 'Invalid response from API')
        except json.JSONDecodeError:
            raise cherrypy.HTTPError(500, 'Invalid JSON response from API')
    

    async def call_get_info(self, name):
        chatresponse = await zukiAI.zuki_chat.sendMessage("S", f"Tell me ideal conditions(specify: ground/enviroment humidity, hours of exposition to sun, temperature) of this plant {name}. Respond in 50 words. Structure the answer as a json with plant_name:string, soil_moisture_min:number, soil_moisture_max:number, hours_sun_suggested:number, temperature_min:number, temperature_max:number, description:text(generalComprehensiveDescription in 40 words)")
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
 
