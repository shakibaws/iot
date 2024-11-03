#!/bin/bash

pkill screen

screen -S resource_catalog -dm bash -c 'source venv/bin/activate; cd Microservices/catalog_expose; python ./resource_service_firebase.py'

screen -S service_catalog -dm bash -c 'source venv/bin/activate; cd Microservices/catalog_expose; python ./service_service_firebase.py'

screen -S telegram_bot -dm bash -c 'source venv/bin/activate; python TelegramBot/bot_async.py'

sleep 4

screen -S gemini -dm bash -c 'source venv/bin/activate; cd Microservices/gemini; python ./main.py'

screen -S recommendation_service -dm bash -c 'source venv/bin/activate; cd Microservices/recommendation_service; python ./main_async.py'

screen -S vase_control -dm bash -c 'source venv/bin/activate; cd Microservices/vase_control; python ./main.py'

screen -S image_recognition -dm bash -c 'source venv/bin/activate; cd Microservices/image_recognition; python ./main.py'

screen -S thingspeak_adaptor -dm bash -c 'source venv/bin/activate; cd Microservices/ThingSpeak_adaptor; python ./main.py'

screen -S chart_service -dm bash -c 'source venv/bin/activate; cd Microservices/chart_service; python ./main_plot.py'

screen -S data_analysis -dm bash -c 'source venv/bin/activate; cd Microservices/data_analysis; python ./main.py'

screen -S telegram_bot_notifier -dm bash -c 'source venv/bin/activate; cd TelegramBot; python ./bot_notifier.py'

#screen -S log_esp32 -dm bash -c 'stty -F /dev/ttyUSB0 raw 115200; cat /dev/ttyUSB0 > log_esp32.txt'

wait
