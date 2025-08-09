import cherrypy
import requests
import os
import json
from CustomerLogger import CustomLogger  

class PlantHealthAssistant:
    exposed = True

    def __init__(self):
        # Initialize the logger with a service name and optional user ID
        self.logger = CustomLogger(service_name="plant_health_assistant", user_id="system")

    def POST(self, **params):
        try:
            self.logger.info("POST request received")

            # Expecting a JSON with image_url
            request_body = cherrypy.request.body.read()
            data = json.loads(request_body)
            image_url = data.get("image_url")

            if not image_url:
                self.logger.error("Missing image URL in request")
                raise cherrypy.HTTPError(400, "Missing image URL")

            # Step 1: Send image to Plant.id API
            self.logger.info(f"Sending image to Plant.id: {image_url}")
            disease_info = self.detect_disease(image_url)

            # Step 2: Ask Gemini for a personalized care tip
            self.logger.info(f"Received disease info: {disease_info}")
            care_tip = self.ask_gemini(disease_info)
            self.logger.info("Generated care tip from Gemini")

            return json.dumps({
                "diagnosis": disease_info,
                "care_tip": care_tip
            })

        except Exception as e:
            self.logger.error(f"Error in PlantHealthAssistant: {str(e)}")
            raise cherrypy.HTTPError(500, "Internal Server Error")

    def detect_disease(self, image_url):
        api_key = os.getenv("PLANT_ID_API_KEY")
        response = requests.post(
            "https://api.plant.id/v2/health_assessment",
            headers={"Content-Type": "application/json"},
            json={
                "images": [image_url],
                "organs": ["leaf"],
                "api_key": api_key
            }
        )
        result = response.json()
        # Simplify the result to only useful info
        disease = result.get("health_assessment", {}).get("diseases", [{}])[0]
        return f"Disease: {disease.get('name', 'Unknown')}, Confidence: {disease.get('probability', 0)}"

    def ask_gemini(self, diagnosis_text):
        api_key = os.getenv("GEMINI_API_KEY")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        prompt = f"A plant has the following issue:\n{diagnosis_text}\nWhat care advice would you recommend?"

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        reply = response.json()
        return reply['choices'][0]['message']['content']


if __name__ == "__main__":
    config = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
            'tools.response_headers.on': True
        }
    }

    cherrypy.config.update({
        'server.socket_host': 'localhost',
        'server.socket_port': 5090
    })

    cherrypy.tree.mount(PlantHealthAssistant(), '/', config)
    cherrypy.engine.start()
    cherrypy.engine.block()
