import cherrypy
import json
import datetime
import uuid
import aiohttp
import asyncio
import time
import os
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from io import BytesIO
from PIL import Image
from datetime import datetime
from random import randint
import gc  # garbage collectorx
import threading
import CustomerLogger

class ThingspeakChart:
    exposed = True

    def __init__(self):
        # Create an event loop that will run in a separate thread
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.start_loop, daemon=True)
        self.thread.start()
        self.logger = CustomerLogger.CustomLogger("chart_service", "user_id_test")

    def start_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def fetch_data(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    self.logger.error("error fetching data")
                    raise cherrypy.HTTPError(400, f"Error fetching data: {response.status}")
                return await response.json()

    def GET(self, *args, **kwargs):
        # Schedule `get_chart` to run in the background loop
        future = asyncio.run_coroutine_threadsafe(self.get_chart(args, kwargs), self.loop)
        return future.result()

    async def get_chart(self, args, kwargs):
        # Handle parameters and set chart limits
        days = int(kwargs.get("days", 1))
        title = kwargs.get("title", "default")
        y_max = 100  # Default y-axis limit, can be adjusted based on title

        # URL and data fetch
        if args[0] and args[1]:
            url = f"https://api.thingspeak.com/channels/{args[0]}/fields/{args[1]}.json?days={days}"
            data = await self.fetch_data(url)
            
            field_name = data["channel"].get(f"field{args[1]}")
            feeds = data.get("feeds", [])
            
            if not feeds:
                self.logger.error("error fetching data")
                raise ValueError("No data found for the specified field.")

            times = [datetime.strptime(feed['created_at'], '%Y-%m-%dT%H:%M:%SZ') for feed in feeds]
            values = [float(feed[f"field{args[1]}"]) for feed in feeds]

            # Downsampling
            step = max(1, len(values) // 60)
            times, values = times[::step], values[::step]

            # Plot generation
            plt.figure(figsize=(8, 6))
            plt.plot(times, values, marker="o", linestyle="-")
            plt.xlabel("Time")
            plt.ylabel(field_name.capitalize())
            plt.title(f"{title.capitalize()} chart")
            plt.ylim(0, y_max)
            plt.xticks(rotation=45, ha='right')

            # Format x-axis
            locator, formatter = self.get_locator_and_formatter(days)
            plt.gca().xaxis.set_major_locator(locator)
            plt.gca().xaxis.set_major_formatter(formatter)

            # Save to buffer
            img_buf = BytesIO()
            plt.tight_layout()
            plt.savefig(img_buf, format="jpeg")
            img_buf.seek(0)
            plt.clf()
            plt.close()
            gc.collect()

            # Serve image
            cherrypy.response.headers['Content-Type'] = 'image/jpeg'
            return img_buf.getvalue()

        return {"message": "error"}

    def get_locator_and_formatter(self, days):
        # Helper function to return the right locator and formatter for days
        if days == 1:
            locator = mdates.HourLocator(interval=1)
            formatter = ticker.FuncFormatter(lambda x, pos: mdates.num2date(x).strftime('%H:%M'))
        elif days == 7:
            locator = mdates.HourLocator(byhour=[8, 20])
            formatter = mdates.DateFormatter('%d/%m/%y %H:%M')
        elif days == 30:
            locator = mdates.DayLocator(interval=1)
            formatter = mdates.DateFormatter('%d/%m/%y')
        elif days == 365:
            locator = mdates.MonthLocator(interval=1)
            formatter = mdates.DateFormatter('%B')
        else:
            locator = mdates.AutoDateLocator()
            formatter = mdates.AutoDateFormatter(locator)
        return locator, formatter

if __name__ == '__main__':
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
