import datetime
from MyMQTT import *
import time
import requests

class vaseControl:
    def __init__(self,clientID,broker,port,topic_sensors, topic_actuators, topic_telegram_chat, resource_catalog):
        self.control = MyMQTT(clientID,broker,port,self)
        self.topic_sub = topic_sensors
        self.topic_pub = topic_actuators
        self.topic_telegram_chat = topic_telegram_chat
        self.boo = 1
        
    def notify(self,topic,payload):
        data = json.loads(payload)
        print(f"Message received on topic: {topic}, {data}")
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
        vase = requests.get(resource_catalog+'/vase/'+resource['vase_id']).json()
        user_id = vase["user_id"]
        user = requests.get(resource_catalog+'/user/'+user_id).json()
        telegram_chat = self.topic_telegram_chat.replace("telegram_chat_id", user["telegram_chat_id"])

        """ {
            'bn': device_id,
            'e':
            [
                {'n': 'temperature', 'value': '', 'timestamp': '', 'unit': 'C'},
                {'n': 'soil_moisture', 'value': '', 'timestamp': '', 'unit': '%'}
                {'n': 'light_level', 'value': '', 'timestamp': '', 'unit': 'lumen'},
                {'n': 'watertank_level', 'value': '', 'timestamp': '', 'unit': '%'}
            ]
        } """
        for i in data['e']:    
            if i['n'] == 'light_level':
                if i['value'] < 100 and datetime.now().hour < vase["plant"]["plant_schedule_light"]:
                    """ if "MQTT" in resource["available_services"] and "light" in resource["actuators"]:
                        # send number of hours to light
                        self.control.myPublish(publisher+"/light", {"target":1})
                    else:
                        self.control.myPublish(telegram_chat/"alert", {"light":"low"}) """
                    # send number of hours to light
                    self.control.myPublish(publisher+"/"+i['n'], {"target":1})
                else: # enough light or past schedule
                    self.control.myPublish(publisher+"/"+i['n'], {"target":0}) # turn off the light

            elif i['n'] == "temperature":
                if i['value'] < vase["plant"]["temperature_min"]:
                    self.control.myPublish(telegram_chat+"/alert", {"temperature":"low"})
                elif i['value'] > vase["plant"]["temperature_max"]:
                    self.control.myPublish(telegram_chat+"/alert", {"temperature":"high"})
            
            elif i['n'] == "soil_moisture":
                if i['value'] < vase["plant"]["soil_moisture_min"] or i['value'] < 10000:
                    if self.boo == 1:
                        self.boo = 0
                    else:
                        self.boo = 1
                    self.control.myPublish(publisher+"/"+i['n'], {"target":1}) # wet the plant

            elif i['n'] == "watertank_level":
                if i['value'] < 10:
                    self.control.myPublish(telegram_chat+"/alert", {"watertank_level":"low"})

if __name__ == "__main__":

    clientID = "vase_control"

    #get al service_catalog
    go = False
    while not go:
        try:
            service_catalog = requests.get("http://serviceservice.duck.pictures/all").json()
            go = True
        except requests.exceptions.RequestException as e:
            print(f"Error occurred while making the HTTP request: {e}")
        time.sleep(5)
    topicSensors = service_catalog["topics"]["topic_sensors"]
    topicActuators = service_catalog["topics"]["topic_actuators"]
    topic_telegram_chat = service_catalog["topics"]["topic_telegram_chat"]
    resource_catalog = service_catalog["services"]["resource_catalog_address"]
    broker = service_catalog["broker"]["broker_address"]
    port = service_catalog["broker"]["port"]

    controller = vaseControl(clientID,broker,port,topicSensors,topicActuators,topic_telegram_chat,resource_catalog)
    controller.startSim()

    try:
        while True:        
            time.sleep(10)
    except KeyboardInterrupt:
            controller.stopSim()
    