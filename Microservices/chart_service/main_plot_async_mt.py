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

    async def generate_chart(self, times, values, field_name, days, y_max):
        """Function to generate chart in a separate thread."""
        def _generate_chart():
            self.logger.info("Generating chart")
            plt.figure(figsize=(8, 6))
            plt.plot(times, values, marker="o", linestyle="-")
            plt.xlabel("Time")
            plt.ylabel(str(field_name).capitalize())
            plt.title(f"{str(field_name).split('_')[0].capitalize()} chart")
            plt.ylim(0, y_max)

            # Set the date format based on days range
            try:
                if days == 1:
                    locator = mdates.HourLocator(interval=1)
                    plt.gca().xaxis.set_major_locator(locator)
                    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(self._custom_date_formatter(times)))

                elif days == 7:
                    locator = mdates.DayLocator(interval=1)
                    plt.gca().xaxis.set_major_locator(locator)
                    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%y'))

                elif days == 30:
                    locator = mdates.DayLocator(interval=2)
                    plt.gca().xaxis.set_major_locator(locator)
                    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%y'))

                if days == 365 and len(times) < 12:
                    plt.xlim(times[0], times[-1])  # Limit to the actual data range
                else:
                    locator = mdates.MonthLocator(interval=1)
                    plt.gca().xaxis.set_major_locator(locator)
                    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m'))
                    
                plt.xticks(rotation=45, ha='right')
                img_buf = BytesIO()
                plt.tight_layout()
                plt.savefig(img_buf, format="jpeg")
                img_buf.seek(0)
                return img_buf
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
        y_max = 100 if title.startswith("soil") else 1000 if title.startswith("light") else 40 if title.startswith("temperature") else 100
        url = f"https://api.thingspeak.com/channels/{args[0]}/fields/{args[1]}.json?days={days}"
        
        try:
            data = await self.fetch_data(url)
            field_name = data["channel"].get(f"field{args[1]}")
            feeds = data.get("feeds", [])
            if not feeds:
                self.logger.error("No data found for the specified field")
                raise cherrypy.HTTPError(404, "No data found")

            times = [datetime.strptime(feed['created_at'], '%Y-%m-%dT%H:%M:%SZ') for feed in feeds]

            values = [feed[f"field{args[1]}"] for feed in feeds]

            filtered_times_values = [(time, float(value)) for time, value in zip(times, values) if value is not None]

            # Unzip the filtered list of tuples into separate times and values lists
            filtered_times, filtered_values = zip(*filtered_times_values) if filtered_times_values else ([], [])


            # Downsample data if necessary
            times1, values1 = self.downsample_data(filtered_times, filtered_values, days)
            
            print(times1)
            img_buf = await self.generate_chart(times1, values1, field_name, days, y_max)
            cherrypy.response.headers['Content-Type'] = 'image/jpeg'
            self.logger.info("Chart image generated and retrieved successfully")
            return img_buf.getvalue()
        except ValueError as ve:
            self.logger.error(f"Value error: {str(ve)}")
            raise cherrypy.HTTPError(400, "Invalid data values")
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            raise cherrypy.HTTPError(500, "Internal server error")

    def downsample_data(self, times, values, days, max_points=60):
        """Downsample data to reduce the number of points plotted based on the time period."""
        # Determine the aggregation interval
        print(days)
        if days == 1:  # Aggregate by hour
            interval = timedelta(hours=1)
            time_format = "%Y-%m-%d %H"
        elif days in [7, 30]:  # Aggregate by day
            interval = timedelta(days=1)
            time_format = "%Y-%m-%d"
        elif days == 365:  # Aggregate by month
            interval = timedelta(days=30)  # Approximate month duration
            time_format = "%Y-%m"
        else:
            # If an unsupported 'days' value is provided, default to hourly aggregation
            interval = timedelta(hours=1)
            time_format = "%Y-%m-%d %H"
        
        # Group data by the specified time period (hour, day, or month)
        aggregated_times = []
        aggregated_values = []
        
        # Initialize variables for the aggregation
        current_group = []
        group_start_time = times[0]

        for time, value in zip(times, values):
            # Determine the group for this data point
            group_key = time.strftime(time_format)
            
            if not current_group:
                current_group.append(value)
            elif time - group_start_time <= interval:
                current_group.append(value)
            else:
                # Aggregate the current group
                aggregated_times.append(group_start_time)
                aggregated_values.append(np.mean(current_group))  # Use the mean as "average"
                
                # Start a new group
                current_group = [value]
                group_start_time = time
        
        # Add the last group
        if current_group:
            aggregated_times.append(group_start_time)
            aggregated_values.append(np.mean(current_group))
        
        # Downsample if the number of points exceeds max_points
        if len(aggregated_values) > max_points:
            interval = len(aggregated_values) // max_points
            aggregated_times = aggregated_times[::interval]
            aggregated_values = aggregated_values[::interval]
        
        return aggregated_times, aggregated_values

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
            'server.socket_port': 5300
        })
        cherrypy.tree.mount(chart, '/', conf)
        cherrypy.engine.start()
        cherrypy.engine.block()
    except Exception as e:
        print("ERROR OCCUREDD, DUMPING INFO...")
        path = os.path.abspath('/app/logs/ERROR_chartservice.err')
        with open(path, 'a') as file:
            date = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
            file.write(f"Crashed at : {date}")
            file.write(f"Unexpected error: {e}")
        print("EXITING...")
        sys.exit(1) 