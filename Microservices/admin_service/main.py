import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import requests
import datetime
import json
import CustomerLogger
import sys
import os
from collections import Counter, deque
import threading
import time
import random
from MyMQTT import MyMQTT

class AdminDashboard:
    def __init__(self):
        self.logger = CustomerLogger.CustomLogger("admin_analytics", "admin_user")
        self.service_catalog_endpoint = 'http://service_catalog:5001'  # Service catalog endpoint
        self.resource_catalog_address = ''
        
        # MQTT configuration
        self.mqtt_broker = ''
        self.mqtt_port = 1883
        self.mqtt_client = None
        self.sensor_data_queue = deque(maxlen=100)  # Store last 100 sensor readings
        
        # Initialize Dash app
        self.app = dash.Dash(__name__)
        self.app.title = "IoT Smart Vase Admin Dashboard"
        
        # Get service configuration
        self.get_service_configuration()
        
        # Setup MQTT listener
        self.setup_mqtt_listener()
        
        # Setup layout and callbacks
        self.setup_layout()
        self.setup_callbacks()
        
        # Start background data refresh
        self.start_background_refresh()
        

        
    def get_service_configuration(self):
        try:
            response = requests.get(f'{self.service_catalog_endpoint}/all')
            if response.status_code == 200:
                config = response.json()
                self.resource_catalog_address = config['services']['resource_catalog']
                self.mqtt_broker = config['mqtt_broker']['broker_address']
                self.mqtt_port = config['mqtt_broker']['port']
                self.sensor_topic = config['mqtt_topics']['topic_sensors']  # "smartplant/+/sensors"
                self.logger.info(f"Resource catalog endpoint: {self.resource_catalog_address}")
                self.logger.info(f"MQTT broker: {self.mqtt_broker}:{self.mqtt_port}")
            else:
                self.logger.error("Failed to get service catalog")
                self.resource_catalog_address = 'http://resource_catalog:5002' 
                self.mqtt_broker = 'broker.hivemq.com' 
                self.sensor_topic = 'smartplant/+/sensors'
        except Exception as e:
            self.logger.error(f"Error getting service configuration: {str(e)}")
            self.resource_catalog_address = 'http://resource_catalog:5002'  
            self.mqtt_broker = 'broker.hivemq.com' 
            self.sensor_topic = 'smartplant/+/sensors'

    def setup_mqtt_listener(self):
        """Setup MQTT client to listen for sensor data"""
        try:
            # Only setup MQTT if we have valid configuration
            if not self.mqtt_broker or not self.sensor_topic:
                self.logger.error("Missing MQTT configuration - broker or topic not set")
                return
                
            client_id = f"admin_analytics_{random.randint(1000, 9999)}"
            self.mqtt_client = MyMQTT(client_id, self.mqtt_broker, self.mqtt_port, self)
            
            self.logger.info(f"Setting up MQTT: broker={self.mqtt_broker}, port={self.mqtt_port}, topic={self.sensor_topic}")
            
            # Start MQTT in a separate thread
            mqtt_thread = threading.Thread(target=self.start_mqtt_listener, daemon=True)
            mqtt_thread.start()
            
            self.logger.info("MQTT listener setup completed")
        except Exception as e:
            self.logger.error(f"Error setting up MQTT listener: {str(e)}")

    def start_mqtt_listener(self):
        """Start MQTT listener in background thread"""
        retry_count = 0
        max_retries = 5
        
        while retry_count < max_retries:
            try:
                self.logger.info(f"Attempting MQTT connection (attempt {retry_count + 1}/{max_retries})")
                self.mqtt_client.mySubscribe(self.sensor_topic)
                self.mqtt_client.connect()
                time.sleep(3)  # Allow connection to establish
                self.mqtt_client.start()  # This calls loop_forever() - blocking
                self.logger.info(f"MQTT listener started successfully, subscribed to: {self.sensor_topic}")
                return  # Success, exit retry loop
            except Exception as e:
                retry_count += 1
                self.logger.error(f"Error starting MQTT listener (attempt {retry_count}): {str(e)}")
                if retry_count < max_retries:
                    time.sleep(5)  # Wait before retry
                else:
                    self.logger.error("Failed to start MQTT listener after all retries")

    def notify(self, topic, payload):
        """MQTT message callback - called when sensor data is received"""
        try:
            self.logger.info(f"MQTT message received - Topic: {topic}")
            
            # Handle payload decoding
            if isinstance(payload, bytes):
                payload_str = payload.decode('utf-8')
            else:
                payload_str = str(payload)
            
            self.logger.info(f"MQTT payload: {payload_str}")
            
            # Parse the topic to extract device_id
            # Topic format: "smartplant/device_id/sensors"
            topic_parts = topic.split('/')
            self.logger.info(f"Topic parts: {topic_parts}")
            
            if len(topic_parts) >= 3:
                device_id = topic_parts[1]
                message_type = topic_parts[2]
                
                self.logger.info(f"Parsed - Device ID: {device_id}, Message Type: {message_type}")
                
                if message_type == "sensors":
                    try:
                        # Parse the JSON payload
                        data = json.loads(payload_str)
                        self.logger.info(f"Parsed JSON data: {data}")
                        
                        # Get device information to find channel_id (async to not block MQTT)
                        channel_id = 'Unknown'
                        try:
                            device_info = self.get_device_info(device_id)
                            if device_info:
                                channel_id = device_info.get('channel_id', 'Unknown')
                        except Exception as device_err:
                            self.logger.warning(f"Could not get device info for {device_id}: {device_err}")
                        
                        # Process sensor data
                        sensor_reading = {
                            'timestamp': datetime.datetime.now(),
                            'device_id': device_id,
                            'channel_id': channel_id,
                            'data': data,
                            'topic': topic
                        }
                        
                        # Add to queue for recent activity display
                        self.sensor_data_queue.append(sensor_reading)
                        
                        # Log the sensor data
                        self.logger.info(f"✅ Sensor data processed and queued for device {device_id} - Queue size: {len(self.sensor_data_queue)}")
                        
                    except json.JSONDecodeError as json_err:
                        self.logger.error(f"Failed to parse JSON payload: {json_err}")
                        
                else:
                    self.logger.info(f"Ignoring non-sensor message: {message_type}")
            else:
                self.logger.warning(f"Invalid topic format: {topic}")
                    
        except Exception as e:
            self.logger.error(f"Error processing MQTT message: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")

    def get_device_info(self, device_id):
        """Get device information including channel_id"""
        try:
            response = requests.get(f'{self.resource_catalog_address}/device/{device_id}', timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            self.logger.error(f"Error getting device info for {device_id}: {str(e)}")
            return None

   
    def fetch_data(self):
        """Fetch data from resource catalog"""
        try:
            # Fetch users, vases, and devices
            users_response = requests.get(f'{self.resource_catalog_address}/listUser')
            vases_response = requests.get(f'{self.resource_catalog_address}/listVase')
            devices_response = requests.get(f'{self.resource_catalog_address}/listDevice')
            
            users = users_response.json() if users_response.status_code == 200 else []
            vases = vases_response.json() if vases_response.status_code == 200 else []
            devices = devices_response.json() if devices_response.status_code == 200 else []
            
            return users, vases, devices
        except Exception as e:
            self.logger.error(f"Error fetching data: {str(e)}")
            return [], [], []

    def setup_layout(self):
        """Setup the Dash layout"""
        self.app.layout = html.Div([
            # Header
            html.Div([
                html.H1("🌱 IoT Smart Vase Admin Dashboard", 
                       className="header-title"),
                html.P("Real-time insights and analytics for your IoT system", 
                       className="header-subtitle"),
                html.Div(id="last-update", className="last-update")
            ], className="header"),
            
            # Stats Cards
            html.Div([
                html.Div([
                    html.Div([
                        html.H3(id="total-users", children="0"),
                        html.P("Total Users")
                    ], className="stat-card users-card")
                ], className="stat-item"),
                
                html.Div([
                    html.Div([
                        html.H3(id="total-vases", children="0"),
                        html.P("Total Vases")
                    ], className="stat-card vases-card")
                ], className="stat-item"),
                
                html.Div([
                    html.Div([
                        html.H3(id="total-devices", children="0"),
                        html.P("Total Devices")
                    ], className="stat-card devices-card")
                ], className="stat-item"),
                
                html.Div([
                    html.Div([
                        html.H3(id="active-devices", children="0"),
                        html.P("Active Devices")
                    ], className="stat-card active-card")
                ], className="stat-item")
            ], className="stats-container"),
            
            # Charts Row 1
            html.Div([
                html.Div([
                    dcc.Graph(id="users-vases-chart")
                ], className="chart-container"),
                
                html.Div([
                    dcc.Graph(id="device-status-chart")
                ], className="chart-container")
            ], className="charts-row"),
            
            # Charts Row 2
            html.Div([
                html.Div([
                    dcc.Graph(id="top-users-chart")
                ], className="chart-container"),
                
                html.Div([
                    dcc.Graph(id="plant-types-chart")
                ], className="chart-container")
            ], className="charts-row"),
            
            # Recent Activity
            html.Div([
                html.H3("Recent Activity"),
                html.Div([
                    html.Div([
                        html.H4("📊 Real-time Sensor Data"),
                        html.Div(id="sensor-activity")
                    ], className="activity-subsection"),
                    html.Div([
                        html.H4("👥 System Activity"),
                        html.Div(id="system-activity")
                    ], className="activity-subsection")
                ], className="activity-grid")
            ], className="activity-section"),
            
            # Auto-refresh interval
            dcc.Interval(
                id='interval-component',
                interval=30*1000,  # Refresh every 30 seconds
                n_intervals=0
            ),
            
            # Custom CSS
            html.Link(
                rel='stylesheet',
                href='/assets/styles.css'
            )
        ])

    def setup_callbacks(self):
        """Setup Dash callbacks"""
        @self.app.callback(
            [Output('total-users', 'children'),
             Output('total-vases', 'children'),
             Output('total-devices', 'children'),
             Output('active-devices', 'children'),
             Output('users-vases-chart', 'figure'),
             Output('device-status-chart', 'figure'),
             Output('top-users-chart', 'figure'),
             Output('plant-types-chart', 'figure'),
             Output('sensor-activity', 'children'),
             Output('system-activity', 'children'),
             Output('last-update', 'children')],
            [Input('interval-component', 'n_intervals')]
        )
        def update_dashboard(n):
            users, vases, devices = self.fetch_data()
            
            # Calculate statistics
            total_users = len(users)
            total_vases = len(vases)
            total_devices = len(devices)
            active_devices = len([d for d in devices if d.get('device_status') == 'active'])
            
            # Users vs Vases chart
            users_vases_fig = go.Figure(data=[
                go.Bar(name='Users', x=['Count'], y=[total_users], marker_color='#3498db'),
                go.Bar(name='Vases', x=['Count'], y=[total_vases], marker_color='#2ecc71'),
                go.Bar(name='Devices', x=['Count'], y=[total_devices], marker_color='#e74c3c')
            ])
            users_vases_fig.update_layout(
                title="System Overview",
                barmode='group',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            # Device status chart
            device_statuses = [d.get('device_status', 'unknown') for d in devices]
            status_counts = Counter(device_statuses)
            
            device_status_fig = go.Figure(data=[
                go.Pie(labels=list(status_counts.keys()), 
                       values=list(status_counts.values()),
                       hole=0.4)
            ])
            device_status_fig.update_layout(
                title="Device Status Distribution",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            # Top users by vase count
            user_vase_counts = Counter([v.get('user_id') for v in vases if v.get('user_id')])
            top_users = user_vase_counts.most_common(5)
            
            if top_users:
                user_ids, counts = zip(*top_users)
                # Try to get user names
                user_names = []
                for user_id in user_ids:
                    user = next((u for u in users if u.get('user_id') == user_id), None)
                    if user and user.get('telegram_chat_id'):
                        user_names.append(f"User {user_id[-4:]}")
                    else:
                        user_names.append(f"User {user_id[-4:]}")
                
                top_users_fig = go.Figure(data=[
                    go.Bar(x=user_names, y=counts, marker_color='#9b59b6')
                ])
                top_users_fig.update_layout(
                    title="Top 5 Users by Vase Count",
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
            else:
                top_users_fig = go.Figure()
                top_users_fig.update_layout(title="Top 5 Users by Vase Count - No Data")
            
            # Plant types distribution
            plant_names = []
            for vase in vases:
                plant = vase.get('plant', {})
                if isinstance(plant, dict):
                    plant_name = plant.get('plant_name', 'Unknown')
                    plant_names.append(plant_name)
            
            plant_counts = Counter(plant_names)
            
            if plant_counts:
                plant_types_fig = go.Figure(data=[
                    go.Bar(x=list(plant_counts.keys()), 
                           y=list(plant_counts.values()),
                           marker_color='#1abc9c')
                ])
                plant_types_fig.update_layout(
                    title="Plant Types Distribution",
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    xaxis_tickangle=-45
                )
            else:
                plant_types_fig = go.Figure()
                plant_types_fig.update_layout(title="Plant Types Distribution - No Data")
            
            # Sensor activity from MQTT data
            sensor_activities = []
            recent_sensor_data = list(self.sensor_data_queue)[-10:]  # Last 10 sensor readings
            
            # Debug logging
            self.logger.info(f"Dashboard update - Queue size: {len(self.sensor_data_queue)}, Recent data: {len(recent_sensor_data)}")
            
            for reading in reversed(recent_sensor_data):  # Most recent first
                timestamp = reading['timestamp'].strftime('%H:%M:%S')
                device_id = reading['device_id']
                channel_id = reading['channel_id']
                
                # Parse sensor data
                sensor_values = []
                if 'e' in reading['data']:
                    for sensor in reading['data']['e']:
                        name = sensor.get('n', 'Unknown')
                        value = sensor.get('value', 'N/A')
                        
                        # Format sensor name and value with appropriate icons
                        if name == 'temperature':
                            sensor_values.append(f"🌡️ {value}°C")
                        elif name == 'soil_moisture':
                            sensor_values.append(f"💧 {value}%")
                        elif name == 'light_level':
                            sensor_values.append(f"☀️ {value}lx")
                        elif name == 'watertank_level':
                            sensor_values.append(f"🚰 {value}%")
                        else:
                            sensor_values.append(f"📊 {name}: {value}")
                
                sensor_str = " | ".join(sensor_values) if sensor_values else "No data"
                
                sensor_activities.append(html.Div([
                    html.Span("📡 ", style={'marginRight': '5px'}),
                    html.Span(f"{device_id}", style={'color': '#e74c3c', 'fontWeight': 'bold'}),
                    html.Span(f" (Ch:{channel_id}) ", style={'color': '#95a5a6', 'fontSize': '10px'}),
                    html.Br(),
                    html.Span(sensor_str, style={'color': '#2c3e50', 'fontSize': '12px'}),
                    html.Span(f" - {timestamp}", style={'color': '#7f8c8d', 'fontSize': '10px', 'float': 'right'})
                ], style={'marginBottom': '8px', 'padding': '5px', 'border': '1px solid #ecf0f1', 'borderRadius': '3px'}))
            
            if not sensor_activities:
                # Add debug information if no sensor data
                debug_info = []
                debug_info.append(html.P("No sensor data received yet", style={'color': '#95a5a6', 'fontStyle': 'italic'}))
                debug_info.append(html.P(f"MQTT Broker: {self.mqtt_broker}", style={'fontSize': '10px', 'color': '#95a5a6'}))
                debug_info.append(html.P(f"Sensor Topic: {self.sensor_topic}", style={'fontSize': '10px', 'color': '#95a5a6'}))
                debug_info.append(html.P(f"Queue Size: {len(self.sensor_data_queue)}", style={'fontSize': '10px', 'color': '#95a5a6'}))
                sensor_activities = debug_info
            
            # System activity
            system_activities = []
            
            # Sort by lastUpdate if available
            recent_users = sorted(users, key=lambda x: x.get('lastUpdate', ''), reverse=True)[:3]
            recent_vases = sorted(vases, key=lambda x: x.get('lastUpdate', ''), reverse=True)[:3]
            
            for user in recent_users:
                system_activities.append(html.Div([
                    html.Span("👤 ", style={'marginRight': '5px'}),
                    html.Span(f"New user registered", style={'color': '#3498db'}),
                    html.Span(f" - {user.get('lastUpdate', 'Unknown time')}", 
                             style={'color': '#7f8c8d', 'fontSize': '12px'})
                ], style={'marginBottom': '5px'}))
            
            for vase in recent_vases:
                plant_name = "Unknown"
                if isinstance(vase.get('plant'), dict):
                    plant_name = vase.get('plant', {}).get('plant_name', 'Unknown')
                system_activities.append(html.Div([
                    html.Span("🌱 ", style={'marginRight': '5px'}),
                    html.Span(f"New vase added: {plant_name}", style={'color': '#2ecc71'}),
                    html.Span(f" - {vase.get('lastUpdate', 'Unknown time')}", 
                             style={'color': '#7f8c8d', 'fontSize': '12px'})
                ], style={'marginBottom': '5px'}))
            
            if not system_activities:
                system_activities = [html.P("No recent system activity")]
            
            # Last update time
            last_update = f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return (total_users, total_vases, total_devices, active_devices,
                   users_vases_fig, device_status_fig, top_users_fig, plant_types_fig,
                   sensor_activities, system_activities, last_update)

    def start_background_refresh(self):
        """Start background data refresh"""
        def refresh_data():
            while True:
                try:
                    self.get_service_configuration()
                    time.sleep(300)  # Refresh service catalog every 5 minutes
                except Exception as e:
                    self.logger.error(f"Background refresh error: {str(e)}")
                    time.sleep(60)  # Wait 1 minute on error
        
        refresh_thread = threading.Thread(target=refresh_data, daemon=True)
        refresh_thread.start()

    def run(self, host='0.0.0.0', port=5010, debug=False):
        """Run the Dash application"""
        self.logger.info(f"Starting Admin Dashboard on {host}:{port}")
        self.app.run_server(host=host, port=port, debug=debug)


if __name__ == '__main__':
    try:
        # Create assets directory for CSS
        assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        os.makedirs(assets_dir, exist_ok=True)
        
        # Create and run dashboard
        dashboard = AdminDashboard()
        dashboard.run(debug=False)
        
    except Exception as e:
        print("ERROR OCCURRED, DUMPING INFO...")
        path = os.path.abspath('./logs/ERROR_admin_analytics.err')
        try:
            with open(path, 'a') as file:
                date = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
                file.write(f"Crashed at : {date}\n")
                file.write(f"Unexpected error: {e}\n")
        except:
            pass
        print(f"Unexpected error: {e}")
        print("EXITING...")
        sys.exit(1)
