import cherrypy
import json
import datetime
import uuid
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image
import time
import io
import os

def iframe_to_image(iframe_url, output_image_path='chart_image.png'):
    # Ensure the directory exists
    output_dir = os.path.dirname(output_image_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Configure Selenium to use headless Chrome
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    # Initialize the Chrome WebDriver
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Open the iframe URL in the browser
        driver.get(iframe_url)

        # Zoom the page to 150%
        driver.execute_script("document.body.style.zoom='250%'")

        # Wait for the page to load the dynamic content (if necessary)
        time.sleep(10)  # Adjust this delay based on your needs

        # Take screenshot of the full page (or a specific element)
        screenshot = driver.get_screenshot_as_png()

        # Open the image using PIL for further processing (optional)
        image = Image.open(io.BytesIO(screenshot))

        # Save the screenshot
        image.save(output_image_path)

        print(f"Screenshot saved as {output_image_path}")

    finally:
        # Close the browser after taking the screenshot
        driver.quit()


class ThingspeakChart:
    exposed = True
    def __init__(self):
        pass

    def GET(self, *args, **kwargs):
        # Construct the URL for the ThingSpeak chart
        details = ""
        if "title" in kwargs:
            details = details + "&title=" + str(kwargs["title"])
        if "days" in kwargs:
            details = details + "&days=" + str(kwargs["days"])
        else:
            details = details + "&results=60"
        if "color" in kwargs:
            details = details + "&color=" + str(kwargs["color"])
        else:
            details = details + "&color=%23d62020"
        if "bgcolor" in kwargs:
            details = details + "&bgcolor=" + str(kwargs["bgcolor"])
        else:
            details = details + "&bgcolor=%23ffffff"
        
            
        url = f"https://thingspeak.com/channels/{args[0]}/charts/{args[1]}?type=line" + details
        image_path = './tmp_images/chart_image.png'

        # Call the function to take a screenshot
        iframe_to_image(url, image_path)

        # Set the content type to an image
        cherrypy.response.headers['Content-Type'] = 'image/png'

        # Open the image and send it in the response
        with open(image_path, 'rb') as f:
            image_data = f.read()

        # Delete the image after sending the response
        try:
            os.remove(image_path)
            print(f"Deleted file: {image_path}")
        except Exception as e:
            print(f"Error deleting file: {e}")

        return image_data


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
        'server.socket_port': 5300  # Specify your desired port here
    })
    cherrypy.tree.mount(chart, '/', conf)
    cherrypy.engine.start()
    cherrypy.engine.block()
