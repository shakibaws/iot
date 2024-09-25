from ThingSpeak.mqtt_client import MQTTClient
from ThingSpeak.env import PUBLISHER_CLIENT_ID, PUBLISHER_PASSWORD, PUBLISHER_USER_NAME, CHANNEL_ID
import time


class ThingSpeakPublisher:
    def __init__(self):
        self.client = MQTTClient(CHANNEL_ID, PUBLISHER_CLIENT_ID,
                                 PUBLISHER_USER_NAME, PUBLISHER_PASSWORD)
        self.client.connect()
        while not self.client.connected:
            time.sleep(5)
            print('Connecting...')

    def publish(self, temperature=None, soil_moisture=None, light_level=None, watertank_level=None, status=None):
        self.client.publish_data(temperature, soil_moisture,
                                 light_level, watertank_level, status)
        self.disconnect()

    def disconnect(self):
        self.client.disconnect()