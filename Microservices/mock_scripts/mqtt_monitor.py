#!/usr/bin/env python3
"""
MQTT Monitor - Monitor all MQTT messages using MyMQTT
"""

import sys
import os
import json
from datetime import datetime

# Add the current directory to Python path to import MyMQTT
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from MyMQTT import MyMQTT


class MQTTMonitor:
    def __init__(self, broker: str = "broker.hivemq.com", port: int = 1883):
        self.broker = broker
        self.port = port
        self.client = MyMQTT("mqtt_monitor", broker, port, self)
        
        print(f"📡 MQTT Monitor connected to {broker}:{port}")
    
    def notify(self, topic, payload):
        """Handle incoming MQTT messages"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{timestamp}] 📥 Topic: {topic}")
            
            # Try to parse as JSON for pretty printing
            try:
                data = json.loads(payload.decode())
                print(f"💾 Data: {json.dumps(data, indent=2)}")
            except:
                print(f"💾 Raw Data: {payload.decode()}")
                
        except Exception as e:
            print(f"❌ Error processing message: {e}")
    
    def start(self):
        """Start monitoring"""
        print("🚀 Starting MQTT Monitor...")
        print("📋 Monitoring all smartplant topics...")
        print("Press Ctrl+C to stop\n")
        
        # Subscribe to all smartplant topics
        self.client.mySubscribe("smartplant/#")
        
        # Connect and start listening
        self.client.connect()
        
        try:
            self.client.start()  # This will block and listen for messages
        except KeyboardInterrupt:
            print("\n🛑 Stopping monitor...")
            self.client.stop()
            print("✅ Stopped")


def main():
    """Main function"""
    print("📡 MQTT Monitor (MyMQTT Compatible)")
    print("=" * 35)
    
    # Optional: Ask for broker
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
    
    # Start monitor
    monitor = MQTTMonitor(broker)
    monitor.start()


if __name__ == "__main__":
    main() 