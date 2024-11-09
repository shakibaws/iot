# DOCUMENTATION

## MICROSERVICES

---

### 0. **Resource Catalog**
local port -> :5000  
public endpoint = 'http://resourceservice.duck.pictures'  
### **API**:

**GET Requests**

1. **List all devices**
   - **Endpoint**: `/listDevice`
   - **Response**: 
     ```json
     [
       { "device_id": "...", "user_id": "...", "device_status": "active", ... },
       ...
     ]
     ```

2. **List all vases**
   - **Endpoint**: `/listVase`
   - **Response**:
     ```json
     [
       { "vase_id": "...", "plant": {}.. },
       ...
     ]
     ```

3. **List all users**
   - **Endpoint**: `/listUser`
   - **Response**:
     ```json
     [
       { "user_id": "...", "telegram_chat_id": "...", ... },
       ...
     ]
     ```

4. **List devices by user**
   - **Endpoint**: `/listDeviceByUser/{user_id}`
   - **Response**:
     ```json
     [
       { "device_id": "...", "user_id": "...", ... },
       ...
     ]
     ```

5. **List vases by user**
   - **Endpoint**: `/listVaseByUser/{user_id}`
   - **Response**:
     ```json
     [
       { "vase_id": "...", "device_id": "...", ... },
       ...
     ]
     ```

6. **Get a device by ID**
   - **Endpoint**: `/device/{device_id}`
   - **Response**:
     ```json
     { "device_id": "...", "user_id": "...", "device_status": "active", ... }
     ```

7. **Get a vase by device ID**
   - **Endpoint**: `/vaseByDevice/{device_id}`
   - **Response**:
     ```json
     { "vase_id": "...", "plant": {}, ... }
     ```

8. **Get a vase by ID**
   - **Endpoint**: `/vase/{vase_id}`
   - **Response**:
     ```json
     { "vase_id": "...", "device_id": "...", ... }
     ```

9. **Get a user by ID**
   - **Endpoint**: `/user/{user_id}`
   - **Response**:
     ```json
     { "user_id": "...", "telegram_chat_id": "...", ... }
     ```

---

**POST Requests**

1. **Add a new device**
   - **Endpoint**: `/device`
   - **Request Body**:
     ```json
     {
       "device_id": "12345",
       "user_id": "67890"
       ...
     }
     ```
   - **Response**:
     ```json
     { "message": "Device added successfully" }
     ```
   - **Error Response** (if channel creation fails):
     - Status Code: 500
     - Message: `"Error in creating channel"`

2. **Add a new vase**
   - **Endpoint**: `/vase`
   - **Request Body**:
     ```json
     {
       "device_id": "12345",
       "vase_name": "Indoor Vase"
       ...
     }
     ```
   - **Response**:
     ```json
     {
       "message": "Vase added successfully",
       "id": 123456789
     }
     ```
   - **Error Response** (if device not found):
     ```json
     { "message": "No devices found with the given device_id" }
     ```

3. **Add a new user**
   - **Endpoint**: `/user`
   - **Request Body**:
     ```json
     {
       "telegram_chat_it": "123123123123"
     }
     ```
   - **Response**:
     ```json
     {
       "message": "User added successfully",
       "id": 987654321
     }
     ```

---

**PUT Requests**

1. **Update a device**
   - **Endpoint**: `/device/{device_id}`
   - **Request Body**:
     ```json
     {
       "device_status": "inactive"
     }
     ```
   - **Response**:
     ```json
     { "message": "Device updated successfully" }
     ```
   - **Error Response**:
     ```json
     { "message": "Device not found" }
     ```

2. **Update a vase**
   - **Endpoint**: `/vase/{vase_id}`
   - **Request Body**:
     ```json
     {
       "vase_name": "Outdoor Vase"
     }
     ```
   - **Response**:
     ```json
     { "message": "Vase updated successfully" }
     ```
   - **Error Response**:
     ```json
     { "message": "Vase not found" }
     ```

3. **Update a user**
   - **Endpoint**: `/user/{user_id}`
   - **Request Body**:
     ```json
     {
       "telegram_chat_id": "192873982"
     }
     ```
   - **Response**:
     ```json
     { "message": "User updated successfully" }
     ```
   - **Error Response**:
     ```json
     { "message": "User not found" }
     ```

---

### 1. **Data Analysis Service**
- **Local Port**: `:5082`
- **Public Endpoint**: `http://dataanalysis.duck.pictures`

**Description**:  
Fetches data on demand from ThingSpeak, analyzes it based on thresholds defined in the resource catalog, and is utilized by a Telegram bot to display real-time sensor data. Provides suggestions to improve plant conditions.

**API**:  
- **Request**: `GET /device_id`
- **Response**:
  ```json
  {
    "temperature_alert": "",
    "soil_moisture_alert": "high",
    "watertank_level_alert": "",
    "light_level_alert": "",
    "temperature": "20.0625",
    "light_level": "537.4847",
    "watertank_level": "0.0",
    "soil_moisture": "60.17094"
  }
  ```

---

### 2. **Gemini Service**
- **Local Port**: `:5151`
- **Public Endpoint**: `http://chat.duck.pictures`

**Description**:  
A wrapper around the Gemini LLM, providing plant care suggestions based on environmental data.

**API**:  
- **Request**: `POST /chat`  
  **Body (JSON)**: 
  ```json
  {"question": "question_to_ask"}
  ```
- **Response**:  
  `text of Gemini response`

---

### 3. **Chart Service**
- **Local Port**: `:5300`
- **Public Endpoint**: `http://chartservice.duck.pictures`

**Description**:  
Generates charts using ThingSpeak data, ranging from daily to yearly views.

**API**:  
- **Request**: `GET /channel_id/thingspeak_field?title='chart_title'&days=number`
- **Response**:  
  Returns an image of the requested chart.

---

### 4. **Image Recognition Service**
- **Local Port**: `:8085`
- **Public Endpoint**: `http://imagerecognition.duck.pictures`

**Description**:  
Uses PlantNet’s dataset API to identify plant species from images. Accepts up to 5 images and returns the recognized species.

**API**:  
- **Request**: `POST /`  
  **Form Data**: Up to 5 images
- **Response**:
  ```json
  {
    "result": {
      "species": "scientific_name",
      "common_name": "most_probable_plant_common_name",
      "confidence": "score_number"
    }
  }
  ```

---

### 5. **Recommendation Service**
- **Local Port**: `:8081`
- **Public Endpoint**: `http://recommendationservice.duck.pictures`

**Description**:  
Accepts up to 5 images, identifies the plant species using the Image Recognition Service, and queries the Gemini service for plant care suggestions.

**API**:  
- **Request**: `POST /`  
  **Form Data**: Up to 5 images
- **Response**:
  ```json
  {
    "plant_name": "string",
    "soil_moisture_min": double_digits_integer,
    "soil_moisture_max": double_digits_integer,
    "hours_sun_suggested": single_digit_integer,
    "temperature_min": double_digits_integer,
    "temperature_max": double_digits_integer,
    "description": "string (max 40 words)"
  }
  ```

---

### 6. **Service Catalog**
- **Local Port**: `:8082`
- **Public Endpoint**: `http://serviceservice.duck.pictures`

**Description**:  
Acts as the entry point for discovering other services.

**API**:  
- **Request**: `GET /all` or `GET /specific_field`
- **Response**:  
  Returns the requested field from the service catalog.

### 7. **Telegram Bot**
This service run a telegram bot which serve as a bridge for the user to interact with the rest of the services and display data.
### 8. **bot notifier**
This service run a mqtt client which subscribe to telegram topic. When it receive a message take the telegram_chat_id from it and send a push notification to the user.
### 9. **thingspeak adaptor**
This service act as a gateway between mqtt and thingspeak. It implement an mqtt client which subscribe on topic_sensor. On a received message from the esp32 it push the data to thingspeak database trough REST api.
### 10. **vase control**
This service implement an mqtt client which subscribe to topic_sensors. On message received it get the device_id from the topic, ask resource catalog for the plant configuration, check the treshold and eventually publish on topic_actuators(for actuation on esp32) or topic_telegram(for push notification).
### 11. **device connector**
This service is the only one running directly on the esp32 inside the smart vase. It manage everything related to the device starting from the first configuration, pushing the new device to resource catalog trough REST api. It implement an mqtt publisher to publish data from sensors and subscriber to receive actuation command.

## logs microservices
### grafana
local port -> :3000
public endpoint = 'http://grafana.duck.pictures'
### loki
local port -> :3100
public endpoint = 'http://loki.duck.pictures'
### prometheus
local port -> :9095
public endpoint = 'http://prometheus.duck.pictures'

## service catalog strcture
- mqtt_broker
    - broker_address
    - port
- mqtt_topics
    - topic_sensors
    - topic_actuators
    - topic_telegram_chat
- services
    - chart_service
    - data_analysis
    - gemini
    - image_recognition
    - recommendation_service
    - resource_catalog


## resource catalog strcture
- deviceList {...}
    - device_id
    - channel_id
    - read_key(thingspeak channel)
    - device_name
    - device_status
    - sensors []
    - actuators []
    - availableServices []
    - lastUpdate
    - user_id
- vaseList {...}
    - vase_id
    - vase_name
    - user_id
    - vase_status
    - plant
        - plant_name
        - plant_schedule_water
        - plant_schedule_light_level (duplicated)
        - soil_moisture_min
        - soil_moisture_max
        - hours_sun_min ()duplicated
        - temperature_min
        - temperature_max
        - description
    - lastUpdate
- userList {...}
    - user_id
    - telegram_chat_id
    - lastUpdate

## topics
- topic_sensors --> smartplant/+/sensors(+ --> device_id):  
'''json
{
    'vase_id': vase_id,  
    'bn': device_id,  
    'e':  
    [
        {'n': 'temperature', 'value': '', 'timestamp': '', 'unit': 'C'},  
        {'n': 'soil_moisture', 'value': '', 'timestamp': '', 'unit': '%'},
        {'n': 'light_level', 'value': '', 'timestamp': '', 'unit': 'lumen'},
        {'n': 'watertank_level', 'value': '', 'timestamp': '', 'unit': '%'}
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