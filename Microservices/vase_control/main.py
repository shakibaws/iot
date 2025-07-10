import datetime
from MyMQTT import *
import time
import requests
import CustomerLogger
import os
import sys
import random
import asyncio
import threading

service_name="vase_control"

class vaseControl:
    def __init__(self,clientID,broker,port,topic_sensors, topic_actuators, topic_telegram_chat, resource_catalog):
        self.control = MyMQTT(clientID,broker,port,self)
        self.topic_sub = topic_sensors
        self.topic_pub = topic_actuators
        self.resource_catalog = resource_catalog
        self.topic_telegram_chat = topic_telegram_chat
        self.boo = 1
        self.logger = CustomerLogger.CustomLogger(service_name=service_name)
        self._message_arrived = False

    def timerRestart(self):
        # check every 5 minutes if a new message has arrived, otherwise restart the service
        while True:
            self._message_arrived = False
            time.sleep(300)
            if not self._message_arrived:
                print("Stopping simulation...")
                self.stopSim()
                print("Timer expired, restarting...")
                sys.exit(1) 

    def checkNewAddress(self, broker):
        # follow public ip changement for mqtt broker
        while True:
            time.sleep(60)
            res = requests.get("http://serviceservice.duck.pictures/mqtt").text
            res = res.replace('"', '')
            if res != broker:
                print("Stopping simulation...")
                self.stopSim()
                print("New address detected, restarting...")
                sys.exit(1)   

    #Called by your MQTT client whenever a new message arrives.
    def notify(self,topic,payload):
        self._message_arrived = True
        data = json.loads(payload)
        print(f"Message received on topic: {topic}, {data}")
        self.logger.info(f"Message received on topic: {topic}, {data}")
        device_id = topic.split('/')[1]
        self.controller(data, device_id)


    #subscribes to sensor topics, connects to broker, waits briefly, then starts the MQTT loop        
    def startSim(self):
        print("connecting mqtt...")
        self.control.mySubscribe(self.topic_sub)
        time.sleep(1)
        self.control.connect()
        time.sleep(15)
        print("Start loop_forever")
        self.control.start()
    
    def stopSim(self):
        self.control.unsubscribe()
        self.control.stop()

    #called whenever a new batch of sensor readings (data) arrives for a particular device (device_id)
    def controller(self, data, device_id):
        publisher = self.topic_pub.replace("device_id", device_id)
        try:
            vase = requests.get(self.resource_catalog + '/vaseByDevice/' + device_id).json()
        except requests.exceptions.ConnectionError:
            self.logger.error("Connection error occurred. Please check the network.")
            return
        except requests.exceptions.RequestException as e:
            self.logger.error(f"A network error occurred: {e}")
            return
    
        # If the device is not configured yet (no vase)
        if not vase:
            self.logger.error(f"Device {device_id} is not configured yet")
            return
        else:
            user_id = vase["user_id"]
            user = requests.get(self.resource_catalog+'/user/'+user_id).json()
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
                    if i['value'] and int(i['value']) < int(vase["plant"]["soil_moisture_min"]):
                        # check if watertank is not empty
                        for c in data['e']:
                            if c['n'] == "watertank_level":
                                if c['value'] and c['value'] >= 10:
                                    self.control.myPublish(publisher+"/"+"water_pump", {"target":1}) # wet the plant
                elif i['n'] == "watertank_level":
                    if i['value'] and int(i['value']) < 20:
                        self.control.myPublish(telegram_chat+"/alert", {"watertank_level": vase['vase_name']})

if __name__ == "__main__":
    r = random.randint(0,1000)
    clientID = "vase_control_smartvase_1010"+str(r)
    logger = CustomerLogger.CustomLogger(service_name)

    try:
        # Get the service catalog
     
        service_catalog = requests.get("http://serviceservice.duck.pictures/all").json()
        
        topicSensors = service_catalog["mqtt_topics"]["topic_sensors"]
        topicActuators = service_catalog["mqtt_topics"]["topic_actuators"]
        topic_telegram_chat = service_catalog["mqtt_topics"]["topic_telegram_chat"]
        resource_catalog = service_catalog["services"]["resource_catalog"]
        broker = service_catalog["mqtt_broker"]["broker_address"]
        port = service_catalog["mqtt_broker"]["port"]

        logger.info(f"Starting service. The parameters are: topicSensors: {str(topicSensors)}, topicActuators: {str(topicActuators)}, topic_telegram_chat: {topic_telegram_chat}, resource_catalog: {resource_catalog}")
        controller = vaseControl(clientID, broker, port, topicSensors, topicActuators, topic_telegram_chat, resource_catalog)
        # thread to check new addres for public ip
        t_addr = threading.Thread(target=controller.checkNewAddress, args=(broker,))
        # thread to restart script to avoid problem with mqtt not receiving message
        ##t_timer = threading.Thread(target=controller.timerRestart)

        t_addr.start()
        ##t_timer.start()

        controller.startSim()

        # if exit the loop_forever
        
        raise RuntimeError

    except Exception as e:
        logger.error("SYSTEM CRASHED AT TIME: "+datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"))
        logger.error("Stopping simulation...")
        controller.stopSim()
        logger.error("ERROR OCCUREDD, DUMPING INFO...")
        path = os.path.abspath('/app/logs/ERROR_vasecontrol.err')
        with open(path, 'a') as file:
            date = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
            file.write(f"Crashed at : {date}")
            file.write(f"Unexpected error: {e}")
        logger.error("EXITING...")
        sys.exit(1)   