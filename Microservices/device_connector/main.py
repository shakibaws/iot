#!/usr/bin/env python3

import cherrypy
import json
import requests
import time
import os
import sys
import datetime
import CustomerLogger

class DeviceRegistrationService:
    exposed = True
    
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.service_catalog_url = "http://service_catalog:5001/all"
        self.device_cfg = {}
        self.service_catalog = {}
        self.logger = CustomerLogger.CustomLogger("device_registration_service")
        
        # Load device configuration on startup
        self.load_config()

    def load_config(self):
        """Load device configuration from config.json"""
        try:
            with open(self.config_path, "r") as file:
                self.device_cfg = json.load(file)
                self.logger.info(f"Loaded device configuration from {self.config_path}")
                return True
        except FileNotFoundError:
            self.logger.error(f"Config file {self.config_path} not found")
            return False
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON in {self.config_path}")
            return False

    def get_service_catalog(self):
        """Get service catalog from the service catalog URL"""
        retries = 5
        for attempt in range(retries):
            try:
                self.logger.info(f"Getting service catalog (attempt {attempt + 1}/{retries})")
                response = requests.get(self.service_catalog_url, timeout=10)
                response.raise_for_status()
                self.service_catalog = response.json()
                self.logger.info("Retrieved service catalog successfully")
                
                # Save service catalog locally for future use
                with open("service_catalog.json", "w") as file:
                    json.dump(self.service_catalog, file, indent=2)
                self.logger.info("Saved service catalog locally")
                return True
                
            except requests.RequestException as e:
                if attempt < retries - 1:
                    self.logger.error(f"Error getting service catalog: {e}. Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    self.logger.error(f"Failed to get service catalog after {retries} attempts: {e}")
                    return False
        return False

    def get_next_device_id(self):
        """Get the next available device ID by querying existing devices"""
        try:
            resource_catalog_url = self.service_catalog["services"]["resource_catalog"]
            list_devices_url = f"{resource_catalog_url}/listDevice"
            
            self.logger.info("Fetching existing devices to determine next device ID")
            response = requests.get(list_devices_url, timeout=10)
            response.raise_for_status()
            
            devices = response.json()
            self.logger.info(f"Found {len(devices)} existing devices")
            
            # Find the highest device ID number
            max_device_num = 0
            for device in devices:
                device_id = device.get("device_id", "")
                if device_id.startswith("device") and len(device_id) > 6:
                    try:
                        # Extract number from device_id like "device1", "device2", etc.
                        device_num_str = device_id[6:]  # Remove "device" prefix
                        device_num = int(device_num_str)
                        max_device_num = max(max_device_num, device_num)
                    except ValueError:
                        # Skip devices with unexpected ID format
                        continue
            
            next_device_id = f"device{max_device_num + 1}"
            self.logger.info(f"Next device ID will be: {next_device_id}")
            return next_device_id
            
        except requests.RequestException as e:
            self.logger.error(f"Error fetching devices list: {e}")
            # Fallback to default if we can't fetch the list
            return "device1"
        except Exception as e:
            self.logger.error(f"Unexpected error determining next device ID: {e}")
            # Fallback to default if something goes wrong
            return "device1"

    def register_device_with_catalog(self, user_id):
        """Register device with resource catalog"""
        # Generate next device ID
        next_device_id = self.get_next_device_id()
        
        # Add user_id and auto-generated device_id to device configuration
        device_info = self.device_cfg["device"].copy()
        device_info["user_id"] = user_id
        device_info["device_id"] = next_device_id  # Override with auto-generated ID
        
        # Get resource catalog URL
        try:
            resource_catalog_url = self.service_catalog["services"]["resource_catalog"]
            register_url = f"{resource_catalog_url}/device"
            self.logger.info(f"Registering device at: {register_url}")
        except KeyError:
            self.logger.error("resource_catalog service not found in service catalog")
            return False, "Resource catalog service not found"

        # Register device with retry logic
        retries = 5
        for attempt in range(retries):
            try:
                self.logger.info(f"Registering device (attempt {attempt + 1}/{retries})")
                response = requests.post(register_url, json=device_info, timeout=10)
                response.raise_for_status()
                
                self.logger.info("Device registered successfully!")
                self.logger.info(f"Device ID: {device_info['device_id']}, User ID: {user_id}")
                
                # Get response data
                response_data = {}
                if response.text:
                    try:
                        response_data = response.json()
                    except json.JSONDecodeError:
                        response_data = {"response_text": response.text}
                
                return True, {
                    "device_id": device_info["device_id"],
                    "user_id": user_id,
                    "status_code": response.status_code,
                    "response_data": response_data
                }
                
            except requests.RequestException as e:
                if attempt < retries - 1:
                    self.logger.error(f"Error registering device: {e}. Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    self.logger.error(f"Failed to register device after {retries} attempts: {e}")
                    return False, f"Failed to register device: {e}"
        return False, "Registration failed after all retries"

    @cherrypy.tools.json_out()
    @cherrypy.tools.response_headers(headers=[('Access-Control-Allow-Origin', '*'),
                                                ('Access-Control-Allow-Methods', 'POST, OPTIONS, GET'),
                                                ('Access-Control-Allow-Headers', 'Content-Type')])
    def GET(self, *args, **kwargs):
        """Handle GET requests for device registration"""
        self.logger.info("GET request received for device registration")
        
        # Check if user_id is provided as query parameter
        user_id = kwargs.get('user_id')
        if not user_id:
            self.logger.error("Missing user_id parameter")
            raise cherrypy.HTTPError(400, "Missing user_id parameter")
        
        # Validate user_id
        user_id = user_id.strip()
        if not user_id:
            self.logger.error("Empty user_id parameter")
            raise cherrypy.HTTPError(400, "Empty user_id parameter")
        
        # Load configuration if not already loaded
        if not self.device_cfg:
            if not self.load_config():
                self.logger.error("Failed to load device configuration")
                raise cherrypy.HTTPError(500, "Failed to load device configuration")
        
        # Get service catalog
        if not self.get_service_catalog():
            self.logger.error("Failed to get service catalog")
            raise cherrypy.HTTPError(500, "Failed to get service catalog")
        
        # Register device
        success, result = self.register_device_with_catalog(user_id)
        
        if success:
            self.logger.info(f"Device registration completed successfully for user: {user_id}")
            return {
                "status": "success",
                "message": "Device registered successfully",
                "data": result
            }
        else:
            self.logger.error(f"Device registration failed for user: {user_id}")
            raise cherrypy.HTTPError(500, f"Device registration failed: {result}")

    
    def OPTIONS(self, *args, **kwargs):
        """Handle OPTIONS requests for CORS"""
        pass

def main():
    """Main function to start the CherryPy server"""
    try:
        # Change to script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        
        # Create device registration service
        device_registration = DeviceRegistrationService()
        
        # CherryPy configuration
        conf = {
            '/': {
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                'tools.sessions.on': True,
                'tools.response_headers.on': True,
            }
        }
        
        cherrypy.config.update({
            'server.socket_host': '0.0.0.0',
            'server.socket_port': 5004  # Choose appropriate port
        })
        
        cherrypy.tree.mount(device_registration, '/', conf)
        cherrypy.engine.start()
        cherrypy.engine.block()
        
    except Exception as e:
        print("ERROR OCCURRED, DUMPING INFO...")
        path = os.path.abspath('./logs/ERROR_deviceregistration.err')
        with open(path, 'a') as file:
            date = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
            file.write(f"Crashed at : {date}\n")
            file.write(f"Unexpected error: {e}\n")
        print(e)
        print("EXITING...")
        sys.exit(1)

if __name__ == "__main__":
    main() 