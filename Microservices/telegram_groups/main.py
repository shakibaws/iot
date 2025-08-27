import cherrypy
import json
import datetime
import aiohttp
import asyncio
import requests
import CustomerLogger
import os
import sys


class TelegramGroupsExpose:
    exposed = True

    def __init__(self):
        self.logger = CustomerLogger.CustomLogger("telegramgroups")
        self.service_catalog_address = 'http://service_catalog:5001'
        self.resource_catalog_address = ''
        
        # Get resource catalog address from service catalog
        self._initialize_resource_catalog_address()

    def _initialize_resource_catalog_address(self):
        """Initialize resource catalog address from service catalog"""
        try:
            response = requests.get(f"{self.service_catalog_address}/all")
            if response.status_code == 200:
                services = response.json()
                self.resource_catalog_address = services['services']['resource_catalog']
                self.logger.info(f"Successfully retrieved resource catalog address: {self.resource_catalog_address}")
            else:
                self.logger.error(f"Failed to get service catalog. Status: {response.status_code}")
                raise Exception("Failed to initialize resource catalog address")
        except Exception as e:
            self.logger.error(f"Error initializing resource catalog address: {e}")
            raise

    async def get_telegram_group_by_plant_type(self, plant_type):
        """Get telegram group that matches the given plant type"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.resource_catalog_address}/listgroup") as response:
                    self.logger.info(f"Fetching groups from resource catalog. Status: {response.status}")
                    
                    if response.status == 200:
                        group_list = await response.json()
                        self.logger.info(f"Retrieved {len(group_list)} groups from resource catalog")
                        
                        # Find matching group by plant type
                        for group in group_list:
                            if group.get('plant_type') == plant_type:
                                self.logger.info(f"Found matching group for plant type '{plant_type}': {group.get('name')}")
                                return group
                        
                        self.logger.info(f"No group found for plant type: {plant_type}")
                        return None
                    else:
                        self.logger.error(f"Failed to get group list from resource catalog. Status: {response.status}")
                        return None
                        
        except Exception as e:
            self.logger.error(f"Error fetching telegram groups: {e}")
            return None

    @cherrypy.tools.json_out()
    def GET(self, *args, **kwargs):
        """Handle GET requests to find telegram groups by plant type"""
        self.logger.info(f"GET request received with args: {args}, kwargs: {kwargs}")
        
        if not args or len(args) == 0:
            self.logger.error("No plant type provided in request")
            raise cherrypy.HTTPError(400, "Plant type is required")
        
        plant_type = args[0].lower()
        self.logger.info(f"Looking for telegram group with plant type: {plant_type}")
        
        # Run async function
        result = asyncio.run(self.get_telegram_group_by_plant_type(plant_type))
        
        if result:
            self.logger.info(f"Successfully found group for plant type '{plant_type}'")
            return result
        else:
            self.logger.info(f"No group found for plant type '{plant_type}'")
            raise cherrypy.HTTPError(404, f"No telegram group found for plant type: {plant_type}")

    @cherrypy.tools.json_out()
    def OPTIONS(self, *args, **kwargs):
        """Handle CORS preflight requests"""
        cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
        cherrypy.response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        cherrypy.response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return ""


if __name__ == '__main__':
    try:
        telegramgroups_service = TelegramGroupsExpose()
        
        conf = {
            '/': {
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                'tools.sessions.on': True,
                'tools.response_headers.on': True,
                'tools.response_headers.headers': [
                    ('Access-Control-Allow-Origin', '*'),
                    ('Access-Control-Allow-Methods', 'GET, OPTIONS'),
                    ('Access-Control-Allow-Headers', 'Content-Type')
                ]
            }
        }
        
        cherrypy.config.update({
            'server.socket_host': '0.0.0.0',
            'server.socket_port': 5011
        })
        
        cherrypy.tree.mount(telegramgroups_service, '/', conf)
        cherrypy.engine.start()
        cherrypy.engine.block()
        
    except Exception as e:
        print("ERROR OCCURRED, DUMPING INFO...")
        path = os.path.abspath('./logs/ERROR_telegramgroups.err')
        with open(path, 'a') as file:
            date = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
            file.write(f"Crashed at : {date}\n")
            file.write(f"Unexpected error: {e}\n")
        print(e)
        print("EXITING...")
        sys.exit(1)
