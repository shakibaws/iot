import datetime
from MyMQTT import *
import time
import requests
from telegram import Bot
import asyncio
import os
from dotenv import load_dotenv
import sys
import random
import threading
import CustomerLogger

class TelegramNotifier:
    def __init__(self, clientID, broker, port, topic_sub, token):
        self.mqtt = MyMQTT(clientID, broker, port, self)
        self.topic_sub = topic_sub
        self.watertank = {}
        self.light = {}
        self.bot = Bot(token=token)
        self._message_arrived = False
        self.logger = CustomerLogger.CustomLogger("bot_notifier")
        # Create a single event loop for the application
        self.loop = asyncio.new_event_loop()
        # Start a thread that runs the event loop
        self.loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.loop_thread.start()

    def _run_event_loop(self):
        # Set the created loop as the current event loop for this thread
        asyncio.set_event_loop(self.loop)
        # Run the event loop
        self.loop.run_forever()

    def timerRestart(self):
        # check every 5 minutes if a new message has arrived, otherwise restart the service
        while True:
            self._message_arrived = False
            time.sleep(300)
            if not self._message_arrived:
                self.logger.warning("Timer expired, no messages received in 5 minutes, restarting service")
                print("Stopping simulation...")
                self.stopSim()
                print("Timer expired, restarting...")
                sys.exit(1) 

    def checkNewAddress(self, broker):
        # follow public ip changement for mqtt broker
        while True:
            time.sleep(60)
            res = requests.get("http://service_catalog:5001/mqtt").text
            res = res.replace('"', '')
            if res != broker:
                self.logger.warning(f"New MQTT broker address detected: {res} (was: {broker}), restarting service")
                print("Stopping simulation...")
                self.stopSim()
                print("New address detected, restarting...")
                sys.exit(1)   
        
    def notify(self, topic, payload):
        self._message_arrived = True
        data = json.loads(payload)
        self.logger.info(f"Message received on topic: {topic}, data: {data}")
        # "topic_sensors": "smartplant/+/sensors",
        # "topic_actuators": "smartplant/device_id/actuators"
        telegram_chat = topic.split('/')[2]
        
        # Instead of asyncio.run, use the existing event loop
        asyncio.run_coroutine_threadsafe(self.notifier(data, telegram_chat), self.loop)

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
                        await self.bot.send_message(chat_id=telegram_chat, text=f"Watertank almost empty of vase {name}")
                        self.logger.info(f"Sent watertank alert to chat {telegram_chat} for vase {name}")
                        # Update the last notification time to now
                        self.watertank[telegram_chat]['date'] = current_time
            else:
                # If no previous notification date, send the message and store the time
                await self.bot.send_message(chat_id=telegram_chat, text=f"Watertank almost empty of vase {name}")
                self.logger.info(f"Sent initial watertank alert to chat {telegram_chat} for vase {name}")
                # Set the last notification time
                self.watertank[telegram_chat] = {'date': datetime.datetime.now()}
        elif data.get("light"):
            name = data["light"]
            if self.light.get(telegram_chat, {}):
                last_notified_time = self.light[telegram_chat].get('date')
                if isinstance(last_notified_time, datetime.datetime):
                    current_time = datetime.datetime.now()
                    time_difference = current_time - last_notified_time
                    if time_difference.total_seconds() > 2 * 60 * 60:
                        await self.bot.send_message(chat_id=telegram_chat, text=f"Low light for vase {name}")
                        self.logger.info(f"Sent low light alert to chat {telegram_chat} for vase {name}")
                        self.light[telegram_chat]['date'] = current_time
            else:
                await self.bot.send_message(chat_id=telegram_chat, text=f"Low light for vase {name}")
                self.logger.info(f"Sent initial low light alert to chat {telegram_chat} for vase {name}")
                self.light[telegram_chat] = {'date': datetime.datetime.now()}
        else:
            self.logger.warning(f"Unknown sensor data received: {data}")

    def startSim(self):
        self.logger.info("Starting bot notifier service")
        print("connecting mqtt...")
        self.mqtt.connect()
        time.sleep(1)
        self.logger.info(f"Subscribing to topic: {self.topic_sub}")
        print(f"Subscribing to : {self.topic_sub}")
        self.mqtt.mySubscribe(self.topic_sub)
        time.sleep(1)
        self.logger.info("Starting MQTT loop")
        print("Start loop_forever")
        self.mqtt.start()
    
    def stopSim(self):
        self.logger.info("Stopping bot notifier service")
        self.mqtt.unsubscribe()
        self.mqtt.stop()
        # Stop the event loop properly
        if hasattr(self, 'loop') and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        # Wait for the loop thread to finish
        if hasattr(self, 'loop_thread') and self.loop_thread.is_alive():
            self.loop_thread.join(timeout=1.0)

if __name__ == "__main__":
    r = random.randint(0,1000)
    clientID = "bot_notifier_smartvase_1010"+str(r)

    try:
        load_dotenv()

        TOKEN = os.getenv("TOKEN")

        if not TOKEN:
            raise ValueError("TOKEN is missing from environment variables")
        
        # Initialize logger for main section
        logger = CustomerLogger.CustomLogger("bot_notifier")
        logger.info("Bot notifier service starting up")


        #get al service_catalog
        service_catalog = requests.get("http://service_catalog:5001/all").json()
        logger.info("Service catalog retrieved successfully")

        broker = service_catalog["mqtt_broker"]["broker_address"]
        port = service_catalog["mqtt_broker"]["port"]
        topic_sub = service_catalog['mqtt_topics']['topic_telegram_chat']
        token = TOKEN

        logger.info(f"Initializing bot notifier with broker: {broker}:{port}, topic: {topic_sub}")
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
        print("ERROR OCCUREDD, DUMPING INFO...")
        path = os.path.abspath('./logs/ERROR_botnotifier.err')
        with open(path, 'a') as file:
            date = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
            file.write(f"Crashed at : {date}")
            file.write(f"Unexpected error: {e}")
        print (e)
        print("EXITING...")
        sys.exit(1)   

    