from BaseMQTT import BaseMQTT

import json
import time

'''
message format:
{sender: <sender_student_id>, msg: <string>}
'''

class EX1:
    def __init__(self, clientid, broker, port, topic):
        
        self.mqtt = BaseMQTT(clientid, broker, port, self)
        self.mqtt.start()
        if topic:
            self.mqtt.mySubscribe(topic)

    def notify(self, topic, payload):
        print("Received message on topic: ", topic)
        print("Message: ", payload)

    def stop(self):
        self.mqtt.stop()


if __name__ == "__main__":
    broker = "mqtt.eclipseprojects.io"
    port = 1883
    clientid = "testpublish"
    topic = "test"

    mqtt = EX1(clientid, broker, port, topic)

    try:
        while True:        
            time.sleep(10)
    except KeyboardInterrupt:
            EX1.stop()
        