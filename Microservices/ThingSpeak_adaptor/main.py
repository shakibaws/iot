import datetime
from MyMQTT import *
import time
import requests

service_name = "thingspeak_adaptor"

class vaseControl:
    def __init__(self,clientID,broker,port,topic_sensors, resource_catalog):
        self.control = MyMQTT(clientID,broker,port,self)
        self.topic_sub = topic_sensors
        
    def notify(self,topic,payload):
        data = json.loads(payload)
        # "topic_sensors": "smartplant/+/sensors",
        # "topic_actuators": "smartplant/device_id/actuators"
        device_id = topic.split('/')[1]
        self.speaker(data, device_id)


        
    def startSim(self):
        self.control.start()
        self.control.mySubscribe(self.topic_sub)

    
    def stopSim(self):
        self.control.unsubscribe()
        self.control.stop()

    def speaker(self, data, device_id):
        device = requests.get(resource_catalog+'/device/'+device_id).json()
        vase = requests.get(resource_catalog+'/vaseByDevice/'+device_id).json()
        self.logger.info(f"Analyzing data from {device_id}")
        #print("in speaker")
        #print(device)
        #print(vase)
    
        # If the device is not configured yet (no vase)
        if not vase:
            self.logger.error(f"Device {device_id} is not configured yet")
            return 
        else:
            write_key = device["write_key"]
            url = "https://api.thingspeak.com/update.json"
            
            send_data = {}
            send_data['api_key'] =  write_key  

            for i in data['e']:    
                if i['n'] == 'light_level':
                    send_data["field3"]=i['value']
                elif i['n'] == "temperature":
                    send_data["field1"]=i['value']
                elif i['n'] == "soil_moisture":
                    send_data["field2"]=i['value']
                elif i['n'] == "watertank_level":
                    send_data["field4"]=i['value']
            response = requests.post(url, data=send_data)
                    
            if response.status_code == 200:
                self.logger.info(f"Data sent to ThingSpeak for {device_id}")
            else:
                self.logger.error(f"Error in sending data to ThingSpeak for {device_id}")

if __name__ == "__main__":

    clientID = "thingspeak_adaptor"
    logger = CustomerLogger.CustomLogger(service_name, "user_id_test")
    go = False
    while not go:
        try:
            service_catalog = requests.get("http://serviceservice.duck.pictures/all").json()
            go = True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error occurred while making the HTTP request: {e}")
            print(f"Error occurred while making the HTTP request: {e}")
        time.sleep(5)
    
    logger.info("Service catalog received")
    topicSensors = service_catalog["mqtt_topics"]["topic_sensors"]
    resource_catalog = service_catalog["services"]["resource_catalog_address"]
    broker = service_catalog["mqtt_broker"]["broker_address"]
    port = service_catalog["mqtt_broker"]["port"]

    controller = vaseControl(clientID,broker,port,topicSensors,resource_catalog)
    controller.startSim()

    try:
        while True:        
            time.sleep(10)
    except KeyboardInterrupt:
            controller.stopSim()
    