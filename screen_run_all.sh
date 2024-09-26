#!/bin/bash

pkill screen

screen -S resource_catalog -dm bash -c 'source venv/bin/activate; python Microservices/catalog_expose/resource_service.py'

screen -S service_catalog -dm bash -c 'source venv/bin/activate; python Microservices/catalog_expose/service_service.py'

screen -S telegram_bot -dm bash -c 'source venv/bin/activate; python TelegramBot/bot.py'

sleep 4

screen -S gemini -dm bash -c 'source venv/bin/activate; python Microservices/gemini/main.py'

screen -S recommendation_service -dm bash -c 'source venv/bin/activate; python Microservices/recommendation_service/main.py'

screen -S vase_control -dm bash -c 'source venv/bin/activate; python Microservices/vase_control/main.py'

screen -S image_recognition -dm bash -c 'source venv/bin/activate; python Microservices/image_recognition/main.py'

screen -S thingspeak_adaptor -dm bash -c 'source venv/bin/activate; python Microservices/ThingSpeak_adaptor/main.py'

wait
