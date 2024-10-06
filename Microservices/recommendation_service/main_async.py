import asyncio
import json
import cherrypy
import aiohttp
import time
import datetime

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
    
    async def process_images(self, images):
        files = []
        for image in images:
            if not image.file:
                raise cherrypy.HTTPError(400, 'Immagine non fornita')
            image_data = image.file.read()
            files.append(('images', ("image.jpg", image_data)))

        # Assicurati di avere almeno un file da inviare
        if not files:
            raise cherrypy.HTTPError(400, 'No images provided')

        # Effettua la richiesta POST asincrona
        async with aiohttp.ClientSession() as session:
            async with session.post(image_recognition_service, data=files) as response:
                if response.status != 200:
                    raise cherrypy.HTTPError(response.status, 'Errore nella richiesta API')
                json_result = await response.json()
                
                if 'result' in json_result:
                    result = json_result['result']
                    
                    req = {
                        'question': (
                            f"Tell me ideal conditions of the plant {result['species']}. "
                            "Using this JSON schema: Plant = "
                            "{ 'plant_name':str, 'soil_moisture_min':num, 'soil_moisture_max':num, 'hours_sun_suggested':num, "
                            "'temperature_min':num, 'temperature_max':num, 'description':str(max 40 words)}."
                        )
                    }

                    # Richiesta al servizio di chat
                    async with session.post('http://chat.duck.pictures/chat', json=req) as chat_response:
                        chat_result = await chat_response.json()
                        return chat_result
                else:
                    raise cherrypy.HTTPError(500, 'Risposta non valida dalla API')

    def POST(self, **params):
        # Esegui l'operazione asincrona
        if not isinstance(params['images'], list):
            params['images'] = [params['images']]

        if len(params['images']) == 0:
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
