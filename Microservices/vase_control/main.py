import datetime
from MyMQTT import *
import time
import requests
import CustomerLogger

class vaseControl:
    def __init__(self,clientID,broker,port,topic_sensors, topic_actuators, topic_telegram_chat, resource_catalog):
        self.control = MyMQTT(clientID,broker,port,self)
        self.topic_sub = topic_sensors
        self.topic_pub = topic_actuators
        self.topic_telegram_chat = topic_telegram_chat
        self.boo = 1
        self.logger = CustomerLogger.CustomLogger("vase_control", "user_id_test")
        
    def notify(self,topic,payload):
        data = json.loads(payload)
        print(f"Message received on topic: {topic}, {data}")
        self.logger.info(f"Message received on topic: {topic}, {data}")
        # "topic_sensors": "smartplant/+/sensors",
        # "topic_actuators": "smartplant/device_id/actuators"
        device_id = topic.split('/')[1]
        self.controller(data, device_id)

        
    def startSim(self):
        self.control.start()
        self.control.mySubscribe(self.topic_sub)
    
    def stopSim(self):
        self.control.unsubscribe()
        self.control.stop()

    def controller(self, data, device_id):
        publisher = self.topic_pub.replace("device_id", device_id)
        resource = requests.get(resource_catalog+'/device/'+device_id).json()
        vase = requests.get(resource_catalog+'/vaseByDevice/'+device_id).json()

    
        # If the device is not configured yet (no vase)
        if not vase:
            self.logger.error(f"Device {device_id} is not configured yet")
            return
        else:
            user_id = vase["user_id"]
            user = requests.get(resource_catalog+'/user/'+user_id).json()
            telegram_chat = self.topic_telegram_chat.replace("telegram_chat_id", str(user["telegram_chat_id"]))
            self.logger.info(f"Analyzing data from {device_id}")
            for i in data['e']:    
                if i['n'] == 'light_level':
                    # to be analyze later with thingspeak data
                    pass
                elif i['n'] == "temperature":
                    # to be analyze later with thingspeak data
                    pass
                    """ if i['value'] < vase["plant"]["temperature_min"]:
                        self.control.myPublish(telegram_chat+"/alert", {"temperature":"low"})
                    elif i['value'] > vase["plant"]["temperature_max"]:
                        self.control.myPublish(telegram_chat+"/alert", {"temperature":"high"}) """
                elif i['n'] == "soil_moisture":
                    if int(i['value']) < int(vase["plant"]["soil_moisture_min"]):
                        self.control.myPublish(publisher+"/"+i['n'], {"target":1}) # wet the plant
                elif i['n'] == "watertank_level":
                    if int(i['value']) < 20:
                        self.control.myPublish(telegram_chat+"/alert", {"watertank_level": f"{vase['vase_name']}"})

if __name__ == "__main__":

    clientID = "vase_control"

    #get al service_catalog
    service_catalog = requests.get("http://serviceservice.duck.pictures/all").json()

    topicSensors = service_catalog["mqtt_topics"]["topic_sensors"]
    topicActuators = service_catalog["mqtt_topics"]["topic_actuators"]
    topic_telegram_chat = service_catalog["mqtt_topics"]["topic_telegram_chat"]
    resource_catalog = service_catalog["services"]["resource_catalog"]
    broker = service_catalog["mqtt_broker"]["broker_address"]
    port = service_catalog["mqtt_broker"]["port"]

    controller = vaseControl(clientID,broker,port,topicSensors,topicActuators,topic_telegram_chat,resource_catalog)
    controller.startSim()

    try:
        while True:        
            time.sleep(10)
    except KeyboardInterrupt:
            controller.stopSim()
    