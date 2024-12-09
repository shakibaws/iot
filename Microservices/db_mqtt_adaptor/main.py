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

service_name = "db_mqtt_adaptor"

class Db_Mqtt_Adaptor:
    def __init__(self,clientID,broker,port,topic_sensors, resource_catalog):
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
            res = requests.get("http://serviceservice.duck.pictures/mqtt").text
            res = res.replace('"', '')
            if res != broker:
                print("Stopping simulation...")
                self.stopSim()
                print("New address detected, restarting...")
                sys.exit(1)   

    def notify(self,topic,payload):
        self._message_arrived=True
        try:
            data = json.loads(payload)
            if data['target'] == 1:
                print("target 1 detected")
                # topic -> "smartplant/<device_id>/actuators/<actuator>"
                splitted = topic.split('/')
                device_id = splitted[1]
                actuator = splitted[3]
                print(f"dev_id: {device_id}, actuator: {actuator}")
                self.pusher(device_id, actuator)
        except Exception as e:
            self.logger.error(f"Error on notify: {e}")
            return

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

    def pusher(self, device_id, actuator):
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
            print("vase found")
            # **Endpoint**: `/postData/vaseid/<datatype(ex. water_pump)>`
            url = self.resource_catalog+"/postData/"+str(vase['vase_id'])+"/"+actuator
            print(url)
            # date and time
            dateTimeObj = time.localtime()
            Dyear, Dmonth, Dday, Dhour, Dmin, Dsec = dateTimeObj[:6]  # Extract only the first six elements
            Ddateandtime = "{:02d}/{:02d}/{:4d}-{:02d}:{:02d}"
            datestr = Ddateandtime.format(Dday, Dmonth, Dyear, Dhour, Dmin)

            send_data = {actuator: datestr}
            print(send_data)

            response = requests.post(url, json=send_data)
                    
            if response.status_code == 200:
                print("Post successfull")
                self.logger.info(f"Data sent to firebase for {device_id}: {send_data}")
            else:
                print("Error post")
                self.logger.error(f"Error in sending data to firebase for {device_id}")

if __name__ == '__main__':
    r = random.randint(0,10000)
    clientID = "thingspeak_adaptor_smartvase_1010"+str(r)
    logger = CustomerLogger.CustomLogger(service_name)

    try:
        go = False
        while not go:
            try:
                service_catalog = requests.get("http://serviceservice.duck.pictures/all").json()
                print("Service get")
                go = True
            except requests.exceptions.RequestException as e:
                logger.error(f"Error occurred while making the HTTP request: {e}")
                print(f"Error occurred while making the HTTP request: {e}")
            time.sleep(5)
        
        logger.info("Service catalog received")
        topicActuators = service_catalog["mqtt_topics"]["topic_actuators"]
        resource_catalog = service_catalog["services"]["resource_catalog"]
        broker = service_catalog["mqtt_broker"]["broker_address"]
        port = service_catalog["mqtt_broker"]["port"]
        
        topicActuators = topicActuators.replace("device_id", '+') + "/+"


        logger.info("Starting service...")
        adapter = Db_Mqtt_Adaptor(clientID,broker,port,topicActuators,resource_catalog)
        # thread to check new addres for public ip
        t_addr = threading.Thread(target=adapter.checkNewAddress, args=(broker,))
        # thread to restart script to avoid problem with mqtt not receiving message
        ##t_timer = threading.Thread(target=adapter.timerRestart)

        t_addr.start()
        ##t_timer.start()

        adapter.startSim() # blocking
    
        # if exit the loop_forever
        raise RuntimeError

    except Exception as e:
        logger.error("SYSTEM CRASHED AT TIME: "+datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"))
        logger.error("Stopping simulation...")
        adapter.stopSim()
        logger.error("ERROR OCCUREDD, DUMPING INFO...")
        path = os.path.abspath('/app/logs/ERROR_db_mqtt_adaptor.err')
        with open(path, 'a') as file:
            date = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
            file.write(f"Crashed at : {date}")
            file.write(f"Unexpected error: {e}")
        logger.error("EXITING...")
        sys.exit(1)   
