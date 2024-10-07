import datetime
from MyMQTT import *
import time
import requests
from telegram import Bot

class TelegramNotifier:
    def __init__(self,clientID,broker,port,topic_sub, token):
        self.control = MyMQTT(clientID,broker,port,self)
        self.topic_sub = topic_sub
        self.watertank = {}
        self.bot = Bot(token=token)
        
    def notify(self,topic,payload):
        data = json.loads(payload)
        print(f"Message received on topic: {topic}, {data}")
        # "topic_sensors": "smartplant/+/sensors",
        # "topic_actuators": "smartplant/device_id/actuators"
        telegram_chat = topic.split('/')[2]
        self.notifier(data, telegram_chat)

    def notifier(self, data, telegram_chat):
        if data.get("watertank_level"):  # Check if watertank_level is present and non-empty
            if self.watertank[telegram_chat]:
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
                        self.bot.send_message(chat_id=telegram_chat, text="Watertank almost empty")
                        # Update the last notification time to now
                        self.watertank['telegram_chat']['date'] = current_time
            else:
                # If no previous notification date, send the message and store the time
                self.bot.send_message(chat_id=telegram_chat, text="Watertank almost empty")
                # Set the last notification time
                self.watertank[telegram_chat] = {'date': datetime.datetime.now()}
        
    def startSim(self):
        self.control.start()
        self.control.mySubscribe(self.topic_sub)
    
    def stopSim(self):
        self.control.unsubscribe()
        self.control.stop()

    
if __name__ == "__main__":

    clientID = "vase_control"

    #get al service_catalog
    service_catalog = requests.get("http://serviceservice.duck.pictures/all").json()

    broker = service_catalog["broker"]["broker_address"]
    port = service_catalog["broker"]["port"]
    topic_sub = service_catalog['topics']['topic_telegram_chat']
    token = service_catalog['telegram_bot']['token']

    controller = TelegramNotifier(clientID,broker,port,topic_sub, token)
    controller.startSim()

    try:
        while True:        
            time.sleep(10)
    except KeyboardInterrupt:
            controller.stopSim()
    