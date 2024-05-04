from mqtt_client import MQTTClient
from env import LISTENER_CLIENT_ID, LISTENER_PASSWORD, LISTENER_USER_NAME, CHANNEL_ID

import time


client = MQTTClient(CHANNEL_ID, LISTENER_CLIENT_ID,
                    LISTENER_USER_NAME, LISTENER_PASSWORD)


def on_message(topic, message):
    print(f"Received message on topic {topic}: {message}")


client.connect()

while not client.connected:
    time.sleep(5)

    print('Connecting..')

client.subscribe_to_channel(on_message)


while True:
    time.sleep(10)
