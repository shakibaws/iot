from umqtt.simple import MQTTClient
import ujson

class myMqtt:
    def __init__(self, clientid, broker, port, actuate):
        self.actuate = actuate
        self.mqttc = MQTTClient(clientid, broker, port = port, keepalive=60)
        self.mqttc.set_callback(self.myOnReceive)
        
    def connect(self):
        self.mqttc.connect()

    def subscribe(self, topic):
        self.mqttc.subscribe(topic)
        print("Sub on topic: ", topic)

    def publish(self, topic, message):
        self.mqttc.publish(topic, message)
        print("Message published: ",message)

    def publishJson(self, topic, message):
        self.mqttc.publish(topic, ujson.dumps(message))
        print("Json published: ", ujson.dumps(message))

    def check_message(self):
        self.mqttc.check_msg()

    def myOnReceive(self, topic, msg):
        # topic received in bytes
        # Decode topic from bytes to string
        topic_str = topic.decode('utf-8')
        print(f"New message on topic: {topic}, {msg}")
        self.actuate(topic_str, msg)
        self.mqttc.check_msg() # check other message in queue

    def disconnect(self):
        self.mqttc.unsubscribe()
        self.mqttc.disconnect()
        print("Disconnected from MQTT broker")