import cherrypy
import google.generativeai as genai
import os
import CustomerLogger
import os
from dotenv import load_dotenv
import os
import sys
import datetime

class Gemini_service:
    exposed = True
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"response_mime_type": "application/json"})
        self.logger = CustomerLogger.CustomLogger("gemini_service")

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
                self.logger.error("Error in sending data to gemini")
                return {"message": "Error in sending data to gemini"}
        else:
            self.logger.error("POST request received: Invalid resource")
            return {"message": "Invalid resource"}

if __name__ == '__main__':
    try:
        load_dotenv()

        API_KEY = os.getenv("API_KEY")


        if not API_KEY:
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
            'server.socket_port': 5007  # Specify your desired port here
        })
        cherrypy.tree.mount(gemini, '/', conf)
        cherrypy.engine.start()
        cherrypy.engine.block()
    except Exception as e:
        print("ERROR OCCUREDD, DUMPING INFO...")
        path = os.path.abspath('./logs/ERROR_gemini.err')
        with open(path, 'a') as file:
            date = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
            file.write(f"Crashed at : {date}")
            file.write(f"Unexpected error: {e}")
        print(e)
        print("EXITING...")
        sys.exit(1) 

    