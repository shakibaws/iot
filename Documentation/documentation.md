# Documentation schema

## ports

## service catalog
- broker
    - broker_address
    - port
- services
    - resource_catalog_address
- topics
    - topic_sensors
    - topic_actuators
    - topic_telegram_chat

## resource catalog
- deviceList
    - device_id
    - vase_id
    - device_name
    - device_status
    - sensors
    - actuators
    - availableServices
    - lastUpdate
    - user_id
- vaseList
    - vase_id
    - vase_name
    - user_id
    - vase_status
    - plant
        - plant_name
        - plant_schedule_water
        - plant_schedule_light
        - soil_moisture_min
        - soil_moisture_max
        - hours_sun_min
        - temperature_min
        - temperature_max
        - description
    - deviceList
    - lastUpdate
- userList
    - user_id
    - user_name
    - user_chat
    - user_vase

## topics

- topic_sensors --> smartplant/+/sensors(+ --> device_id):  
'''json
{
    'vase_id': vase_id,  
    'bn': device_id,  
    'e':  
    [
        {'n': 'temperature', 'value': '', 'timestamp': '', 'unit': 'C'},  
        {'n': 'soil_moisture', 'value': '', 'timestamp': '', 'unit': '%'}  
        {'n': 'light_level', 'value': '', 'timestamp': '', 'unit': 'lumen'}  
    ]  
}
'''
- topic_actuators --> smartplant/device_id/actuators
    - /pump --> {"pump_target": "1"}
    - /light --> {"light_target": "1"}
- topic_telegram_chat --> smartplant/telegram/telegram_chat_id
    - /alert 
        - {"watertank":"low"}
        - {"water":"low"}
        - {"temperature":"low"}
        - {"light":"low"}




## service catalog
- broker: An object containing the broker configuration.
    - broker_address: The address of the MQTT broker.
    - port: The port number to connect to the broker.

- services: An object containing the service configuration.
    - resource_catalog_address: The address of the resource catalog service.

- topics: An object containing the topic configuration.
    - topic_sensors: The MQTT topic for sensor data.
    - topic_actuators: The MQTT topic for actuator commands.
    - topic_telegram_chat: The MQTT topic for Telegram chat messages.

## resource catalog
- deviceList: Represents a list of devices in the system.
    - device_id: The unique identifier of the device.
    - vase_id: The identifier of the vase associated with the device.
    - device_name: The name of the device.
    - device_status: The status of the device (active or disabled).
    - sensors: The list of sensors available in the device.
    - actuators: The list of actuators available in the device.
    - availableServices: The list of available services for the device.
    - lastUpdate: The timestamp of the last update for the device.
    - user_id
- vaseList: Represents a list of vases in the system.
    - vase_id: The unique identifier of the vase.
    - vase_name: The name of the vase.
    - user_id: The user associated with the vase.
    - vase_status: The status of the vase (active or disabled).
    - plant: Represents the plant information associated with the vase.
        - plant_name: The name of the plant.
        - plant_schedule_water: The watering schedule for the plant.
        - plant_schedule_light: The light schedule for the plant.
        - soil_moisture_min: The minimum soil moisture required for the plant.
        - soil_moisture_max: The maximum soil moisture required for the plant.
        - hours_sun_min: The minimum number of hours of sunlight required for the plant.
        - temperature_min: The minimum temperature required for the plant.
        - temperature_max: The maximum temperature required for the plant.
        - description: A brief description of the plant.
    - deviceList: The list of devices associated with the vase.
    - lastUpdate: The timestamp of the last update for the vase.
- userList: Represents a list of users in the system.
    - user_id: The unique identifier of the user.
    - user_name: The name of the user.
    - user_chat: The chat ID of the user (e.g., Telegram chat ID).
    - user_vase: The list of vases associated with the user.