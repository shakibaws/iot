#!/bin/bash

# Activate the virtual environment (if needed)
# source .venv/bin/activate

python ./Microservices/catalog_expose/resource_service.py &

python ./Microservices/catalog_expose/service_service.py &

sleep 5

# Traverse the directory and run each Python script
find . \( -path './.venv' -o -path './Microservices/device_connector' -o -path './Microservices/catalog_expose' -o -path './TelegramBot' -o -path './ThingSpeak' \) -prune -o -type f -name "*.py" -print  | while read script; do
  echo "Running script: $script"
  python "$script" &
  sleep 2
done

while true; do
  sleep 1
  echo '.'
done

# Deactivate the virtual environment (if activated)
# deactivate