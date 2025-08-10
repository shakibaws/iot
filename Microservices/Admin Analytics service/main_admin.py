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
from collections import Counter
import threading
import time

class AdminDashboard:
    def __init__(self):
        self.logger = CustomerLogger.CustomLogger("admin_analytics", "admin_user")
        self.service_catalog_endpoint = 'http://localhost:5001'  # Service catalog endpoint
        self.resource_catalog_address = ''
        
        # Initialize Dash app
        self.app = dash.Dash(__name__)
        self.app.title = "IoT Smart Vase Admin Dashboard"
        
        # Get resource catalog endpoint from service catalog
        self.get_resource_catalog_endpoint()
        
        # Setup layout and callbacks
        self.setup_layout()
        self.setup_callbacks()
        
        # Start background data refresh
        self.start_background_refresh()
        
    def get_resource_catalog_endpoint(self):
        """Get the resource catalog endpoint from service catalog"""
        try:
            response = requests.get(f'{self.service_catalog_endpoint}/all')
            if response.status_code == 200:
                services = response.json()
                self.resource_catalog_address = services['services']['resource_catalog']
                self.logger.info(f"Resource catalog endpoint: {self.resource_catalog_address}")
            else:
                self.logger.error("Failed to get service catalog")
                self.resource_catalog_address = 'http://localhost:5002'  # Default fallback
        except Exception as e:
            self.logger.error(f"Error getting resource catalog endpoint: {str(e)}")
            self.resource_catalog_address = 'http://localhost:5002'  # Default fallback

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
                html.Div(id="recent-activity")
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
             Output('recent-activity', 'children'),
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
            
            # Recent activity
            recent_activities = []
            
            # Sort by lastUpdate if available
            recent_users = sorted(users, key=lambda x: x.get('lastUpdate', ''), reverse=True)[:3]
            recent_vases = sorted(vases, key=lambda x: x.get('lastUpdate', ''), reverse=True)[:3]
            
            for user in recent_users:
                recent_activities.append(html.Div([
                    html.Span("👤 ", style={'marginRight': '5px'}),
                    html.Span(f"New user registered", style={'color': '#3498db'}),
                    html.Span(f" - {user.get('lastUpdate', 'Unknown time')}", 
                             style={'color': '#7f8c8d', 'fontSize': '12px'})
                ], style={'marginBottom': '5px'}))
            
            for vase in recent_vases:
                plant_name = "Unknown"
                if isinstance(vase.get('plant'), dict):
                    plant_name = vase.get('plant', {}).get('plant_name', 'Unknown')
                recent_activities.append(html.Div([
                    html.Span("🌱 ", style={'marginRight': '5px'}),
                    html.Span(f"New vase added: {plant_name}", style={'color': '#2ecc71'}),
                    html.Span(f" - {vase.get('lastUpdate', 'Unknown time')}", 
                             style={'color': '#7f8c8d', 'fontSize': '12px'})
                ], style={'marginBottom': '5px'}))
            
            if not recent_activities:
                recent_activities = [html.P("No recent activity")]
            
            # Last update time
            last_update = f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return (total_users, total_vases, total_devices, active_devices,
                   users_vases_fig, device_status_fig, top_users_fig, plant_types_fig,
                   recent_activities, last_update)

    def start_background_refresh(self):
        """Start background data refresh"""
        def refresh_data():
            while True:
                try:
                    self.get_resource_catalog_endpoint()
                    time.sleep(300)  # Refresh service catalog every 5 minutes
                except Exception as e:
                    self.logger.error(f"Background refresh error: {str(e)}")
                    time.sleep(60)  # Wait 1 minute on error
        
        refresh_thread = threading.Thread(target=refresh_data, daemon=True)
        refresh_thread.start()

    def run(self, host='localhost', port=5010, debug=False):
        """Run the Dash application"""
        self.logger.info(f"Starting Admin Dashboard on {host}:{port}")
        self.app.run_server(host=host, port=port, debug=debug)

# Custom CSS styling
CSS_STYLES = """
/* Dashboard Styles */
body {
    font-family: 'Arial', sans-serif;
    margin: 0;
    padding: 0;
    background-color: #f8f9fa;
}

.header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 2rem;
    text-align: center;
    margin-bottom: 2rem;
}

.header-title {
    margin: 0;
    font-size: 2.5rem;
    font-weight: bold;
}

.header-subtitle {
    margin: 0.5rem 0 0 0;
    font-size: 1.2rem;
    opacity: 0.9;
}

.last-update {
    margin-top: 1rem;
    font-size: 0.9rem;
    opacity: 0.8;
}

.stats-container {
    display: flex;
    gap: 1rem;
    margin-bottom: 2rem;
    padding: 0 1rem;
}

.stat-item {
    flex: 1;
}

.stat-card {
    background: white;
    padding: 1.5rem;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    text-align: center;
    transition: transform 0.3s ease;
}

.stat-card:hover {
    transform: translateY(-5px);
}

.stat-card h3 {
    margin: 0;
    font-size: 2.5rem;
    font-weight: bold;
}

.stat-card p {
    margin: 0.5rem 0 0 0;
    color: #7f8c8d;
    font-size: 1rem;
}

.users-card h3 { color: #3498db; }
.vases-card h3 { color: #2ecc71; }
.devices-card h3 { color: #e74c3c; }
.active-card h3 { color: #f39c12; }

.charts-row {
    display: flex;
    gap: 1rem;
    margin-bottom: 2rem;
    padding: 0 1rem;
}

.chart-container {
    flex: 1;
    background: white;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    padding: 1rem;
}

.activity-section {
    margin: 2rem 1rem;
    background: white;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    padding: 1.5rem;
}

.activity-section h3 {
    margin-top: 0;
    color: #2c3e50;
}

@media (max-width: 768px) {
    .stats-container,
    .charts-row {
        flex-direction: column;
    }
    
    .header-title {
        font-size: 2rem;
    }
    
    .header-subtitle {
        font-size: 1rem;
    }
}
"""

if __name__ == '__main__':
    try:
        # Create assets directory for CSS
        assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        os.makedirs(assets_dir, exist_ok=True)
        
        # Write CSS file
        with open(os.path.join(assets_dir, 'styles.css'), 'w') as f:
            f.write(CSS_STYLES)
        
        # Create and run dashboard
        dashboard = AdminDashboard()
        dashboard.run(debug=False)
        
    except Exception as e:
        print("ERROR OCCURRED, DUMPING INFO...")
        path = os.path.abspath('/app/logs/ERROR_admin_analytics.err')
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
