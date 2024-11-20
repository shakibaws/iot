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

class TelegramNotifier:
    def __init__(self,clientID,broker,port,topic_sub, token):
        self.mqtt = MyMQTT(clientID,broker,port,self)
        self.topic_sub = topic_sub
        self.watertank = {}
        self.bot = Bot(token=token)
        
    def notify(self,topic,payload):
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
        self.mqtt.start()
        self.mqtt.mySubscribe(self.topic_sub)
    
    def stopSim(self):
        self.mqtt.unsubscribe()
        self.mqtt.stop()


def main():
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
        bot_notification.startSim()

        try:
            while True:        
                time.sleep(10)
        except KeyboardInterrupt:
                bot_notification.stopSim()

    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        restart_script()
    except Exception as e:
        print(f"Unexpected error: {e}")
        restart_script()

def restart_script():
    """Restart the script from scratch."""
    print("Restarting script...")
    python = sys.executable
    os.execl(python, python, *sys.argv)

if __name__ == "__main__":
    main()

    