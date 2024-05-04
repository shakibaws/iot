from mqtt_client import MQTTClient
from env import PUBLISHER_CLIENT_ID, PUBLISHER_PASSWORD, PUBLISHER_USER_NAME, CHANNEL_ID
import time


client = MQTTClient(CHANNEL_ID, PUBLISHER_CLIENT_ID,
                    PUBLISHER_USER_NAME, PUBLISHER_PASSWORD)


def on_message(topic, message):
    print(f"Received message on topic {topic}: {message}")


client.connect()

while not client.connected:
    time.sleep(5)

    print('Connecting..')

client.publish_data(5, 6, "MQTTPUBLISH")

client.disconnect()
