import json
import CustomerLogger
import paho.mqtt.client as PahoMQTT
service_name = "thingspeak_adaptor"


class MyMQTT:
    def __init__(self, clientID, broker, port, notifier):
        self.broker = broker
        self.port = port
        self.notifier = notifier
        self.clientID = clientID
        self._topic = ""
        self._isSubscriber = False
        # create an instance of paho.mqtt.client
        # Handle both old and new versions of paho-mqtt
        try:
            self._paho_mqtt = PahoMQTT.Client(PahoMQTT.CallbackAPIVersion.VERSION1, clientID, True)
        except AttributeError:
            # Fallback for older versions of paho-mqtt
            self._paho_mqtt = PahoMQTT.Client(clientID, True)
        # register the callback
        self._paho_mqtt.on_connect = self.myOnConnect
        self._paho_mqtt.on_message = self.myOnMessageReceived
        self.logger = CustomerLogger.CustomLogger(service_name)

    def myOnConnect(self, paho_mqtt, userdata, flags, rc):
        self.logger.info(f"Connected to {self.broker} with result code: {rc}")
        self.logger.info(f"Subscribed to {self._topic}")
        self._paho_mqtt.subscribe(self._topic, 2)

    def myOnMessageReceived(self, paho_mqtt, userdata, msg):
        print("Message received")
        self.notifier.notify(msg.topic, msg.payload)
        self.logger.info(f"Message received on topic: {msg.topic}, {msg.payload}")

    def myPublish(self, topic, msg):
        self.logger.info(f"Publishing message on topic: {topic}, {msg}")
        self._paho_mqtt.publish(topic, json.dumps(msg), 2)

    def mySubscribe(self, topic):
        print("Subscribing...")
        self._isSubscriber = True
        self._topic = topic

    def connect(self):
        # manage connection to broker
        print(f"Connecting to {self.broker}, {self.port}")
        self._paho_mqtt.connect(self.broker, self.port)
        #self._paho_mqtt.loop_start()

    def start(self):
        self._paho_mqtt.loop_forever()

    def unsubscribe(self):
        if (self._isSubscriber):
            #log_to_loki("info", f"unsubscribed from {self._topic}", service_name=service_name, service_name=service_name, user_id=user_id, request_id=request_id)
            self._paho_mqtt.unsubscribe(self._topic)

    def stop(self):
        if (self._isSubscriber):
            # remember to unsuscribe if it is working also as subscriber
            self._paho_mqtt.unsubscribe(self._topic)

        self._paho_mqtt.loop_stop()
        self._paho_mqtt.disconnect() 