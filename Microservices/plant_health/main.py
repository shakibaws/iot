import cherrypy
import requests
import json
import base64
import aiohttp
import asyncio
import io
from CustomerLogger import CustomLogger  
import os
import sys
import datetime
from dotenv import load_dotenv

class PlantHealthAssistant:
    exposed = True

    def __init__(self, gemini_endpoint):
        # Load environment variables from .env file
        load_dotenv()
        
        # Initialize the logger with a service name and optional user ID
        self.logger = CustomLogger(service_name="plant_health_assistant", user_id="system")
        self.gemini_endpoint = gemini_endpoint
        self.logger.info("PlantHealthAssistant initialized")

    def POST(self, **params):
        try:
            self.logger.info("POST request received")

            # Get the uploaded file from the request
            # Try to access the file from CherryPy's parsed parameters
            uploaded_file = None
            
            # Check if CherryPy has already parsed the multipart data
            if hasattr(cherrypy.request, 'params') and 'images' in cherrypy.request.params:
                uploaded_file = cherrypy.request.params['images']
                self.logger.info("Found image in cherrypy.request.params")
          
            if not uploaded_file:
                self.logger.error("No image file provided")
                raise cherrypy.HTTPError(400, "No image file provided")

            
            self.logger.info("Sending uploaded image to Plant.id")
            disease_info = self.detect_disease_from_file(uploaded_file)
            self.logger.info(f"Disease info: {disease_info}")

            if disease_info.get('suggestions') and len(disease_info['suggestions']) > 0:
                self.logger.info("Getting Gemini advice for disease suggestions")
                gemini_response = asyncio.run(self.get_gemini_advice(disease_info['suggestions']))
                disease_info['gemini_advice'] = gemini_response
            else:
                self.logger.info("Plant appears healthy, no treatment recommendations needed")
                disease_info['gemini_advice'] = "Your plant appears to be healthy! No specific treatment recommendations needed at this time."

            response_json = json.dumps(disease_info)
            self.logger.info(f"Returning response: {response_json}")
            return response_json

        except Exception as e:
            self.logger.error(f"Error in PlantHealthAssistant: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise cherrypy.HTTPError(500, "Internal Server Error")

    async def get_gemini_advice(self, suggestions):
        try:
            suggestions_text = ""
            for i, suggestion in enumerate(suggestions, 1):
                name = suggestion.get('name', 'Unknown')
                probability = suggestion.get('probability', 0)
                suggestions_text += f"{name} (Probability: {probability:.2%})\n"
            
            question = f"Based on the following plant health assessment suggestions, provide a clear, simple explanation and treatment recommendations: {suggestions_text}" +"Respond in json format only like this:{advice:string}"

            req = {
                'question': question
            }

            self.logger.info("Calling Gemini service for advice")
            async with aiohttp.ClientSession() as session:
                async with session.post(self.gemini_endpoint, json=req) as response:
                    if response.status == 200:
                        self.logger.info("Gemini response received successfully")
                        result = await response.json()
                        advice = json.loads(result)['advice']

                        self.logger.info(f"Gemini advice: {advice}")
                        return advice
                    else:
                        self.logger.error(f"Gemini service returned status {response.status}")
                        return "Unable to generate advice at this time. Please consult a plant expert."
                        
        except Exception as e:
            self.logger.error(f"Error calling Gemini service: {str(e)}")
            return "Unable to generate advice at this time. Please consult a plant expert."

    def detect_disease_from_file(self, uploaded_file):
        try:
            api_key = os.getenv("PLANT_ID_API_KEY")
            if not api_key:
                raise ValueError("PLANT_ID_API_KEY environment variable not found")
            
            image_data = None
            
            if hasattr(uploaded_file, 'file') and uploaded_file.file:
                uploaded_file.file.seek(0)
                image_data = uploaded_file.file.read()
            
          
            if not image_data:
                self.logger.error("No image data received")
                raise ValueError("No image data received")
                
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            self.logger.info(f"Base64 length: {len(image_base64)}")
            
            self.logger.info("Making request to Plant.id API")
            response = requests.post(
                "https://api.plant.id/v3/health_assessment",
                headers={"Content-Type": "application/json",'Api-Key': api_key},
                json={
                    "images": [f"data:image/jpeg;base64,{image_base64}"],
                }
            )
          
            result = response.json()
            self.logger.info("Plant.id API response received")
            
            # Extract only is_healthy status and suggestions list
            result_data = result.get("result", {})
            is_healthy = result_data.get("is_healthy", {}).get("binary", True)
            suggestions = result_data.get("disease", {}).get("suggestions", [])
            
            if is_healthy:
                self.logger.info("Plant is healthy")
                return {
                    "is_healthy": is_healthy,
                    "suggestions": []
                }        
            
            formatted_suggestions = []
            for suggestion in suggestions:
                formatted_suggestions.append({
                    "name": suggestion.get("name", "Unknown"),
                    "probability": suggestion.get("probability", 0)
                })
            
            self.logger.info(f"Found {len(formatted_suggestions)} disease suggestions")
            return {
                "is_healthy": is_healthy,
                "suggestions": formatted_suggestions
            }
        except Exception as e:
            self.logger.error(f"Error in detect_disease_from_file: {str(e)}")
            raise

   

if __name__ == "__main__":
    try:
        res = requests.get("http://service_catalog:5001/all").json()
        gemini = res['services']['gemini']+'/chat'
        

        config = {
            '/': {
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                'tools.sessions.on': True,
                'tools.response_headers.on': True,
                'request.max_body_size': 10 * 1024 * 1024  # 10MB max file size
            }
        }

        cherrypy.config.update({
            'server.socket_host': '0.0.0.0',
            'server.socket_port': 5009
        })

        cherrypy.tree.mount(PlantHealthAssistant(gemini), '/', config)
        cherrypy.engine.start()
        cherrypy.engine.block()
    except Exception as e:
        print("ERROR OCCUREDD, DUMPING INFO...")
        path = os.path.abspath('./logs/ERROR_servicecatalog.err')
        with open(path, 'a') as file:
            date = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
            file.write(f"Crashed at : {date}")
            file.write(f"Unexpected error: {e}")
        print(e)
        print("EXITING...")
        sys.exit(1) 
        
