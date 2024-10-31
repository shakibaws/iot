
import datetime
import json
import requests

LOKI_ENDPOINT = "http://loki:3100/loki/api/v1/push"

def #log_to_loki(level, message, service_name="plant_api_service", user_id=None, request_id=None):
    headers = {
        'Content-Type': 'application/json'
    }
    labels = f'{{service="{service_name}", level="{level}"'
    if user_id:
        labels += f', user_id="{user_id}"'
    if request_id:
        labels += f', request_id="{request_id}"'
    labels += '}'
    
    log_entry = {
        "streams": [
            {
                "labels": labels,
                "entries": [
                    {
                        "ts": datetime.datetime.utcnow().isoformat() + "Z",
                        "line": message
                    }
                ]
            }
        ]
    }
    try:
        response = requests.post(LOKI_ENDPOINT, data=json.dumps(log_entry), headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to send log to Loki: {e}")
