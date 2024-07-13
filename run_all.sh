#!/bin/bash

# Check if the virtual environment activation script exists
if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
elif [ -f venv/bin/activate ]; then
  source venv/bin/activate
elif [ -f env/bin/activate ]; then
  source env/bin/activate
elif [ -f .env/bin/activate ]; then
  source .env/bin/activate
else
  echo "Virtual environment activation script not found. Please ensure .venv is set up correctly."
  exit 1
fi

python ./Microservices/catalog_expose/resource_service.py &

python ./Microservices/catalog_expose/service_service.py &

sleep 5

# Traverse the directory and run each Python script
find . \( -path './.venv' -o -path './.env' -o -path './env' -o -path './venv' -o -path './Microservices/device_connector' -o -path './Microservices/catalog_expose' -o -path './TelegramBot' -o -path './ThingSpeak' \) -prune -o -type f -name "*.py" -print  | while read script; do
  echo "Running script: $script"
  python "$script" &
  sleep 2
done

wait

# Deactivate the virtual environment (if activated)
deactivate
