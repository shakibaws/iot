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

    def publish(self, topicPub):
        self.mqtt.myPublish(topicPub, {'target': 1})

    def stop(self):
        self.mqtt.stop()


if __name__ == "__main__":
    broker = "broker.emqx.io"
    port = 1883
    clientid = "test_publish_4321"
    topic = 'ciao'
    topicPub = "smartplant/543456543234567/actuators/soil_moisture"

    mqtt = EX1(clientid, broker, port, topic)

    mqtt.publish(topicPub)

    try:
        while True:        
            time.sleep(10)
    except KeyboardInterrupt:
            EX1.stop()
        