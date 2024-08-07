from wlan_connect import Connector
from simple_mqtt import myMqtt
import utime
import time
import urequests
import ujson
from machine import Pin, ADC

class IoTDevice:
    def __init__(self):
        self.go = False
        self.pin_sensors = {}
        self.pin_actuators = {}
        self.device_cfg = {}
        self.mqqtclient = None
        self.sub_topic = ""
        self.pub_topic = ""

        self.service_catalog_url = "http://serviceservice.duck.pictures/all"

        self.c = Connector()

    def actuate(self, topic, msg):
        # check update packet
        if "update" in topic:
            new_cfg = ujson.loads(msg)
            with open("config.json", "w") as file:
                self.device_cfg["device"] = new_cfg
                ujson.dump(self.device_cfg, file)
                file.close()
                self.deinit()

        # check what to actuate(topic) and how(json msg)
        actuator = topic.split("/")[3]
        command = ujson.loads(msg)["target"]
        if actuator == "soil_moisture":
            self.pin_actuators[actuator].value(command)  # activate pump for 2 seconds
            time.sleep(2)
            self.pin_actuators[actuator].value(0)
            time.sleep(10)  # wait for water to flow
        else:
            self.pin_actuators[actuator].value(command)

    def get_sensor(self):
        """ 
        {
            'bn': device_id,
            'e':
            [
                {'n': 'temperature', 'value': '', 'timestamp': '', 'unit': 'C'},
                {'n': 'soil_moisture', 'value': '', 'timestamp': '', 'unit': '%'}
                {'n': 'light_level', 'value': '', 'timestamp': '', 'unit': 'lumen'},
                {'n': 'watertank_level', 'value': '', 'timestamp': '', 'unit': '%'}
            ]
        } 
        """
        message = {
            'bn': self.device_cfg["device"]["device_id"],
            'e': []
        }
        for name, p in self.pin_sensors.items():
            value = p.read()
            stock = {'n': name, 'value': value, 'timestamp': '', 'unit': ''}
            if name == "temperature":
                stock["unit"] = 'C'
            elif name == "soil_moisture":
                stock["unit"] = '%'
            elif name == "light_level":
                stock["unit"] = 'lumen'
            elif name == "watertank_level":
                stock["unit"] = '%'
            else:
                stock["unit"] = 'N/D'
            message["e"].append(stock)

        self.mqqtclient.publishJson(self.pub_topic, message)

    def setup(self):
        status = self.c.connect()
        while not status:
            print("Connection problem")
            time.sleep(2)
            status = self.c.connect()

    def init(self):
        # fetch service catalog
        client_id = "device_connector"
        retries = 5
        for attempt in range(retries):
            try:
                res = urequests.get(self.service_catalog_url)
                service_catalog = ujson.loads(res.text)
                break
            except OSError as e:
                if attempt < retries - 1:
                    print(f"Error {e}. Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    raise

        # sub(post) to resource catalog
        user_id = ""
        with open("user_id.dat", "r") as file:
            user_id = file.read()
        file.close()

        with open("config.json", "r") as file:
            self.device_cfg = ujson.load(file)
            self.device_cfg["device"]["user_id"] = user_id
            file.close()
            resource_catalog = service_catalog["services"]["resource_catalog_address"]
            print(resource_catalog)
            retries = 5
            for attempt in range(retries):
                try:
                    res = urequests.post(resource_catalog+"/device", json=self.device_cfg["device"])
                    break
                except OSError as e:
                    if attempt < retries - 1:
                        print(f"Error {e}. Retrying in 5 seconds...")
                        time.sleep(5)
                    else:
                        raise
        file.close()
        # set pinout
        for i in self.device_cfg["pinout"]["sensors"]:
            self.pin_sensors[i['name']] = ADC(Pin(i['pin']))
        
        for i in self.device_cfg["pinout"]["actuators"]:
            self.pin_actuators[i['name']] = Pin(i['pin'], Pin.OUT)
        
        # connect to mqtt
        broker = service_catalog["broker"]["broker_address"]
        port = service_catalog["broker"]["port"]

        self.pub_topic = service_catalog["topics"]["topic_sensors"]
        self.pub_topic = self.pub_topic.replace("+", self.device_cfg["device"]["device_id"])
        
        self.sub_topic = service_catalog["topics"]["topic_actuators"]
        self.sub_topic = self.sub_topic.replace("device_id", self.device_cfg["device"]["device_id"]) + "/+"

        topic_telegram_chat = service_catalog["topics"]["topic_telegram_chat"]

        self.mqqtclient = myMqtt(client_id, broker, port, self.actuate)
        self.mqqtclient.connect()
        time.sleep(1)
        self.mqqtclient.subscribe(self.sub_topic)

        self.go = True

    def loop(self):
        while True:
            while self.go:
                if not self.c.isconnected():  # if connection goes down, try again to connect
                    self.c.connect()
                
                # take sensor input and publish
                self.get_sensor()
                time.sleep(5)
                # Non-blocking wait for message
                self.mqqtclient.check_message()
                time.sleep(10)
            self.init()

    def deinit(self):
        self.go = False
        self.mqqtclient.disconnect()
        
    def run(self):
        self.setup()
        self.loop()

device = IoTDevice()
device.run()
