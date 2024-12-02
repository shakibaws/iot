import csv
import random
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta
import requests
import pandas as pd
import requests_cache
from retry_requests import retry
import openmeteo_requests
import asyncio
from zoneinfo import ZoneInfo
import time


# Data points (Direct Irradiance, Diffuse Irradiance) and corresponding sensor lux values
irradiance_data = np.array([
    [345, 74],
    [5.1, 260],
    [10, 123],
    [129, 185]
])
lux_values = np.array([410, 450, 64, 535])

# Fit a linear regression model
model = LinearRegression()
model.fit(irradiance_data, lux_values)

# Extract coefficients and intercept
coefficients = model.coef_
intercept = model.intercept_

# Function to calculate lux from irradiance
def calculate_lux(direct_radiation, diffuse_radiation):
    # Predict lux values based on the direct and diffuse radiation
    irradiance = np.array([[direct_radiation, diffuse_radiation]])
    lux = model.predict(irradiance)
    if lux[0] < 0:
        return 0
    else:
        return lux[0]
def adjust_temperature(previous_row, temperature_2m, direct_radiation, diffuse_radiation, new_time):
    # Get the time of day
    hour = new_time.hour
    
    # For simplicity, we assume irradiation data is in the form of 'direct_radiation' and 'diffuse_radiation'
    total_irradiation = direct_radiation + diffuse_radiation
    
    # Morning to Afternoon (8 AM to 4 PM): Increase the temperature based on irradiation
    if 8 <= hour < 16:  # Daytime hours
        if previous_row:
            # Increase temperature in the morning and afternoon
            temperature_2m += random.uniform(0.1, 0.5) * (total_irradiation / 1000)  # Scaling with irradiation level
    else:  # Evening or Night: Temperature stays the same or decreases
        if previous_row:
            # Decrease temperature or keep it steady at night
            temperature_2m += random.uniform(-0.2, 0.1) * (total_irradiation / 1000)  # Negative influence of irradiation

    # If the temperature is lower than 19, we ensure it's at least 19
    if temperature_2m < 19:
        temperature_2m = 19 + random.uniform(0, 0.2)
    
    return temperature_2m

def read_and_create_csv(input_file_path, output_file_path):
    # Open the original CSV file for reading
    with open(input_file_path, mode='r', newline='', encoding='utf-8') as csvfile:
        csvreader = csv.reader(csvfile)
        header = next(csvreader)  # Read header
        data = []
        
        # Process each row in the CSV
        previous_row = None
        soil_mosture = 70
        watertank_level = 100

        try:
            for row in csvreader:
                # Extract the original values
                base_time = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S%z').astimezone(ZoneInfo("Europe/Rome"))
                temperature_2m = float(row[1]) if row[1] != 'd' else 0.0  # Handle 'd' for missing data
                humidity = float(row[2]) if row[2] != 'd' else 0.0
                direct_radiation = float(row[3]) if row[3] != 'd' else 0.0
                diffuse_radiation = float(row[4]) if row[4] != 'd' else 0.0
                
                # For each hour, generate new data for every 2 minutes
                for minute_offset in range(0, 60, 2):
                    new_time = base_time + timedelta(minutes=minute_offset)
                    
                    # Add a random factor to the data to simulate slight changes
                    if previous_row:
                        humidity += random.uniform(-2.0, 2.0)
                        direct_radiation += random.uniform(-0.5, 0.5)
                        diffuse_radiation += random.uniform(-0.5, 0.5)

                        if base_time.hour > 7 and base_time.hour < 18:
                            soil_mosture += random.uniform(-0.2, 0)
                        else:
                            soil_mosture += random.uniform(-0.05, 0)
                        
                        if soil_mosture < 40:
                            soil_mosture = 70
                            watertank_level =  watertank_level - 20
                        
                        if watertank_level < random.choice([0,10,20]):
                            watertank_level = 100

                    # Temperature adjustment: if it is lower than 19, set it to 19 + random factor
                    temperature_2m = adjust_temperature(previous_row, 19, direct_radiation, diffuse_radiation, new_time)
                    
                    # Calculatxe lux from irradiance
                    lux = calculate_lux(direct_radiation, diffuse_radiation)
                    
                    # Append the new row with the updated datetime, temperature, humidity, and lux values
                    data.append([new_time.strftime('%Y-%m-%d %H:%M:%S%z'), round(temperature_2m, 3), round(lux, 2), round(soil_mosture, 2), round(watertank_level)])

                    # Update the previous row
                    previous_row = row
        except Exception as E:
            print('Error in: '+ str(row))  

    # Save the modified data into a new CSV file
    with open(output_file_path, mode='w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        # Write the header with the new column (lux values)
        csvwriter.writerow(['date', 'time', 'temperature', 'lux', 'soil_moisture', 'watertank_level'])
        # Write the new data
        csvwriter.writerows(data)

    print(f"Data saved to {output_file_path}")


    # Save the modified data into a new CSV file
    with open("mocked_data.csv", mode='w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerows(data)

'''
    watering_threshold = 40  # Soil moisture percentage to trigger watering
    records = []

    # Starting values
    light_level = 20.0
    temperature = 20.0
    soil_moisture = 80.0
    watertank_level = 100.0

    # Parse starting and ending dates
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S")

    # Calculate the total number of records based on the time range and cadence
    total_minutes = int((end_date - start_date).total_seconds() / 60)
    total_records = total_minutes // 2  # 2-minute cadence

    for i in range(total_records):
        timestamp = start_date + timedelta(minutes=2 * i)

        # Determine season (simplified based on Italy's climate)
        month = timestamp.month
        if 3 <= month <= 5:  # Spring
            max_light = 600
            temperature += random.uniform(-0.5, 1.0)
            soil_decrease_factor = 0.3
        elif 6 <= month <= 8:  # Summer
            max_light = 800
            temperature += random.uniform(-0.2, 1.5)
            soil_decrease_factor = 0.6
        elif 9 <= month <= 11:  # Autumn
            max_light = 500
            temperature += random.uniform(-0.5, 0.8)
            soil_decrease_factor = 0.4
        else:  # Winter
            max_light = 300
            temperature += random.uniform(-1.0, 0.5)
            soil_decrease_factor = 0.2

        # Simulate temperature and light level variations based on time of day
        hour = timestamp.hour
        if 6 <= hour <= 18:  # Daytime
            light_level = max(10.0, random.uniform(max_light - 200, max_light))
            temperature += random.uniform(-0.3, 1.0)
        else:  # Nighttime
            light_level = max(0.0, random.uniform(0, 50))
            temperature -= random.uniform(0.3, 1.0)

        # Keep temperature within realistic indoor ranges
        temperature = max(15.0, min(temperature, 25.0))

        # Soil moisture decreases based on temperature and soil decrease factor
        soil_moisture -= random.uniform(soil_decrease_factor, 1.0) + (temperature / 50.0)
        soil_moisture = max(0.0, soil_moisture)

        # Handle watering logic
        if soil_moisture < watering_threshold:
            soil_moisture += 20  # Watering increases moisture
            watertank_level -= random.uniform(3, 5)
            watertank_level = max(0.0, watertank_level)

        # Refill water tank if too low
        if watertank_level < 20:
            watertank_level = 100.0

        # Create record
       

'''


def send_data_to_thingspeak(channel_id, bulk_data, max_messages=960, delay=15):
    """
    Sends data to ThingSpeak in chunks based on the maximum number of messages allowed.

    Args:
        channel_id (str): ThingSpeak Channel ID.
        bulk_data (dict): Complete bulk data to send.
        max_messages (int): Maximum number of messages per request (default: 960 for free accounts).
        delay (int): Delay in seconds between requests (default: 15 seconds).
    """

    
    url = f"https://api.thingspeak.com/channels/{channel_id}/bulk_update.json"
    updates = bulk_data["updates"]
    write_api_key = bulk_data["write_api_key"]

    print(f"Sending data in chunks of up to {max_messages} messages\n Total messages: {len(updates)}\n expected time: {((len(updates)-2)*delay)/(max_messages*60)} minutes")

    for i in range(0, len(updates), max_messages):
        chunk = {
            "write_api_key": write_api_key,
            "updates": updates[i:i + max_messages]
        }
        try:
            response = requests.post(url, json=chunk)
            response.raise_for_status()
            print(f"Chunk {i // max_messages + 1} sent successfully.")
            
            # Wait the required delay if more chunks are left
            if i + max_messages < len(updates):
                print(f"Waiting {delay} seconds before sending the next chunk...")
                time.sleep(delay)
        except requests.exceptions.RequestException as e:
            print(f"Failed to send chunk {i // max_messages + 1}: {e}")
            break

async def getData(startDate, endDate):
    cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": 45.0705,
        "longitude": 7.6868,
        "start_date": startDate, # "2024-11-11",
        "end_date": endDate, #"2024-11-23",
        "hourly": ["temperature_2m", "relative_humidity_2m", "direct_radiation_instant", "diffuse_radiation_instant"],
        "timezone": "auto"
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation {response.Elevation()} m asl")
    print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()
    hourly_direct_radiation_instant = hourly.Variables(2).ValuesAsNumpy()
    hourly_diffuse_radiation_instant = hourly.Variables(3).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
        end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = hourly.Interval()),
        inclusive = "left"
    )}
    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["relative_humidity_2m"] = hourly_relative_humidity_2m
    hourly_data["direct_radiation_instant"] = hourly_direct_radiation_instant
    hourly_data["diffuse_radiation_instant"] = hourly_diffuse_radiation_instant

    hourly_dataframe = pd.DataFrame(data = hourly_data)
   # print(hourly_dataframe)
    hourly_dataframe.to_csv("./hourly_data.csv", index=False)

def generate_mock_data(api_key, input_file_path):
   
    with open(input_file_path, mode='r', newline='', encoding='utf-8') as csvfile:
        csvreader = csv.reader(csvfile)
        header = next(csvreader)
        records = []

        for row in csvreader:
            
            if len(row) < 5:
                print(f"Skipping invalid row: {row}")
                continue

            record = {
                "created_at": row[0],
                "field1": row[1],
                "field2": row[3],
                "field3": row[2],
                "field4": row[4],
            }

            records.append(record)

    # Prepare bulk update JSON
    bulk_data = {
        "write_api_key": api_key,
        "updates": records
    }

    return bulk_data

async def main():
    # Inputs
    '''
    channel_id = input("Enter ThingSpeak Channel ID: ")
    api_key = input("Enter ThingSpeak API Key: ")
    start_date_str = input("Enter starting date (YYYY-MM-DD): ")
    end_date_str = input("Enter ending date (YYYY-MM-DD): ")
'''
    channel_id = "2735513"
    api_key = "IMTXCSIUMQT8XAE6"
    start_date_str = "2024-07-01"
    end_date_str = "2024-12-01"

    await getData(start_date_str, end_date_str)
    read_and_create_csv("./hourly_data.csv","./minutes_data.csv")
    # Generate mock data
    bulk_data = generate_mock_data(api_key, "./minutes_data.csv")

    # Send the data to ThingSpeak
    send_data_to_thingspeak(channel_id, bulk_data)

asyncio.run(main())