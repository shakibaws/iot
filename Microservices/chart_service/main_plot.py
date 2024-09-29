import cherrypy
import json
import datetime
import uuid
import requests
import time
import os
import matplotlib
matplotlib.use('Agg')  # Non-interactive backen
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from io import BytesIO
from PIL import Image
from datetime import datetime 

class ThingspeakChart:
    exposed = True
    def __init__(self):
        pass

    def GET(self, *args, **kwargs):
        details = ""

        if "days" in kwargs:
            days = int(kwargs["days"])
            details = "days=" + str(days)
        else:
            days = 1
            details = "days=1"
            
        print(str(details))

        if args[0] and args[1]:
            url = f"https://api.thingspeak.com/channels/{args[0]}/fields/{args[1]}.json?" + details

            response = requests.get(url)
            data = response.json()

            field_name = data["channel"].get(f"field{args[1]}")
            feeds = data.get("feeds", [])
            
            if not feeds:
                raise ValueError("No data found for the specified field.")

            times = [feed['created_at'] for feed in feeds]
            values = [float(feed[f"field{args[1]}"]) for feed in feeds]

            times = [datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%SZ') for time_str in times]

            plt.figure(figsize=(8, 6))
            plt.plot(times, values, marker="o", linestyle="-")
            plt.xlabel("Time")
            plt.ylabel(str(field_name).capitalize())
            plt.title(f"{str(field_name).capitalize()} chart")

            # Custom tick locator and formatter based on days
            if days == 1:
                locator = mdates.HourLocator(interval=1)  # Tick every hour
                plt.gca().xaxis.set_major_locator(locator)

                def custom_date_formatter(x, pos):
                    current_time = mdates.num2date(x)  # Convert the timestamp to datetime object

                    # First and last ticks
                    if pos == 0:  # First tick
                        return current_time.strftime('%d/%m/%y %H:%M')
                    elif pos == len(times) - 1:  # Last tick
                        return current_time.strftime('%d/%m/%y %H:%M')

                    # Format intermediate ticks as HH:MM
                    return current_time.strftime('%H:%M')

                # Apply the custom formatter using ticker.FuncFormatter
                plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(custom_date_formatter))

            elif days == 7:
                # Custom locator to set ticks at 10:00 and 17:00
                locator = mdates.HourLocator(byhour=[7, 19])  # Tick at 10:00 and 17:00
                plt.gca().xaxis.set_major_locator(locator)
                plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%y %H:%M'))

            elif days == 30:
                locator = mdates.DayLocator(interval=1)  # One tick per day
                plt.gca().xaxis.set_major_locator(locator)
                plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%y'))

            elif days == 365:
                locator = mdates.MonthLocator(interval=1)  # One tick per month
                plt.gca().xaxis.set_major_locator(locator)
                plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%B'))

            plt.xticks(rotation=45, ha='right')

            img_buf = BytesIO()
            plt.tight_layout()
            plt.savefig(img_buf, format="jpeg")
            img_buf.seek(0)
            
            cherrypy.response.headers['Content-Type'] = 'image/jpeg'

            return img_buf.getvalue()
        else:
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
