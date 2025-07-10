import cherrypy
import requests
import os
import json
from CustomerLogger import CustomLogger  

class AdminAnalyticsService:
    def __init__(self):
        self.logger = CustomLogger.CustomLogger("admin_analytics_service")
        self.logger.info("Admin Analytics Service started")

    def GET(self, **params):
        self.logger.info("GET request received")
        return "Admin Analytics Service"    

    def POST(self, **params):
        try:
            self.logger.info("POST request received")
            request_body = cherrypy.request.body.read()
            data = json.loads(request_body)
            device_id = data.get("device_id")
            actuator = data.get("actuator")
            if not device_id or not actuator:
                self.logger.error("Missing device_id or actuator in request")
                raise cherrypy.HTTPError(400, "Missing device_id or actuator")
            self.logger.info("Received device_id: {}, actuator: {}".format(device_id, actuator))
            return json.dumps({"message": "Data received successfully"})   
        
        





        except Exception as e:
            self.logger.error(f"Error in AdminAnalyticsService: {str(e)}")
            raise cherrypy.HTTPError(500, "Internal Server Error")
