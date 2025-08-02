import customtkinter as ctk
import json
import random
from datetime import datetime
import requests
from device_simulator import DeviceSimulator


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class DeviceDataPanel:
    def __init__(self,device_list):
        self.device_list = device_list
        self.root = ctk.CTk()
        self.root.title("IoT Device Data Generator")
        self.root.geometry("600x700")
        self.root.resizable(False, False)
        self.simulator : DeviceSimulator
        
        # Device data
        self.device_id = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Title
        title_label = ctk.CTkLabel(
            self.root, 
            text="🌱 IoT Device Data Generator", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=20)
        
        # Device Selection Frame
        device_frame = ctk.CTkFrame(self.root)
        device_frame.pack(pady=10, padx=10, fill="x")
        
        device_label = ctk.CTkLabel(
            device_frame, 
            text="Select Device:", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        device_label.pack(pady=10)
        
        self.device_var = ctk.StringVar(value="Select Device")
        self.device_dropdown = ctk.CTkOptionMenu(
            device_frame,
            values=self.device_list,
            variable=self.device_var,
            command=self.on_device_change,
            width=250
        )
        self.device_dropdown.pack(pady=10)
        
        # Parameters Frame
        params_frame = ctk.CTkFrame(self.root)
        params_frame.pack(pady=10, padx=20, fill="x")
        
        params_label = ctk.CTkLabel(
            params_frame, 
            text="Sensor Parameters:", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        params_label.pack(pady=10)
        
        # Temperature
        temp_frame = ctk.CTkFrame(params_frame)
        temp_frame.pack(pady=5, padx=10, fill="x")
        
        temp_label = ctk.CTkLabel(temp_frame, text="Temperature (°C):")
        temp_label.pack(side="left", padx=10)
        
        self.temp_var = ctk.StringVar(value="22.0")
        self.temp_entry = ctk.CTkEntry(temp_frame, textvariable=self.temp_var, width=100)
        self.temp_entry.pack(side="right", padx=10)
        
        # Soil Moisture
        soil_frame = ctk.CTkFrame(params_frame)
        soil_frame.pack(pady=5, padx=10, fill="x")
        
        soil_label = ctk.CTkLabel(soil_frame, text="Soil Moisture (%):")
        soil_label.pack(side="left", padx=10)
        
        self.soil_var = ctk.StringVar(value="45.0")
        self.soil_entry = ctk.CTkEntry(soil_frame, textvariable=self.soil_var, width=100)
        self.soil_entry.pack(side="right", padx=10)
        
        # Light Level
        light_frame = ctk.CTkFrame(params_frame)
        light_frame.pack(pady=5, padx=10, fill="x")
        
        light_label = ctk.CTkLabel(light_frame, text="Light Level (lux):")
        light_label.pack(side="left", padx=10)
        
        self.light_var = ctk.StringVar(value="600")
        self.light_entry = ctk.CTkEntry(light_frame, textvariable=self.light_var, width=100)
        self.light_entry.pack(side="right", padx=10)
        
        # Water Tank Level
        water_frame = ctk.CTkFrame(params_frame)
        water_frame.pack(pady=5, padx=10, fill="x")
        
        water_label = ctk.CTkLabel(water_frame, text="Water Tank Level (%):")
        water_label.pack(side="left", padx=10)
        
        self.water_var = ctk.StringVar(value="80")
        self.water_entry = ctk.CTkEntry(water_frame, textvariable=self.water_var, width=100)
        self.water_entry.pack(side="right", padx=10)
        
        # Buttons Frame
        buttons_frame = ctk.CTkFrame(self.root)
        buttons_frame.pack(pady=20, padx=20, fill="x")
        
        # Generate Custom Data Button
        self.custom_btn = ctk.CTkButton(
            buttons_frame,
            text="📊 Generate Custom Data",
            command=self.generate_custom_data,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.custom_btn.pack(pady=10, padx=20, fill="x")
        
        # Generate Random Data Button
        self.random_btn = ctk.CTkButton(
            buttons_frame,
            text="🎲 Generate Random Data",
            command=self.generate_random_data,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.random_btn.pack(pady=10, padx=20, fill="x")
        

        

        
        # Log Frame
        log_frame = ctk.CTkFrame(self.root)
        log_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        log_label = ctk.CTkLabel(
            log_frame,
            text="Activity Log:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        log_label.pack(pady=5)
        
        self.log_text = ctk.CTkTextbox(log_frame, height=150)
        self.log_text.pack(pady=5, padx=10, fill="both", expand=True)
        
    def on_device_change(self, choice):
        """Handle device selection change"""
        if choice == "Select Device":
            self.device_id = None
            self.log_message("No device selected")
        else:
            self.device_id = choice.split()[-1]  # Extract number from "Device X"
            self.log_message(f"Selected {choice}")
            self.simulator = DeviceSimulator(choice)
            self.simulator.start()
            self.log_message(f"Simulation started for {choice}")

        
    def log_message(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert("end", log_entry)
        self.log_text.see("end")
        print(log_entry.strip())
        
    def generate_custom_data(self):
        """Generate data with custom values"""
        if not self.device_id:
            self.log_message("❌ Please select a device first")
            return
            
        try:
            # Get values from entries
            temperature = float(self.temp_var.get())
            soil_moisture = float(self.soil_var.get())
            light_level = float(self.light_var.get())
            watertank_level = float(self.water_var.get())
            
            # Validate ranges
            if not (0 <= soil_moisture <= 100):
                self.log_message("❌ Soil moisture must be between 0-100%")
                return
            if not (0 <= watertank_level <= 100):
                self.log_message("❌ Water tank level must be between 0-100%")
                return
            if light_level < 0:
                self.log_message("❌ Light level must be positive")
                return
                
            data = {
                "bn": f"device_{self.device_id}",
                "e": [
                    {"n": "temperature", "value": round(temperature, 1), "unit": "C"},
                    {"n": "soil_moisture", "value": round(soil_moisture, 1), "unit": "%"},
                    {"n": "light_level", "value": round(light_level), "unit": "lux"},
                    {"n": "watertank_level", "value": round(watertank_level, 1), "unit": "%"}
                ]
            }
            
            self.publish_data(data, "custom")
            
        except ValueError:
            self.log_message("❌ Please enter valid numeric values")
            
    def generate_random_data(self):
        """Generate data with random values"""
        if not self.device_id:
            self.log_message("❌ Please select a device first")
            return
            
        # Generate realistic random values
        temperature = random.uniform(18.0, 30.0)
        soil_moisture = random.uniform(20.0, 90.0)
        light_level = random.uniform(50, 1000)
        watertank_level = random.uniform(10.0, 100.0)
        
        data = {
            "bn": f"device_{self.device_id}",
            "e": [
                {"n": "temperature", "value": round(temperature, 1), "unit": "C"},
                {"n": "soil_moisture", "value": round(soil_moisture, 1), "unit": "%"},
                {"n": "light_level", "value": round(light_level), "unit": "lux"},
                {"n": "watertank_level", "value": round(watertank_level, 1), "unit": "%"}
            ]
        }
        
        # Update UI with generated values
        self.temp_var.set(str(round(temperature, 1)))
        self.soil_var.set(str(round(soil_moisture, 1)))
        self.light_var.set(str(round(light_level)))
        self.water_var.set(str(round(watertank_level, 1)))
        
        self.publish_data(data, "random")
        
    def publish_data(self, data, data_type):
        """Generate and log data"""
        # Log the data
        temp = data['e'][0]['value']
        soil = data['e'][1]['value']
        light = data['e'][2]['value']
        water = data['e'][3]['value']
        self.log_message(f"📊 Generated {data_type} data")
        self.log_message(f"📊 T={temp}°C, SM={soil}%, L={light}lux, WT={water}%")
        self.simulator.publish_sensor_data(data)

            
    def run(self):
        """Start the application"""
        self.log_message("🚀 IoT Device Data Generator started")
        self.log_message("Select a device and enter parameters to generate data")
        self.root.mainloop()


def main():
    """Main function"""
    device_list = []
    service_catalog_url = "http://localhost:5001"
    response = requests.get(service_catalog_url)
    resource_catalog = response.json()["services"]["resource_catalog"]
    print(resource_catalog)
    response = requests.get(f"{resource_catalog}/listDevice/")
    for device in response.json():  
        device_list.append(device["device_id"])
    
    print(device_list)
    app = DeviceDataPanel(device_list)
    app.run()


if __name__ == "__main__":
    main() 