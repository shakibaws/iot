import cherrypy
import google.generativeai as genai
import os
import CustomerLogger
import os
from dotenv import load_dotenv

class Gemini_service:
    exposed = True
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
        self.logger = CustomerLogger.CustomLogger("gemini_service", "user_id_test")

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self, *args, **kwargs):
        #print(args[0])
        self.logger.info("POST request received")
        if args[0] and args[0] == 'chat':
            print("asking")
            question = cherrypy.request.json['question']
            response = self.model.generate_content(question)
            if response.text:
                self.logger.info("POST request send to gemini")
                return response.text
            else:
                self.logger.error(f"Error in sending data to gemini: {response.status_code}")
                return {"message": "Error in sending data to gemini"}
        else:
            self.logger.error("POST request received: Invalid resource")
            return {"message": "Invalid resource"}

if __name__ == '__main__':
    load_dotenv()

    API_KEY = os.getenv("API_KEY")

    service_name = "image_recognition"

    if not API_KEY:
        #log_to_loki("info", "POST request received", service_name=service_name, user_id=user_id, request_id=request_id)
        raise ValueError("API_KEY is missing from environment variables")
    
    gemini = Gemini_service(API_KEY)

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
    cherrypy.tree.mount(gemini, '/', conf)
    cherrypy.engine.start()
    cherrypy.engine.block()