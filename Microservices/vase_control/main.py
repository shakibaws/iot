from MyMQTT import *
import time
import requests

class vaseControlWater:
    def __init__(self,clientID,broker,port,topic_subscirber, topic_publisher):
        self.water = MyMQTT(clientID,broker,port,self)
        self.topic_sub = topic_subscirber
        self.topic_pub = topic_publisher
    def notify(self,topic,payload):
        message_json = json.loads(payload) #data from sensor (humidity level???)
        #get call to vase catalog -> know the humidity target
        #some magic to find out how many water is needed
        t = 1 
        #send it to wateringSystem
        self.water.myPublish(self.topic_pub, {"water_target":"1"}) 
        
    def startSim(self):
        self.water.start()
        self.water.mySubscribe(self.topic_sub)
    
    def stopSim(self):
        self.water.unsubscribe()
        self.water.stop()

if __name__ == "__main__":
    clientID = "vaseControl"
    broker = "mqtt.eclipseprojects.io"
    port = 1883
    #get al service_catalog
    service_catalog = requests.get("http://localhost:8082").json()
    url_resource_catalog = service_catalog.services.resource_catalog_address
    deviceList = requests.get(f"{url_resource_catalog}/deviceList").json()
    topics_sensors= []
    for device in deviceList:
       for service in device.servicesDetails:
           if service.serviceType == "MQTT":
                topics_sensors.append(service.topic)
    '''
    topic_sensor = "IoT/project/watering_sensor" #is the mosture humididty sensor??
    wateringSub = vaseControlWater(clientID,broker,port,topic_water_sub, topic_water_pub)
    # lightSub = vaseControlLight(clientID,broker,port,topic_light_sub, topic_light_pub)
    wateringSub.startSim()
    try:
        while True:        
            time.sleep(10)
    except KeyboardInterrupt:
            wateringSub.stopSim()
    '''