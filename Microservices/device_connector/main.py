from wlan_connect import Connector
from simple_mqtt import myMqtt
import utime
import time
import urequests
import ujson
import machine
import onewire, ds18x20
import random
import dht
    

class IoTDevice:
    def __init__(self):

        ##
        ### board init
        #machine.freq(240000000, min_freq=10000000)
        print(machine.freq())
        ##

        self.go = False
        self.pin_sensors = {}
        self.pin_actuators = {}
        self.device_cfg = {}
        self.service_catalog = {}
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
        def _measure_perc(trigger, echo):
            try:
                # Ensure trigger and echo are valid objects
                if not hasattr(trigger, 'on') or not hasattr(trigger, 'off'):
                    raise ValueError("Invalid trigger object. Ensure it has 'on' and 'off' methods.")
                if not hasattr(echo, 'value'):
                    raise ValueError("Invalid echo object. Ensure it has a 'value' method or property.")

                # Get the max height from the configuration
                max_height = None
                configurations = self.device_cfg.get("device", {}).get("configurations", [])
                for config in configurations:
                    if "watertank_height_cm" in config:
                        max_height = config["watertank_height_cm"]
                        break
                    #for future adds of other configurations 
                if max_height is None:
                    raise ValueError("Max height not configured in 'device_cfg'.")
                if not isinstance(max_height, (int, float)) or max_height <= 0:
                    raise ValueError("Max height must be a positive number.")

                # Send a 10µs pulse to the trigger pin
                trigger.off()
                time.sleep_us(2)
                trigger.on()
                time.sleep_us(10)
                trigger.off()

                # Measure the time the echo pin is HIGH
                duration = machine.time_pulse_us(echo, 1, 30000)  # Timeout after 30ms
                if duration < 0:
                    print("Out of range: No echo received or object too far.")
                    return None

                # Calculate the distance in cm
                distance = (duration * 0.0343) / 2
                if distance > max_height:
                    print(f"Measured distance ({distance} cm) exceeds max height ({max_height} cm).")
                    return None

                # Calculate the percentage based on max height
                percentage = (distance / max_height) * 100

                # Return as an integer percentage
                return int(percentage)
            except ValueError as e:
                print(f"Error: {e}")
                return None
            except Exception as e:
                print(f"Unexpected error: {e}")
                return None


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
                value = _measure_perc(p[0]["out"], p[1]["in"])
            else:
                stock["unit"] = 'N/D'
                value = p.read()
            stock['value']=value
            message["e"].append(stock)

        self.mqqtclient.publishJson(self.pub_topic, message)

    def init(self):

        ### try to connect to wifi
        status = self.c.connect()
        while not status:
            print("Connection problem")
            time.sleep(5)
            status = self.c.connect()

        ### if first boot get/post on resource catalog
        if machine.reset_cause() == machine.DEEPSLEEP_RESET:
            # deepsleep
            ### read from file local copy
            with open("config.json", "r") as file:
                self.device_cfg = ujson.load(file)
            with open("service_catalog.json", "r") as file:
                self.service_catalog = ujson.load(file)
        else:
            # hard reset | first boot
            ### try to get service catalog
            while True:
                try:
                    print("GET service catalog")
                    res = urequests.get(self.service_catalog_url)
                    self.service_catalog = ujson.loads(res.text)
                    with open("service_catalog.json", 'w+') as file:
                        ujson.dump(self.service_catalog, file)
                    break
                except OSError as e:
                    print(f"Error {e}. Retrying in 5 seconds...")
                    time.sleep(5)
            ##

            ### subscribe new device(post) to resource catalog
            user_id = ""
            with open("user_id.dat", "r") as file:
                user_id = file.read()
            with open("config.json", "r") as file:
                self.device_cfg = ujson.load(file)
                self.device_cfg["device"]["user_id"] = user_id
                file.close()
                resource_catalog_url = self.service_catalog["services"]["resource_catalog"]
                retries = 5
                for attempt in range(retries):
                    try:
                        print("POST resource catalog")
                        res = urequests.post(resource_catalog_url+"/device", json=self.device_cfg["device"])
                        break
                    except OSError as e:
                        if attempt < retries - 1:
                            print(f"Error {e}. Retrying in 5 seconds...")
                            time.sleep(5)
                        else:
                            raise
            ##

        #### set pinout
        print("Setting pinout")
        for i in self.device_cfg["pinout"]["sensors"]:
            if i['name'] == 'temperature':
                # DS18B20 dallas sensor
                ds_pin = machine.Pin(i['pin'])
                ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
                roms = ds_sensor.scan()
                print('Found DS devices: ', roms)
                if roms:
                    self.pin_sensors[i['name']] = {'rom': roms[0], 'ds_sensor': ds_sensor}
            elif i['name'] == 'watertank_level':
                pin_out = machine.Pin(i['pin'][1], machine.Pin.OUT)
                pin_in = machine.Pin(i['pin'][0], machine.Pin.IN)
                self.pin_sensors[i['name']] = [{"out": pin_out},{"in" : pin_in}]
            else:
                adc = machine.ADC(machine.Pin(i['pin']))
                adc.atten(machine.ADC.ATTN_11DB)
                self.pin_sensors[i['name']] = adc
        
        for i in self.device_cfg["pinout"]["actuators"]:
            self.pin_actuators[i['name']] = machine.Pin(i['pin'], machine.Pin.OUT)
        ##
        
        #### connect to mqtt
        print("Connecting mqtt")
        client_id = f"device_connector_{self.device_cfg['device']['device_id']}"
        broker = self.service_catalog["mqtt_broker"]["broker_address"]
        port = self.service_catalog["mqtt_broker"]["port"]
        self.pub_topic = self.service_catalog["mqtt_topics"]["topic_sensors"]
        self.pub_topic = self.pub_topic.replace("+", self.device_cfg["device"]["device_id"])
        self.sub_topic = self.service_catalog["mqtt_topics"]["topic_actuators"]
        self.sub_topic = self.sub_topic.replace("device_id", self.device_cfg["device"]["device_id"]) + "/+"
        self.mqqtclient = myMqtt(client_id, broker, port, self.actuate)
        self.mqqtclient.connect()
        time.sleep(2)
        self.mqqtclient.subscribe(self.sub_topic)
        ##

        machine.freq(80000000)
        print(machine.freq())
        self.go = True

    def loop(self):
        # not really a loop
        while True:
            if not self.c.isconnected():  # if connection goes down
                for i in range(5):
                    if not self.c.isconnected():
                        self.c.connect()
                        time.sleep(20)
                self.init()
            # take sensor input and publish
            self.get_sensor()
            time.sleep(2)
            # Non-blocking wait for message
            self.mqqtclient.check_message()
            time.sleep(3) # let some time to actuate the message

            # set RTC.ALARM0 to fire after 60 seconds (waking the device)
            # put the device to sleep
            print("RTC timer set for 60 seconds")
            print("Entering deep sleep...")
            machine.deepsleep(60000)


    def deinit(self):
        self.go = False
        self.mqqtclient.disconnect()
        
    def run(self):
        self.init()
        self.loop()

device = IoTDevice()
try:
    device.run()
except Exception as e:
    # dumping exception to file
    with open("crash_dump.err", 'w')as file:
        file.write(f"ERROR ON DEVICE.RUN: {e}")
    machine.reset() # hard reset
