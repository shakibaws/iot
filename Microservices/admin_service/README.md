# Admin Analytics Service

A comprehensive admin dashboard for the IoT Smart Vase system built with Dash Python.

## Features

### Real-time Insights

- **Total Users**: Current number of registered users
- **Total Vases**: Number of vases in the system
- **Total Devices**: Number of connected devices
- **Active Devices**: Number of currently active devices

### Interactive Charts

1. **System Overview**: Bar chart showing users, vases, and devices count
2. **Device Status Distribution**: Pie chart showing device status breakdown
3. **Top 5 Users by Vase Count**: Bar chart showing most active users
4. **Plant Types Distribution**: Bar chart showing variety of plants

### Recent Activity

- Real-time feed of recent user registrations
- New vase additions with plant types
- Timestamped activity log

## Architecture

The service follows the same architectural pattern as other microservices:

- **Framework**: Dash Python for web dashboard
- **Data Source**: Resource Catalog API endpoints
- **Service Discovery**: Service Catalog for endpoint resolution
- **Logging**: CustomLogger for consistent logging
- **Real-time Updates**: Auto-refresh every 30 seconds
- **Responsive Design**: Mobile-friendly CSS styling

## API Endpoints Used

The service consumes data from the Resource Catalog:

- `GET /listUser` - Retrieve all users
- `GET /listVase` - Retrieve all vases
- `GET /listDevice` - Retrieve all devices

## Configuration

- **Port**: 5020 (configurable)
- **Service Catalog**: http://localhost:5001 (default)
- **Auto-refresh**: 30 seconds for dashboard, 5 minutes for service discovery
- **Logs**: Stored in `/app/logs/admin_analytics.log`

## Docker Setup

The service is configured to run in Docker with:

```yaml
admin_analytics:
  build: ./Microservices/Admin Analytics service
  container_name: admin_analytics
  ports:
    - "5020:5020"
  depends_on:
    - resource_catalog
    - service_catalog
  volumes:
    - ./logs/admin_analytics:/app/logs
  environment:
    - LOG_DIR=/app/logs
  restart: on-failure
```

## Access

Once running, access the admin dashboard at: **http://localhost:5020**

## Dependencies

- dash==2.18.1
- plotly==5.22.0
- pandas==2.2.2
- requests==2.32.3
- python-dateutil==2.9.0.post0

## Service Registration

The service is automatically registered in the Service Catalog as:

```json
{
  "admin_analytics": "http://localhost:5020"
}
```
