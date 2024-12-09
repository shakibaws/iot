import datetime
from MyMQTT import *
import time
import requests
from telegram import Bot
import asyncio  # Import asyncio to use async functionality
import os
from dotenv import load_dotenv
import sys
import random
import threading

class TelegramNotifier:
    def __init__(self,clientID,broker,port,topic_sub, token):
        self.mqtt = MyMQTT(clientID,broker,port,self)
        self.topic_sub = topic_sub
        self.watertank = {}
        self.bot = Bot(token=token)
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
        self._message_arrived = True
        data = json.loads(payload)
        print(f"Message received on topic: {topic}, {data}")
        # "topic_sensors": "smartplant/+/sensors",
        # "topic_actuators": "smartplant/device_id/actuators"
        telegram_chat = topic.split('/')[2]
        asyncio.run(self.notifier(data, telegram_chat))

    async def notifier(self, data, telegram_chat):
        if data.get("watertank_level"):  # Check if watertank_level is present and non-empty
            name = data['watertank_level']
            if self.watertank.get(telegram_chat, {}):
                last_notified_time = self.watertank[telegram_chat].get('date')
                # Parse or make sure 'date' is a datetime object
                if isinstance(last_notified_time, datetime.datetime):
                    # Get the current time
                    current_time = datetime.datetime.now()
                    # Calculate the time difference
                    time_difference = current_time - last_notified_time
                    # Check if more than 2 hours have passed
                    if time_difference.total_seconds() > 2 * 60 * 60:
                        # Send the message if more than 2 hours have passed
                        self.bot.send_message(chat_id=telegram_chat, text=f"Watertank almost empty of vase {name}")
                        # Update the last notification time to now
                        self.watertank['telegram_chat']['date'] = current_time
            else:
                # If no previous notification date, send the message and store the time
                await self.bot.send_message(chat_id=telegram_chat, text=f"Watertank almost empty of vase {name}")
                # Set the last notification time
                self.watertank[telegram_chat] = {'date': datetime.datetime.now()}
        
    def startSim(self):
        print("connecting mqtt...")
        self.mqtt.connect()
        time.sleep(1)
        print(f"Subscribing to : {self.topic_sub}")
        self.mqtt.mySubscribe(self.topic_sub)
        time.sleep(1)
        print("Start loop_forever")
        self.mqtt.start()
    
    def stopSim(self):
        self.mqtt.unsubscribe()
        self.mqtt.stop()


if __name__ == "__main__":
    r = random.randint(0,1000)
    clientID = "bot_notifier_smartvase_1010"+str(r)

    try:
        load_dotenv()

        TOKEN = os.getenv("TOKEN")

        if not TOKEN:
            #log_to_loki("info", "POST request received", service_name=service_name, user_id=user_id, request_id=request_id)
            raise ValueError("TOKEN is missing from environment variables")


        #get al service_catalog
        service_catalog = requests.get("http://serviceservice.duck.pictures/all").json()

        broker = service_catalog["mqtt_broker"]["broker_address"]
        port = service_catalog["mqtt_broker"]["port"]
        topic_sub = service_catalog['mqtt_topics']['topic_telegram_chat']
        token = TOKEN

        bot_notification = TelegramNotifier(clientID,broker,port,str(topic_sub).replace('telegram_chat_id', '+')+'/alert', token)
        # thread to check new addres for public ip
        t_addr = threading.Thread(target=bot_notification.checkNewAddress, args=(broker,))
        # thread to restart script to avoid problem with mqtt not receiving message
        #t_timer = threading.Thread(target=bot_notification.timerRestart)

        t_addr.start()
        #t_timer.start()

        bot_notification.startSim() # blocking
        
        # if exit the loop_forever
        raise RuntimeError

    except Exception as e:
        print("Stopping simulation...")
        bot_notification.stopSim()
        print("ERROR OCCUREDD, DUMPING INFO...")
        path = os.path.abspath('/app/logs/ERROR_botnotifier.err')
        with open(path, 'a') as file:
            date = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
            file.write(f"Crashed at : {date}")
            file.write(f"Unexpected error: {e}")
        print("EXITING...")
        sys.exit(1)   

    