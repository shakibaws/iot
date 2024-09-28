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
            details = "days=" + str(kwargs["days"])
        else:
            details = "results=60"
            
        """  if "title" in kwargs:
            details = details + "&title=" + str(kwargs["title"])
        if "color" in kwargs:
            details = details + "&color=" + str(kwargs["color"])
        else:
            details = details + "&color=%23d62020"
        if "bgcolor" in kwargs:
            details = details + "&bgcolor=" + str(kwargs["bgcolor"])
        else:
            details = details + "&bgcolor=%23ffffff" """

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

            locator = mdates.MinuteLocator(interval=5)
            plt.gca().xaxis.set_major_locator(locator)

            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
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
