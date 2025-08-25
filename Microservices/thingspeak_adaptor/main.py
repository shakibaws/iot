import datetime
from MyMQTT import *
import time
import requests
import CustomerLogger
import random
import os
import sys
import asyncio
import threading

service_name = "thingspeak_adaptor"

class ThingspeakAdaptor:
    def __init__(self,clientID,broker,port,topic_sensors,resource_catalog):
        self.adapter = MyMQTT(clientID,broker,port,self)
        self.topic_sub = topic_sensors
        self.resource_catalog = resource_catalog
        self.logger = CustomerLogger.CustomLogger(service_name, "user_id_test")
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
            res = requests.get("http://localhost:5001/mqtt").text
            res = res.replace('"', '')
            if res != broker:
                print("Stopping simulation...")
                self.stopSim()
                print("New address detected, restarting...")
                sys.exit(1)   

    def notify(self,topic,payload):
        self._message_arrived=True
        data = json.loads(payload)
        # "topic_sensors": "smartplant/+/sensors",
        # "topic_actuators": "smartplant/device_id/actuators"
        splitted = topic.split('/')
        if len(splitted) < 3:
            return
        device_id = splitted[1]
        flag = splitted[2]
        name = None
        if len(splitted) > 3 :
            name = splitted[3]
        self.speaker(data, device_id, flag, name)
        time.sleep(15)

    def startSim(self):
        print("connecting mqtt...")
        self.adapter.mySubscribe(self.topic_sub)
        time.sleep(1)
        self.adapter.connect()
        time.sleep(15)
        print("Start loop_forever")
        self.adapter.start()

    
    def stopSim(self):
        self.adapter.unsubscribe()
        self.adapter.stop()

    def speaker(self, data, device_id, flag, actuator_name):
        device = requests.get(self.resource_catalog+'/device/'+device_id).json()
        try:
            vase = requests.get(self.resource_catalog + '/vaseByDevice/' + device_id).json()
        except requests.exceptions.ConnectionError:
            self.logger.error("Connection error occurred. Please check the network.")
            return
        except requests.exceptions.RequestException as e:
            self.logger.error(f"A network error occurred: {e}")
            return        
        self.logger.info(f"Analyzing data from {device_id}")
    
        # If the device is not configured yet (no vase)
        if not vase:
            self.logger.info(f"Device {device_id} is not configured yet")
            return 
        else:
            write_key = device["write_key"]
            url = "https://api.thingspeak.com/update.json"
            
            send_data = {}
            send_data['api_key'] =  write_key  

            if flag == "sensors":
                for i in data['e']:    
                    if i['n'] == 'light_level':
                        send_data["field3"]=i['value']
                    elif i['n'] == "temperature":
                        send_data["field1"]=i['value']
                    elif i['n'] == "soil_moisture":
                        send_data["field2"]=i['value']
                    elif i['n'] == "watertank_level":
                        send_data["field4"]=i['value']
            """ elif flag == "actuators":
                
                if actuator_name == "water_pump":
                    send_data["field5"]=1
                else:
                    self.logger.error(f"{actuator_name} doesn't exist") """

            response = requests.post(url, data=send_data)

            if response.status_code == 200:
                self.logger.info(f"Data sent to ThingSpeak for {device_id}: {send_data}")
            else:
                self.logger.error(f"Error in sending data to ThingSpeak for {device_id}")

if __name__ == '__main__':
    r = random.randint(0,10000)
    clientID = "thingspeak_adaptor_smartvase_1010"+str(r)
    logger = CustomerLogger.CustomLogger(service_name)

    try:
        go = False
        while not go:
            try:
                service_catalog = requests.get("http://localhost:5001/all").json()
                print("Service get")
                go = True
            except requests.exceptions.RequestException as e:
                logger.error(f"Error occurred while making the HTTP request: {e}")
                print(f"Error occurred while making the HTTP request: {e}")
            time.sleep(5)
        
        logger.info("Service catalog received")
        topicSensors = service_catalog["mqtt_topics"]["topic_sensors"]
        resource_catalog = service_catalog["services"]["resource_catalog"]
        broker = service_catalog["mqtt_broker"]["broker_address"]
        port = service_catalog["mqtt_broker"]["port"]
        
        logger.info("Starting service...")
        adapter = ThingspeakAdaptor(clientID,broker,port,topicSensors,resource_catalog)
        # thread to check new addres for public ip
        t_addr = threading.Thread(target=adapter.checkNewAddress, args=(broker,))
       
        t_addr.start()

        adapter.startSim() # blocking
    
        # if exit the loop_forever
        raise RuntimeError

    except Exception as e:
        logger.error("SYSTEM CRASHED AT TIME: "+datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"))
        logger.error("Stopping simulation...")
        adapter.stopSim()
        logger.error("ERROR OCCUREDD, DUMPING INFO...")
        path = os.path.abspath('./logs/ERROR_thingspeakadaptor.err')
        with open(path, 'a') as file:
            date = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
            file.write(f"Crashed at : {date}")
            file.write(f"Unexpected error: {e}")
        print(e)
        logger.error("EXITING...")
        sys.exit(1)   
