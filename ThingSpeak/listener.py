from ThingSpeak.mqtt_client import MQTTClient
from ThingSpeak.env import LISTENER_CLIENT_ID, LISTENER_PASSWORD, LISTENER_USER_NAME, CHANNEL_ID
import time
import threading


class ThingSpeakListener:
    def __init__(self):
        self.client = MQTTClient(CHANNEL_ID, LISTENER_CLIENT_ID,
                                 LISTENER_USER_NAME, LISTENER_PASSWORD)
        self.client.connect()
        while not self.client.connected:
            time.sleep(5)
            print('Connecting...')

    def start_listening(self, on_message_callback):
        # Start listening in a separate thread
        self.client.subscribe_to_channel(on_message_callback)
        self._listening = True
        self._listen_thread = threading.Thread(target=self._keep_listening)
        self._listen_thread.start()

    def _keep_listening(self):
        while self._listening:
            time.sleep(10)

    def stop_listening(self):
        self._listening = False
        self._listen_thread.join()
        self.client.disconnect()