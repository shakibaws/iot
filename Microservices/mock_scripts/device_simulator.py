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
        
        print(f"✅ Device {device_id} initialized")
        print(f"📡 Broker: {broker}:{port}")
    
    def notify(self, topic, payload):
        """Handle incoming MQTT messages (required by MyMQTT)"""
        try:
            data = json.loads(payload.decode())
            if "water_pump" in topic and data.get("target") == 1:
                print("💧 Water pump activated!")
                self.soil_moisture = min(90, self.soil_moisture + 25)
                self.watertank_level = max(0, self.watertank_level - 5)
        except Exception as e:
            print(f"❌ Error processing message: {e}")
    
    def generate_sensor_data(self):
        """Generate realistic sensor data"""
        # Time-based variations
        hour = datetime.now().hour
        if 6 <= hour <= 18:  # Day
            temp_base, light_base = 24.0, 800
        else:  # Night
            temp_base, light_base = 20.0, 50
        
        # Update sensors with natural variations
        self.temperature = temp_base + random.uniform(-3, 3)
        self.light_level = max(0, light_base + random.uniform(-200, 200))
        self.soil_moisture = max(0, self.soil_moisture - random.uniform(0.1, 0.5))
        
        # Occasionally decrease water tank
        if random.random() < 0.1:
            self.watertank_level = max(0, self.watertank_level - 1)
        
        return {
            "bn": self.device_id,
            "e": [
                {"n": "temperature", "value": round(self.temperature, 1), "unit": "C"},
                {"n": "soil_moisture", "value": round(self.soil_moisture, 1), "unit": "%"},
                {"n": "light_level", "value": round(self.light_level), "unit": "lux"},
                {"n": "watertank_level", "value": round(self.watertank_level), "unit": "%"}
            ]
        }
    
    def publish_sensor_data(self):
        """Publish sensor data using MyMQTT"""
        data = self.generate_sensor_data()
        self.client.myPublish(self.sensor_topic, data)
        print(f"📊 T={data['e'][0]['value']}°C, SM={data['e'][1]['value']}%, "
              f"L={data['e'][2]['value']}lux, WT={data['e'][3]['value']}%")
    
    def start(self):
        """Start the device simulator"""
        print(f"🚀 Starting simulation for device: {self.device_id}")
        print("📥 Subscribing to actuator commands...")
        
        # Subscribe to actuator commands
        self.client.mySubscribe(self.actuator_topic)
        
        # Connect to broker
        self.client.connect()
        
        print("📊 Publishing sensor data every 60 seconds...")
        print("💧 Listening for water pump commands...")
        print("Press Ctrl+C to stop")
        
        try:
            # Start background MQTT loop in a separate thread
            import threading
            mqtt_thread = threading.Thread(target=self.client.start)
            mqtt_thread.daemon = True
            mqtt_thread.start()
            
            # Main sensor data publishing loop
            while True:
                self.publish_sensor_data()
                time.sleep(60)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping simulator...")
            self.client.stop()
            print("✅ Stopped")


def main():
    """Main function"""
    print("🌱 IoT Device Simulator (MyMQTT Compatible)")
    print("=" * 45)
    
    # Ask for device ID
    device_id = input("Enter device ID: ").strip()
    
    if not device_id:
        print("❌ No device ID provided")
        return
    
    # Optional: Ask for broker (default to HiveMQ)
    print("\nBroker options:")
    print("1. broker.hivemq.com (default)")
    print("2. test.mosquitto.org")
    print("3. broker.emqx.io")
    print("4. Custom broker")
    
    choice = input("Select broker (1-4) or press Enter for default: ").strip()
    
    broker = "broker.hivemq.com"
    if choice == "2":
        broker = "test.mosquitto.org"
    elif choice == "3":
        broker = "broker.emqx.io"
    elif choice == "4":
        broker = input("Enter custom broker address: ").strip()
    
    # Start simulator
    simulator = DeviceSimulator(device_id, broker)
    simulator.start()


if __name__ == "__main__":
    main() 