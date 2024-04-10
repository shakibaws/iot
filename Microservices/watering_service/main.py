from MyMQTT import *
import time

class WateringServiceSubscriber:
    def __init__(self,clientID,broker,port,topic_subscirber, topic_publisher):
        self.waterLevel = 100 #TODO get from the sensor
        self.wateringClientSub = MyMQTT(clientID,broker,port,self)
        self.topic_sub = topic_subscirber
        self.topic_pub = topic_publisher
    def notify(self,topic,payload):
        message_json = json.loads(payload) #get the target from teh vase_catalog
        #check if the water in the tanks is enough
        
        #menage the watering action
        
        #check if the water in the tanks is enough for the next time
        
        self.wateringClientSub.myPublish(self.topic_pub, {"water_level": 'low'})
    def startSim(self):
        self.wateringClientSub.start()
        self.wateringClientSub.mySubscribe(self.topic_sub)
    
    def stopSim(self):
        self.wateringClientSub.unsubscribe()
        self.wateringClientSub.stop()

if __name__ == "__main__":
    clientID = "wateringService"
    broker = "mqtt.eclipseprojects.io"
    port = 1883
    topic_sub = "IoT/project/watering_service"
    topic_pub = "IoT/project/water_level_low"

    wateringSub = WateringServiceSubscriber(clientID,broker,port,topic_sub,topic_pub)
    wateringSub.startSim()
    try:
        while True:        
            time.sleep(10)
    except KeyboardInterrupt:
            wateringSub.stopSim()