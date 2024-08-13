import cherrypy
import google.generativeai as genai
import os

class Ollama_service:
    exposed = True
    def __init__(self):
        genai.configure(api_key="AIzaSyCmorRbRVa7whMTl7utEyQwo0xCXYWfXlo")
        self.model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})


    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self, *args, **kwargs):
        print(args[0])
        if args[0] and args[0] == 'chat':
            print("asking")
            question = cherrypy.request.json['question']
            response = self.model.generate_content(question)
            print(response.text)
            return response.text

if __name__ == '__main__':

    conf = {
        '/':{
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on' : True
        }
        }
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 5151  # Specify your desired port here
    })
    cherrypy.tree.mount(Ollama_service(), '/', conf)
    cherrypy.engine.start()
    cherrypy.engine.block()