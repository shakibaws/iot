import firebase_admin
from firebase_admin import credentials, db
import json

# Initialize Firebase with the private key
cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://iotvase-default-rtdb.europe-west1.firebasedatabase.app/'
})

# Load the JSON data (replace with your sample file)
data = {
    "resource_catalog": {
        "deviceList": {
            "device1": {
                "device_id": "device1",
                "user_id": "111116871977302905989256955321167310217",
                "device_status": "active",
                "lastUpdate": "2025-02-21 11:00:37",
                "channel_id": 1111111,
                "read_key": "R8ECBTOR4YGZN0N2",
                "write_key": "7OL0R9NAHE2NNR92",
                "actuators": ["light_level", "soil_moisture"],
                "sensors": ["soil_moisture", "watertank_level", "temperature", "light_level"],
                "available_services": ["MQTT"],
                "configurations": [{"watertank_height_cm": 15}]
            }
        },
        "vaseList": {
            "vase1": {
                "vase_id": "257801381876904984820639528779118245491",
                "device_id": "0238402938",
                "user_id": "239391674367824826438604428251723347224",
                "lastUpdate": "2025-02-21 16:02:46",
                "plant": {
                    "plant_name": "Epipremnum aureum",
                    "description": "This plant thrives in bright, indirect light and moderate humidity.",
                    "hours_sun_min": 6,
                    "soil_moisture_min": 20,
                    "soil_moisture_max": 50,
                    "temperature_min": 18,
                    "temperature_max": 29
                }
            }
        },
        "userList": {
            "USER001": {
                "user_id": "239391674367824826438604428251723347224",
                "telegram_chat_id": 480884511,
                "lastUpdate": "2025-02-21 14:41:30"
            }
        },
        "resourceData": {
            "257801381876904984820639528779118245491": {
                "water_pump": {
                    "WDX1": "21/02/2025-16:39",
                    "WDX2": "21/02/2025-16:41"
                }
            }
        }
    },
    "service_catalog": {
        "mqtt_broker": {
            "broker_address": "broker.hivemq.com",
            "broker_websocket": "broker.duck.pictures",
            "port": 1883,
            "port_websocket": 8080
        },
        "mqtt_topics": {
            "topic_actuators": "smartplant/device_id/actuators",
            "topic_sensors": "smartplant/+/sensors",
            "topic_telegram_chat": "smartplant/telegram/telegram_chat_id"
        },
        "services": {
            "chart_service": "http://localhost:5008",
            "data_analysis": "http://localhost:5003",
            "gemini": "http://localhost:5007",
            "resource_catalog": "http://localhost:5002",
            "recommendation_service": "http://localhost:5005",
            "image_recognition": "http://localhost:5006",
            "admin_analytics": "http://localhost:5010",
            "plant_health": "http://localhost:5009"
        }
    }
}

# Upload the data to Firebase
ref = db.reference("/")
ref.set(data)

print("✅ Firebase database populated successfully!")
