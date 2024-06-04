import json
import time

import paho.mqtt.client as PahoMQTT


class BaseMQTT:
    def __init__(self, clientID, broker, port, notifier):
        self.broker = broker
        self.port = port
        self.notifier = notifier
        self.clientID = clientID
        self._topic = ""
        self._isSubscriber = False
        self.connected = False
        # create an instance of paho.mqtt.client
        self._paho_mqtt = PahoMQTT.Client(PahoMQTT.CallbackAPIVersion.VERSION1, clientID, True)
        # register the callback
        self._paho_mqtt.on_connect = self.myOnConnect
        self._paho_mqtt.on_message = self.myOnMessageReceived

    def myOnConnect(self, paho_mqtt, userdata, flags, rc):
        if rc == 0:
            print("Connected to %s" % (self.broker))
            self.connected = True
        else:
            print("Connection failed")

    def myOnMessageReceived(self, paho_mqtt, userdata, msg):
        # A new message is received
        self.notifier.notify(msg.topic, msg.payload)

    def myPublish(self, topic, msg):
        # publish a message with a certain topic
        self._paho_mqtt.publish(topic, json.dumps(msg), 2)
        print("Published on topic %s: %s" % (topic, msg))

    def myBytesPublish(self, topic, msg):
        # publish a message with a certain topic
        self._paho_mqtt.publish(topic, msg, 2)
        print("Published on topic %s: %s" % (topic, msg.hex()))

    def mySubscribe(self, topic):
        # check if connection is established
        if not self.connected:
            time.sleep(1)
        
        if not self.connected:
            print("Connection not established. Cannot subscribe.")
            return
        # subscribe for a topic
        self._paho_mqtt.subscribe(topic, 2)
        # just to remember that it works also as a subscriber
        self._isSubscriber = True
        self._topic = topic
        print("subscribed to %s" % (topic))

    def start(self):
        # manage connection to broker
        self._paho_mqtt.connect(self.broker, self.port)
        self._paho_mqtt.loop_start()

    def unsubscribe(self):
        if (self._isSubscriber):
            # remember to unsuscribe if it is working also as subscriber
            self._paho_mqtt.unsubscribe(self._topic)

    def stop(self):
        if (self._isSubscriber):
            # remember to unsuscribe if it is working also as subscriber
            self._paho_mqtt.unsubscribe(self._topic)

        self._paho_mqtt.loop_stop()
        self._paho_mqtt.disconnect()