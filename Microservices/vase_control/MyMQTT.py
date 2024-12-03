import json
import CustomerLogger
import paho.mqtt.client as PahoMQTT


class MyMQTT:
    def __init__(self, clientID, broker, port, notifier):
        self.broker = broker
        self.port = port
        self.notifier = notifier
        self.clientID = clientID
        self._topic = ""
        self._isSubscriber = False
        # create an instance of paho.mqtt.client
        self._paho_mqtt = PahoMQTT.Client(PahoMQTT.CallbackAPIVersion.VERSION1, clientID, True)
        # register the callback
        self._paho_mqtt.on_connect = self.myOnConnect
        self._paho_mqtt.on_message = self.myOnMessageReceived
        self.logger = CustomerLogger.CustomLogger("vase_control")

    def myOnConnect(self, paho_mqtt, userdata, flags, rc):
        self.logger.info(f"Connected to {self.broker} with result code: {rc}")
        if self._topic:
            self.logger.info(f"Subscribed to {self._topic}")
            self._paho_mqtt.subscribe(self._topic, 2)
        else:
            self.logger.warning("No topic set to subscribe")
                
    
    def myOnMessageReceived(self, paho_mqtt, userdata, msg):
        self.logger.info(f"Message received on topic: {msg.topic}, {msg.payload}")
        self.notifier.notify(msg.topic, msg.payload)

    def myPublish(self, topic, msg):
        self.logger.info(f"Publishing message on topic: {topic}, {msg}")
        self._paho_mqtt.publish(topic, json.dumps(msg), 2)

    def mySubscribe(self, topic):
        # subscribe for a topic
        self.logger.info("subscribing to" + topic)
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
            self.logger.info(f"Unsubscribed from {self._topic}")
            self._paho_mqtt.unsubscribe(self._topic)

    def stop(self):
        if (self._isSubscriber):
            self._paho_mqtt.unsubscribe(self._topic)

        self._paho_mqtt.loop_stop()
        self._paho_mqtt.disconnect()
