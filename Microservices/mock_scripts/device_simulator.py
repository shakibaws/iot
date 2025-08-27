#!/usr/bin/env python3
"""
Simple IoT Device Simulator - Uses MyMQTT class (compatible with microservices)
"""

import json
import time
import random
import sys
import os
from datetime import datetime

# Add the current directory to Python path to import MyMQTT
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from MyMQTT import MyMQTT


class DeviceSimulator:
    def __init__(self, device_id: str, broker: str = "broker.hivemq.com", port: int = 1883):
        self.device_id = device_id
        self.broker = broker
        self.port = port
        
        # Initialize MQTT client using MyMQTT
        self.client = MyMQTT(f"device_simulator_{device_id}", broker, port, self)
        
        # Sensor states
        self.temperature = 22.0
        self.soil_moisture = 45.0
        self.light_level = 600
        self.watertank_level = 80
        
        # Topics
        self.sensor_topic = f"smartplant/{device_id}/sensors"
        self.actuator_topic = f"smartplant/{device_id}/actuators/+"
        
        print(f"Device {device_id} initialized")
        print(f"Broker: {broker}:{port}")
    
    def notify(self, topic, payload):
        """Handle incoming MQTT messages (required by MyMQTT)"""
        try:
            data = json.loads(payload.decode())
            if "water_pump" in topic and data.get("target") == 1:
                print("Water pump activated!")
                self.soil_moisture = min(90, self.soil_moisture + 25)
                self.watertank_level = max(0, self.watertank_level - 5)
        except Exception as e:
            print(f"Error processing message: {e}")
    
   
    
    def publish_sensor_data(self, data):
        """Publish sensor data using MyMQTT"""
        # data = self.generate_sensor_data()
        self.client.myPublish(self.sensor_topic, data)
        print(f"T={data['e'][0]['value']}°C, SM={data['e'][1]['value']}%, "
              f"L={data['e'][2]['value']}lux, WT={data['e'][3]['value']}%")
    
    def start(self):
        """Start the device simulator"""
        print(f"Starting simulation for device: {self.device_id}")
        print("Subscribing to actuator commands...")
        
        # Subscribe to actuator commands
        self.client.mySubscribe(self.actuator_topic)
        
        # Connect to broker
        self.client.connect()
        
        print("Publishing sensor data every 60 seconds...")
        print("Listening for water pump commands...")
        print("Press Ctrl+C to stop")
        
        try:
            # Start background MQTT loop in a separate thread
            import threading
            mqtt_thread = threading.Thread(target=self.client.start)
            mqtt_thread.daemon = True
            mqtt_thread.start()

                
        except KeyboardInterrupt:
            print("\nStopping simulator...")
            self.client.stop()
            print("Stopped")


# def main():
#     """Main function"""
#     print("🌱 IoT Device Simulator (MyMQTT Compatible)")
#     print("=" * 45)
    
#     # Ask for device ID
#     device_id = input("Enter device ID: ").strip()
    
#     if not device_id:
#         print("❌ No device ID provided")
#         return
    
#     # Use default broker
#     broker = "broker.hivemq.com"
    
#     # Start simulator
#     simulator = DeviceSimulator(device_id, broker)
#     simulator.start()


# if __name__ == "__main__":
#     main() 