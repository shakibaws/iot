# SCRIPT TO UPDATE BROKER ADDRESS FOLLOWING PUBLIC IP ADDRESS CHANGEMENT
import time
import requests
while True:
    try:
        time.sleep(60)
        res = requests.get("http://ifconfig.me").text
        print(res)
        requests.post("https://serviceservice.duck.pictures/publicip", json={'publicip': res})
    except Exception as e:
        print(e)
        pass