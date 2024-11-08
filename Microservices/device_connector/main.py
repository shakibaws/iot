from wlan_connect import Connector
from simple_mqtt import myMqtt
import utime
import time
import urequests
import ujson
from machine import Pin, ADC
import onewire, ds18x20
import random
import dht

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
            time.sleep(30)  # wait for water to flow
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
            stock = {'n': name, 'value': 0, 'timestamp': '', 'unit': ''}
            value = 0
            if name == "temperature":
                #stock["value"] = random.randint(15,30) # random value(to be removed)
                stock["unit"] = 'C'
                p['ds_sensor'].convert_temp()
                time.sleep(1)
                value = p['ds_sensor'].read_temp(p['rom'])
            elif name == "soil_moisture":
                #stock["value"] = random.randint(10,90) # random value(to be removed)
                #lower is the value wetter is the soil
                stock["unit"] = '%'
                value = (1-(p.read()/4095))*100
            elif name == "light_level":
                #stock["value"] = random.randint(100,1000) # random value(to be removed)
                stock["unit"] = 'lux'
                value = p.read()/4095*1000
            elif name == "watertank_level":
                #stock["value"] = random.randint(0,100) # random value(to be removed)
                stock["unit"] = '%'
                value = p.read()/4095*100
            else:
                stock["unit"] = 'N/D'
                value = p.read()
            stock['value']=value
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
            resource_catalog = service_catalog["services"]["resource_catalog"]
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
            if i['name'] == 'temperature':
                # DS18B20 dallas sensor
                ds_pin = Pin(i['pin'])
                ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
                roms = ds_sensor.scan()
                print('Found DS devices: ', roms)
                if roms:
                    self.pin_sensors[i['name']] = {'rom': roms[0], 'ds_sensor': ds_sensor}
            else:
                adc = ADC(Pin(i['pin']))
                adc.atten(ADC.ATTN_11DB)
                self.pin_sensors[i['name']] = adc
        
        for i in self.device_cfg["pinout"]["actuators"]:
            self.pin_actuators[i['name']] = Pin(i['pin'], Pin.OUT)
        
        # connect to mqtt
        broker = service_catalog["mqtt_broker"]["broker_address"]
        port = service_catalog["mqtt_broker"]["port"]

        self.pub_topic = service_catalog["mqtt_topics"]["topic_sensors"]
        self.pub_topic = self.pub_topic.replace("+", self.device_cfg["device"]["device_id"])
        
        self.sub_topic = service_catalog["mqtt_topics"]["topic_actuators"]
        self.sub_topic = self.sub_topic.replace("device_id", self.device_cfg["device"]["device_id"]) + "/+"

        topic_telegram_chat = service_catalog["mqtt_topics"]["topic_telegram_chat"]

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
