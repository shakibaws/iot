import cherrypy
import json
import datetime
import uuid
import aiohttp
import asyncio
import time
import os
import matplotlib
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from io import BytesIO
from PIL import Image
from datetime import datetime, timedelta
from random import *
import CustomerLogger
import pytz
import sys
import numpy as np


# Thread pool to execute synchronous tasks in separate threads
executor = ThreadPoolExecutor(max_workers=4)

class ThingspeakChart:
    exposed = True

    def __init__(self):
        self.logger = CustomerLogger.CustomLogger("chart_service")
      

    async def fetch_data(self, url):
        """Fetch data asynchronously from ThingSpeak API with error handling."""
        self.logger.info(f"Fetching data from URL: {url}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        self.logger.error(f"Error fetching data. Status code: {response.status}")
                        raise cherrypy.HTTPError(400, f"Error fetching data: {response.status}")
                    return await response.json()
        except aiohttp.ClientError as e:
            self.logger.error(f"Network error while fetching data: {str(e)}")
            raise cherrypy.HTTPError(500, "Network error while fetching data")
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            raise cherrypy.HTTPError(500, "Unexpected error occurred")

    async def generate_chart(self, times, values, field_name, days):
        """Function to generate chart in a separate thread."""
        def _generate_chart():
            try:
                italy_tz = pytz.timezone('Europe/Rome')
                self.logger.info(f"Generating chart with {len(times)} data points")
                for t in times:
                    if not t.tzinfo:
                        t.replace(tzinfo=pytz.utc)
                    t.astimezone(italy_tz)


                plt.figure(figsize=(8, 6))
                plt.plot(times, values, marker="o", linestyle="-")
                plt.xlabel("Time")
                plt.ylabel(str(field_name).capitalize())
                plt.title(f"{str(field_name).split('_')[0].capitalize()} chart - {days} day{'s' if days > 1 else ''}")
                
                # Set y-axis limits dynamically based on the data
                if values:
                    # Calculate data range
                    max_val = max(values)
                    min_val = min(values)
                    data_range = max_val - min_val
                    
                    # If the data range is very small, add some padding to make the chart readable
                    if data_range < 0.1:
                        padding = 0.5
                    elif data_range < 1:
                        padding = 1
                    else:
                        # Add padding as a percentage of the data range (20%)
                        padding = data_range * 0.2
                    
                    # Set y-axis limits with appropriate padding
                    plt.ylim(min_val - padding, max_val + padding)
                    
                    # Adjust the y-axis ticks for better readability
                    if data_range < 10:
                        # For small ranges, use more precise tick marks
                        plt.gca().yaxis.set_major_locator(ticker.MaxNLocator(nbins=10))
                    else:
                        plt.gca().yaxis.set_major_locator(ticker.AutoLocator())
                else:
                    # Default if no values
                    plt.ylim(0, 100)


                  # Define Italy's timezone

                if days == 1:
                    min_date = datetime.now(pytz.utc) - timedelta(hours=24)  # Get UTC time
                    min_date = min_date.astimezone(italy_tz)  # Convert to Italy time

                    max_date = datetime.now(pytz.utc).astimezone(italy_tz)  # Convert now to Italy time

                    print("max_time", max(times))  # Ensure times are also in correct timezone

                    plt.xlim(min_date, max_date)
                    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                    plt.gca().xaxis.set_major_locator(plt.MaxNLocator(12))  # At most 12 ticks for hourly view
                elif days == 7:
                    min_date = datetime.now(pytz.utc) - timedelta(days=6)
                    min_date = min_date.astimezone(italy_tz)

                    max_date = datetime.now(pytz.utc).astimezone(italy_tz)

                    plt.xlim(min_date, max_date)
                    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%A'))
                    plt.gca().xaxis.set_major_locator(mdates.DayLocator())  # One tick per day
                elif days == 30:
                    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
                    plt.gca().xaxis.set_major_locator(plt.MaxNLocator(10))  # At most 10 ticks for monthly view
                elif days == 365:
                    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
                    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())

                    # If very few data points, reduce the locator frequency
                    if len(times) < 6:
                        plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=1))
                    
                # Rotate the x-axis labels for better readability
                plt.xticks(rotation=45, ha='right')
                
                # Add grid for better readability
                plt.grid(True, linestyle='--', alpha=0.7)
                
                # Ensure tight layout to avoid clipping labels
                plt.tight_layout()
                
                # Save the figure to a bytes buffer
                img_buf = BytesIO()
                plt.savefig(img_buf, format="jpeg", dpi=100)
                img_buf.seek(0)
                return img_buf
            except Exception as e:
                self.logger.error(f"Error generating chart: {str(e)}")
                raise
            finally:
                plt.close()  # Ensure the figure is closed to free memory

        # Run chart generation in a separate thread
        return await asyncio.get_event_loop().run_in_executor(executor, _generate_chart)

    def _custom_date_formatter(self, times):
        """Custom formatter for date on x-axis when days=1."""
        def formatter(x, pos):
            current_time = mdates.num2date(x)
            local_tz = datetime.now().astimezone().tzinfo
            current_time = current_time.replace(tzinfo=pytz.utc).astimezone(local_tz)
            if pos == 0 or pos == len(times) - 1:
                return current_time.strftime('%d/%m/%y %H:%M')
            return current_time.strftime('%H:%M')
        return formatter

    def GET(self, *args, **kwargs):
        """Handle HTTP GET requests."""
        return asyncio.run(self.get_chart(args, kwargs))

    async def get_chart(self, args, kwargs):
        """Fetch data and generate chart image."""
        if not args or len(args) < 2:
            self.logger.error("Invalid parameters in request")
            raise cherrypy.HTTPError(400, "Missing channel or field ID in request")

        days = int(kwargs.get("days", 1))
        title = kwargs.get("title", "")
        
        # Make sure we fetch only the data for the requested time period
        url = f"https://api.thingspeak.com/channels/{args[0]}/fields/{args[1]}.json?days={days}"
        
        try:
            data = await self.fetch_data(url)
            field_name = data["channel"].get(f"field{args[1]}")
            feeds = data.get("feeds", [])
            if not feeds:
                self.logger.error("No data found for the specified field")
                raise cherrypy.HTTPError(404, "No data found")

            # Parse times and extract values
            times = []
            values = []
            for feed in feeds:
                try:
                    time_val = datetime.strptime(feed['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                    field_val = feed[f"field{args[1]}"]
                    
                    # Only include points with valid values
                    if field_val is not None and field_val != "":
                        times.append(time_val)
                        values.append(float(field_val))
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Skipping invalid data point: {str(e)}")
            
            if not times:
                self.logger.error("No valid data points found")
                raise cherrypy.HTTPError(404, "No valid data found")
                
            self.logger.info(f"Processing {len(times)} data points for {days} days")
            
            # Ensure times are sorted chronologically
            if len(times) > 1:
                # Sort data chronologically
                sorted_data = sorted(zip(times, values), key=lambda x: x[0])
                times, values = zip(*sorted_data)
            
            # Downsample data if necessary
            times_downsampled, values_downsampled = self.downsample_data(times, values, days)
            
            if not times_downsampled:
                self.logger.error("Downsampling resulted in no data points")
                raise cherrypy.HTTPError(500, "Error processing data")
                
            self.logger.info(f"After downsampling: {len(times_downsampled)} data points")
            
            # Generate the chart - pass the default_y_max, but let the chart function adjust based on data
            img_buf = await self.generate_chart(times_downsampled, values_downsampled, field_name, days)
            cherrypy.response.headers['Content-Type'] = 'image/jpeg'
            self.logger.info("Chart image generated and retrieved successfully")
            return img_buf.getvalue()
        except ValueError as ve:
            self.logger.error(f"Value error: {str(ve)}")
            raise cherrypy.HTTPError(400, "Invalid data values")
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            raise cherrypy.HTTPError(500, f"Internal server error: {str(e)}")

    def downsample_data(self, times, values, days, max_points=60):
        """Downsample data to reduce the number of points plotted based on the time period."""
        if not times or not values:
            return [], []
        
        # If we have few points, no need to downsample
        if len(times) <= max_points:
            return list(times), list(values)
        
        # Adjust max_points based on time range
        if days == 1:
            max_points = 24  # For 1 day, show up to 24 points (hourly)
        elif days == 7:
            max_points = 7 * 4  # For 1 week, show up to 28 points (4 per day)
        elif days == 30:
            max_points = 30  # For 1 month, show daily points
        elif days == 365:
            max_points = 12  # For 1 year, show monthly points
        
        # For simple downsampling on small datasets, use linear spacing
        if len(times) <= max_points * 2:
            indices = np.linspace(0, len(times) - 1, max_points, dtype=int)
            return [times[i] for i in indices], [values[i] for i in indices]
        
        # For larger datasets, use time-based aggregation
        result_times = []
        result_values = []
        
        if days == 1:
            # For 1 day, aggregate by hour
            by_hour = {}
            for t, v in zip(times, values):
                hour_key = t.replace(minute=0, second=0, microsecond=0)
                if hour_key in by_hour:
                    by_hour[hour_key].append(v)
                else:
                    by_hour[hour_key] = [v]
            
            for hour, vals in sorted(by_hour.items()):
                result_times.append(hour)
                result_values.append(np.mean(vals))
        
        elif days == 7:
            # For 7 days, aggregate by 6-hour periods
            by_period = {}
            for t, v in zip(times, values):
                # Round to nearest 6-hour period
                hour = t.hour
                period_hour = (hour // 6) * 6
                period_key = t.replace(hour=period_hour, minute=0, second=0, microsecond=0)
                if period_key in by_period:
                    by_period[period_key].append(v)
                else:
                    by_period[period_key] = [v]
            
            for period, vals in sorted(by_period.items()):
                result_times.append(period)
                result_values.append(np.mean(vals))
        
        elif days == 30:
            # For 30 days, aggregate by day
            by_day = {}
            for t, v in zip(times, values):
                day_key = t.replace(hour=0, minute=0, second=0, microsecond=0)
                if day_key in by_day:
                    by_day[day_key].append(v)
                else:
                    by_day[day_key] = [v]
            
            for day, vals in sorted(by_day.items()):
                result_times.append(day)
                result_values.append(np.mean(vals))
        
        elif days == 365:
            # For 365 days, aggregate by month
            by_month = {}
            for t, v in zip(times, values):
                month_key = t.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                if month_key in by_month:
                    by_month[month_key].append(v)
                else:
                    by_month[month_key] = [v]
            
            for month, vals in sorted(by_month.items()):
                result_times.append(month)
                result_values.append(np.mean(vals))
        
        # If we still have too many points after aggregation, downsample
        if len(result_times) > max_points:
            indices = np.linspace(0, len(result_times) - 1, max_points, dtype=int)
            result_times = [result_times[i] for i in indices]
            result_values = [result_values[i] for i in indices]
        
        self.logger.info(f"Downsampled {len(times)} points to {len(result_times)} points for {days} days view")
        return result_times, result_values

if __name__ == '__main__':
    try:
        chart = ThingspeakChart()
        conf = {
            '/': {
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                'tools.sessions.on': True
            }
        }
        cherrypy.config.update({
            'server.socket_host': '0.0.0.0',
            'server.socket_port': 5008
        })
        cherrypy.tree.mount(chart, '/', conf)
        cherrypy.engine.start()
        cherrypy.engine.block()
    except Exception as e:
        print("ERROR OCCUREDD, DUMPING INFO...")
        path = os.path.abspath('./logs/ERROR_chartservice.err')
        with open(path, 'a') as file:
            date = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
            file.write(f"Crashed at : {date}")
            file.write(f"Unexpected error: {e}")
        print(e)
        print("EXITING...")
        sys.exit(1)