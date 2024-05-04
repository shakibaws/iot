import paho.mqtt.client as mqtt


class MQTTClient:
    def __init__(self, channel_id, client_id, username, password):
        self.channel_id = channel_id
        self.client_id = client_id
        self.username = username
        self.password = password
        self.client = mqtt.Client(client_id=client_id)
        self.client.username_pw_set(username=username, password=password)
        self.connected = False
        self.on_message_callback = None

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            print("Connected to MQTT Broker!")
        else:
            print(f"Connection failed with code {rc}")

    def on_message(self, client, userdata, msg):
        if self.on_message_callback:
            self.on_message_callback(msg.topic, msg.payload.decode('utf-8'))

    def connect(self):
        if not self.connected:
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.connect("mqtt3.thingspeak.com", 1883)
            self.client.loop_start()

    def disconnect(self):
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False

    def publish_data(self, field1, field2, status):
        if self.connected:
            payload = f"field1={field1}&field2={field2}&status={status}"
            topic = f"channels/{self.channel_id}/publish"
            self.client.publish(topic, payload)
            print(f"Published data: {payload} to topic: {topic}")
        else:
            print("Not connected to MQTT Broker. Please connect first.")

    def subscribe_to_channel(self, callback):
        if self.connected:
            topic = f"channels/{self.channel_id}/subscribe"
            self.client.subscribe(topic, qos=0)
            print(f"Subscribed to topic: {topic}")
            self.on_message_callback = callback
        else:
            print("Not connected to MQTT Broker. Please connect first.")
