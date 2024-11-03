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
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from io import BytesIO
from PIL import Image
from datetime import datetime
from random import *
# Thread pool per eseguire operazioni sincrone in thread separati
executor = ThreadPoolExecutor(max_workers=4)
import CustomerLogger
class ThingspeakChart:
    exposed = True

    def __init__(self):
        self.logger = CustomerLogger.CustomLogger("chart_service", "user_id_test")
        pass

    async def fetch_data(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    self.logger.error(f"Error fetching data: {response.status}")
                    raise cherrypy.HTTPError(400, f"Error fetching data: {response.status}")
                return await response.json()

    async def generate_chart(self, times, values, field_name, days):
        """Funzione per generare il grafico in un thread separato"""
        def _generate_chart():
            self.logger.info("Generating chart...")
            plt.figure(figsize=(8, 6))
            plt.plot(times, values, marker="o", linestyle="-")
            plt.xlabel("Time")
            plt.ylabel(str(field_name).capitalize())
            plt.title(f"{str(field_name).capitalize()} chart")

            if days == 1:
                locator = mdates.HourLocator(interval=1)
                plt.gca().xaxis.set_major_locator(locator)

                def custom_date_formatter(x, pos):
                    current_time = mdates.num2date(x)
                    if pos == 0 or pos == len(times) - 1:
                        return current_time.strftime('%d/%m/%y %H:%M')
                    return current_time.strftime('%H:%M')

                plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(custom_date_formatter))

            elif days == 7:
                locator = mdates.HourLocator(byhour=[8, 20])
                plt.gca().xaxis.set_major_locator(locator)
                plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%y %H:%M'))

            elif days == 30:
                locator = mdates.DayLocator(interval=1)
                plt.gca().xaxis.set_major_locator(locator)
                plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%y'))

            elif days == 365:
                locator = mdates.MonthLocator(interval=1)
                plt.gca().xaxis.set_major_locator(locator)
                plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%B'))

            plt.xticks(rotation=45, ha='right')

            img_buf = BytesIO()
            plt.tight_layout()
            plt.savefig(img_buf, format="jpeg")
            img_buf.seek(0)
            self.logger.info("Chart generated successfully")
            return img_buf

        # Eseguire la generazione del grafico in un thread separato
        return await asyncio.get_event_loop().run_in_executor(executor, _generate_chart)

    def GET(self, *args, **kwargs):
        self.logger.info("GET request received")
        return asyncio.run(self.get_chart(args, kwargs))

    async def get_chart(self, args, kwargs):
        details = ""

        if "days" in kwargs:
            days = int(kwargs["days"])
            details = "days=" + str(days)
        else:
            days = 1
            details = "days=1"
        
        if args[0] and args[1]:
            url = f"https://api.thingspeak.com/channels/{args[0]}/fields/{args[1]}.json?" + details

            # Esegui la richiesta asincrona a ThingSpeak
            data = await self.fetch_data(url)

            field_name = data["channel"].get(f"field{args[1]}")
            feeds = data.get("feeds", [])
            
            if not feeds:
                self.logger.error(f"No data found for the specified field:\nchannel: {args[0]}\nfield:{args[1]}.")
                raise ValueError("No data found for the specified field.")

            times = [feed['created_at'] for feed in feeds]
            values = [float(feed[f"field{args[1]}"]) for feed in feeds]

            times = [datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%SZ') for time_str in times]

            # Funzione di downsampling
            def downsample_data(times, values, step=10):
                return times[::step], values[::step]

            # Downsample dei dati
            l = len(values)
            interval = 1
            if l > 60:
                interval = int(l / 60)
         
            times, values = downsample_data(times, values, step=interval)
         
            # Genera il grafico in un thread separato
            img_buf = await self.generate_chart(times, values, field_name, days)

            cherrypy.response.headers['Content-Type'] = 'image/jpeg'
            self.logger.info("GET request successful")
            return img_buf.getvalue()
        else:
            self.logger.error("Invalid parameters provided")
            return {"message": "error"}

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
