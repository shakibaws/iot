from MyMQTT import *
import time

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
    topic_water_sub = "IoT/project/watering_sensor" #is the mosture humididty sensor??
    topic_water_pub = "IoT/project/watering_service"
    topic_light_sub = "IoT/project/light_sensor" #is the mosture humididty sensor??
    topic_light_pub = "IoT/project/light_service"
    wateringSub = vaseControlWater(clientID,broker,port,topic_water_sub, topic_water_pub)
    # lightSub = vaseControlLight(clientID,broker,port,topic_light_sub, topic_light_pub)
    wateringSub.startSim()
    try:
        while True:        
            time.sleep(10)
    except KeyboardInterrupt:
            wateringSub.stopSim()