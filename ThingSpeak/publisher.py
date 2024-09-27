from ThingSpeak.mqtt_client import MQTTClient
from ThingSpeak.env import PUBLISHER_CLIENT_ID, PUBLISHER_PASSWORD, PUBLISHER_USER_NAME, CHANNEL_ID
import time


class ThingSpeakPublisher:
    def __init__(self):
        self.client = MQTTClient("thingspeak_smartvase")
        self.client.connect()
        while not self.client.connected:
            time.sleep(5)
            print('Connecting...')

    def publish(self, channel_id=None, write_key=None, temperature=None, soil_moisture=None, light_level=None, watertank_level=None, status=None):
        self.client.publish_data(channel_id, write_key, temperature, soil_moisture,
                                 light_level, watertank_level, status)

    def disconnect(self):
        self.client.disconnect()