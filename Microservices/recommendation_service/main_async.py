import asyncio
import json
import cherrypy
import aiohttp
import time
import datetime
import CustomerLogger

image_recognition_service = "http://imagerecognition.duck.pictures"


class API:
    exposed=True
    @cherrypy.tools.json_out()
    @cherrypy.tools.response_headers(headers=[('Access-Control-Allow-Origin', '*'),
                                                ('Access-Control-Allow-Methods', 'POST, OPTIONS, GET'),
                                                ('Access-Control-Allow-Headers', 'Content-Type')])
    def __init__(self):
        self.logger = CustomerLogger.CustomLogger("recommendation_service", "user_id_test")

    def GET(self):
        return 'GET successfully'
    
    async def process_images(self, images):
        form_data = aiohttp.FormData()
        for image in images:
            if not image.file:
                self.logger.error("No images provided")
                raise cherrypy.HTTPError(400, 'Immagine non fornita')
            image_data = image.file.read()
            form_data.add_field('images', image_data, filename="image.jpg", content_type='image/jpeg')

        # Effettua la richiesta POST asincrona
        async with aiohttp.ClientSession() as session:
            async with session.post(image_recognition_service, data=form_data) as response:
                if response.status != 200:
                    self.logger.error("No images provided")
                    raise cherrypy.HTTPError(response.status, 'Error in the API request')
                
                json_result = json.loads(await response.text())
                
                if 'result' in json_result:
                    result = json_result['result']
                    
                    req = {
                        'question': (
                            f"Tell me ideal conditions of the plant {result['species']}. "
                            "Using this JSON schema: Plant = "
                            "{ 'plant_name':string, 'soil_moisture_min':double_digits_integer, 'soil_moisture_max':double_digits_integer, 'hours_sun_suggested':single_digit_integer, "
                            "'temperature_min':double_digits_integer(in Celsius), 'temperature_max':double_digits_integer(in Celsius), 'description':string(max 40 words)}."
                        )
                    }

                    # Richiesta al servizio di chat
                    async with session.post('http://chat.duck.pictures/chat', json=req) as chat_response:
                        self.logger.info("API failed: impossible to find 'result' in the recognition service repsonse")                        chat_result = await chat_response.json()
                        return chat_result
                else:
                    self.logger.error("API failed: impossible to find 'result' in the recognition service repsonse")
                    raise cherrypy.HTTPError(500, 'Invalid API response')

    def POST(self, **params):
        self.logger.info("POST request received")
        
        if not isinstance(params['images'], list):
            params['images'] = [params['images']]

        if len(params['images']) == 0:
            self.logger.error("No images provided")
            raise cherrypy.HTTPError(400, 'No images provided')

        # Esegui il codice asincrono
        result = asyncio.run(self.process_images(params['images']))
        return result

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
        'server.socket_port': 8081  # Specifica la porta desiderata
    })
    webService = API()
    cherrypy.tree.mount(webService, '/', conf)
    cherrypy.engine.start()
    cherrypy.engine.block()
