# IoT Device Data Generator Panel

A simple and minimal customtkinter interface for generating fake IoT device data.

## Features

- **Device Selection**: Choose between Device 1, 2, or 3
- **Custom Data Generation**: Enter specific values for temperature, soil moisture, light level, and water tank level
- **Random Data Generation**: Generate realistic random values for all sensors
- **MQTT Integration**: Connect to MQTT broker to publish data
- **Real-time Logging**: View all activities in the built-in log panel

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements_panel.txt
```

## Usage

1. Run the device panel:
```bash
python device_panel.py
```

2. **Select a Device**: Choose Device 1, 2, or 3 using the radio buttons

3. **Enter Parameters**: 
   - Temperature (°C): 18.0 - 30.0 (typical range)
   - Soil Moisture (%): 0 - 100
   - Light Level (lux): 0 - 1000+
   - Water Tank Level (%): 0 - 100

4. **Generate Data**:
   - **Custom Data**: Uses the values you entered
   - **Random Data**: Generates realistic random values and updates the input fields

5. **MQTT Connection** (Optional):
   - Click "Connect to MQTT" to publish data to the broker
   - Data will be published to topic: `smartplant/{device_id}/sensors`

## Data Format

The generated data follows the SenML format:
```json
{
  "bn": "device_1",
  "e": [
    {"n": "temperature", "value": 22.5, "unit": "C"},
    {"n": "soil_moisture", "value": 45.2, "unit": "%"},
    {"n": "light_level", "value": 600, "unit": "lux"},
    {"n": "watertank_level", "value": 80.0, "unit": "%"}
  ]
}
```

## MQTT Topics

- **Publish**: `smartplant/{device_id}/sensors`
- **Subscribe**: `smartplant/{device_id}/actuators/+`

## Default Broker

- **Broker**: broker.hivemq.com
- **Port**: 1883

## Screenshots

The panel features:
- Dark theme with modern UI
- Device selection radio buttons
- Parameter input fields
- Action buttons with icons
- Real-time activity log
- Connection status indicator

## Troubleshooting

- **Connection Issues**: Make sure you have internet access for MQTT broker connection
- **Invalid Values**: Enter numeric values only, with appropriate ranges
- **Import Errors**: Ensure all dependencies are installed correctly 