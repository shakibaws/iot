import cherrypy
import requests
import json
import base64
import aiohttp
import asyncio
import io
from CustomerLogger import CustomLogger  

class PlantHealthAssistant:
    exposed = True

    def __init__(self, gemini_endpoint):
        # Initialize the logger with a service name and optional user ID
        # self.logger = CustomLogger(service_name="plant_health_assistant", user_id="system")
        self.gemini_endpoint = gemini_endpoint

    def POST(self, **params):
        try:
            # self.logger.info("POST request received")
            print("POST request received")

            # Get the uploaded file from the request
            # Try to access the file from CherryPy's parsed parameters
            uploaded_file = None
            
            # Check if CherryPy has already parsed the multipart data
            if hasattr(cherrypy.request, 'params') and 'images' in cherrypy.request.params:
                uploaded_file = cherrypy.request.params['images']
                print("Found file in cherrypy.request.params")
            elif hasattr(cherrypy.request, 'body_params') and 'images' in cherrypy.request.body_params:
                uploaded_file = cherrypy.request.body_params['images']
                print("Found file in cherrypy.request.body_params")
            else:
                # Try to access the raw body if it hasn't been consumed
                try:
                    raw_body = cherrypy.request.body.read()
                    if raw_body:
                        uploaded_file = io.BytesIO(raw_body)
                        print("Using raw body")
                    else:
                        print("Raw body is empty")
                except:
                    print("Could not read raw body")
            
            if not uploaded_file:
            
                raise cherrypy.HTTPError(400, "No image file provided")

            
            # self.logger.info("Sending uploaded image to Plant.id")
            print("Sending uploaded image to Plant.id")
            disease_info = self.detect_disease_from_file(uploaded_file)
            print(f"Disease info: {disease_info}")

            if disease_info.get('suggestions') and len(disease_info['suggestions']) > 0:
                gemini_response = asyncio.run(self.get_gemini_advice(disease_info['suggestions']))
                disease_info['gemini_advice'] = gemini_response
            else:
                disease_info['gemini_advice'] = "Your plant appears to be healthy! No specific treatment recommendations needed at this time."

            response_json = json.dumps(disease_info)
            print(f"Returning response: {response_json}")
            return response_json

        except Exception as e:
            print(f"Error in PlantHealthAssistant: {str(e)}")
            import traceback
            traceback.print_exc()
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

            async with aiohttp.ClientSession() as session:
                async with session.post(self.gemini_endpoint, json=req) as response:
                    if response.status == 200:
                        print("Gemini response received")
                        print(response)
                        result = await response.json()
                        advice = json.loads(result)['advice']

                        print(f"Gemini advice: {advice}")
                        return advice
                    else:
                        print(f"Gemini service returned status {response.status}")
                        return "Unable to generate advice at this time. Please consult a plant expert."
                        
        except Exception as e:
            print(f"Error calling Gemini service: {str(e)}")
            return "Unable to generate advice at this time. Please consult a plant expert."

    def detect_disease_from_file(self, uploaded_file):
        api_key = "49Yahtr6e4QC9JlQTA3kJurIIM3WtFbIcMFnVdvDkls3f3dOmE"
        
        image_data = None
        
        if hasattr(uploaded_file, 'file') and uploaded_file.file:
            uploaded_file.file.seek(0)
            image_data = uploaded_file.file.read()
        
      
        if not image_data:
            raise ValueError("No image data received")
            
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        print(f"Base64 length: {len(image_base64)}")
        
        response = requests.post(
            "https://api.plant.id/v3/health_assessment",
            headers={"Content-Type": "application/json",'Api-Key': api_key},
            json={
                "images": [f"data:image/jpeg;base64,{image_base64}"],
            }
        )
      
        result = response.json()
        
        # Extract only is_healthy status and suggestions list
        result_data = result.get("result", {})
        is_healthy = result_data.get("is_healthy", {}).get("binary", True)
        suggestions = result_data.get("disease", {}).get("suggestions", [])
        if is_healthy:
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
        
        return {
            "is_healthy": is_healthy,
            "suggestions": formatted_suggestions
        }

   

if __name__ == "__main__":
    res = requests.get("http://localhost:5001/all").json()
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
        'server.socket_host': 'localhost',
        'server.socket_port': 5009
    })

    cherrypy.tree.mount(PlantHealthAssistant(gemini), '/', config)
    cherrypy.engine.start()
    cherrypy.engine.block()
