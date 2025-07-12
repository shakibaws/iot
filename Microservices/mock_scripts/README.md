# IoT Device Simulator (MyMQTT Compatible)

This device simulator mimics ESP32 devices and works with the existing microservices architecture using the `MyMQTT` class.

## Features

- **Compatible with MyMQTT**: Uses the same MQTT wrapper as other microservices
- **Realistic sensor data**: Temperature, soil moisture, light level, water tank level
- **Automatic watering response**: Responds to water pump commands
- **Time-based variations**: Day/night cycles for temperature and light
- **Multiple broker support**: HiveMQ, Mosquitto, EMQX, or custom brokers

## Setup

1. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Run the simulator**:

   ```bash
   python device_simulator.py
   ```

3. **Enter device ID** when prompted (e.g., `device_001`)

4. **Select MQTT broker** (or use default HiveMQ)

## How It Works

### Data Flow

```
Device Simulator → MQTT Broker → ThingSpeak Adaptor → ThingSpeak
                                ↓
                              Vase Control → Water Pump Command
                                ↓
Device Simulator (responds to pump) ← MQTT Broker
```

### Sensor Data Format

```json
{
  "bn": "device_001",
  "e": [
    { "n": "temperature", "value": 24.5, "unit": "C" },
    { "n": "soil_moisture", "value": 45.2, "unit": "%" },
    { "n": "light_level", "value": 750, "unit": "lux" },
    { "n": "watertank_level", "value": 85, "unit": "%" }
  ]
}
```

### MQTT Topics

- **Publishes to**: `smartplant/{device_id}/sensors`
- **Subscribes to**: `smartplant/{device_id}/actuators/+`

## Usage Example

```bash
$ python device_simulator.py

🌱 IoT Device Simulator (MyMQTT Compatible)
=============================================

Enter device ID: test_device_123

Broker options:
1. broker.hivemq.com (default)
2. test.mosquitto.org
3. broker.emqx.io
4. Custom broker

Select broker (1-4) or press Enter for default:

✅ Device test_device_123 initialized
📡 Broker: broker.hivemq.com:1883
🚀 Starting simulation for device: test_device_123
📥 Subscribing to actuator commands...
📊 Publishing sensor data every 60 seconds...
💧 Listening for water pump commands...
Press Ctrl+C to stop

📊 T=24.1°C, SM=44.8%, L=823lux, WT=85%
📊 T=23.9°C, SM=44.3%, L=797lux, WT=85%
💧 Water pump activated!
📊 T=24.2°C, SM=69.1%, L=801lux, WT=80%
```

## Integration with Microservices

The simulator works seamlessly with:

- **ThingSpeak Adaptor**: Automatically logs sensor data to ThingSpeak
- **Vase Control**: Triggers automatic watering based on soil moisture
- **Telegram Bot**: Sends alerts when water tank is low
- **Data Analysis**: Analyzes sensor trends over time

## Files

- `device_simulator.py` - Main simulator script
- `MyMQTT.py` - MQTT wrapper class (provided by user)
- `CustomerLogger.py` - Logging utility
- `requirements.txt` - Python dependencies
- `README.md` - This documentation

## Notes

- The simulator uses threading to handle MQTT communication while publishing sensor data
- Water pump commands automatically increase soil moisture by 25%
- Each pump activation reduces water tank level by 5%
- Natural sensor variations simulate real-world conditions
