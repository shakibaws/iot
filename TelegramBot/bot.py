from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Bot
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import requests
import time
import json
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

resource_catalog_address = ''
service_expose_endpoint = 'http://serviceservice.duck.pictures'
users_list = []
vase_list = []
device_list = []
current_context = None
welcome_message = None
no_vase_found_message = None
vase_found_message = None
global_device_id = ""


def start(update: Update, context: CallbackContext) -> None:
    global welcome_message, users_list
    welcome_message = update.message.reply_text(
        "Welcome to the Smart Vase bot assitance, where you can indentify your plan, get suggestions and so much more!",)
    users_list = []
    context.user_data["vase_list"]=[]
    context.user_data["device_list"]=[]
    context.user_data["current_user"]=None
    handle_endpoints()
    if not is_logged_in(update, context):
        login(update, context)
    else:
        handle_main_actions(update)


def is_logged_in(update: Update, context: CallbackContext):
    current_user = context.user_data.get("current_user")
    isLoggedIn = current_user != None and current_user['telegram_chat_id'] == update.message.chat_id

    print(
        f'is user logged in: {isLoggedIn} loggin_user={current_user} \n chat_id={update.message.chat_id}')
    return isLoggedIn


def login(update: Update, context: CallbackContext):
    global resource_catalog_address, users_list
    users_response = requests.get(f'{resource_catalog_address}/listUser')
    print(users_response.status_code)
    if users_response.status_code == 200:
        users_list = users_response.json()
        for user in users_list:
            if user['telegram_chat_id'] == update.message.chat_id:
                context.user_data["current_user"]=user
                print(f'User found and logged in. User = {user}')
                handle_main_actions(update)
                break
        if context.user_data["current_user"] == None:
            print('User not found')
            signup(update, context)


def handle_endpoints():
    global resource_catalog_address, service_expose_endpoint
    resource_endpoint_response = requests.get(f'{service_expose_endpoint}/all')
    if resource_endpoint_response.status_code == 200:
        resource_catalog_address = resource_endpoint_response.json(
        )['services']['resource_catalog_address']


def remove_message(update: Update, context: CallbackContext,message, is_query: bool = False):
    context.bot.delete_message(
        chat_id=update.callback_query.message.chat_id if is_query else update.message.chat_id, message_id=message.message_id)


def signup(update: Update, context:CallbackContext):
    global welcome_message
    time.sleep(1)
    #remove_message(update, context, welcome_message)
    signup_message = update.message.reply_text(
        "It seems like you are new here. We are creating an account for you!",)
    print('Signing up')
    signup_response = requests.post(
        f'{resource_catalog_address}/user',
        json={'telegram_chat_id': update.message.chat_id}
    )
    if signup_response.status_code == 200:
        print('User signed up')
        time.sleep(2)
        #remove_message(update, context, signup_message)
        signup_confirm_message = update.message.reply_text(
            "Done 🎉, now let's get started!"
        )
        time.sleep(1)
        login(update, context)
        #remove_message(update, context, signup_confirm_message)


def handle_main_actions(update: Update):
    keyboard = [
        [InlineKeyboardButton(
            "Add a new Smart Vase", callback_data='add_vase')],
        [InlineKeyboardButton(
            "See the list of connected Smart Vases", callback_data='vase_list')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "Let's get started 🚀. How can I help you?", reply_markup=reply_markup)


def add_vase(update:Update, context: CallbackContext):
    global resource_catalog_address
    current_user = context.user_data.get("current_user")

    addingVaseInstructions = f"Follow these steps to activate it:\n\n1. Please turn on the vase and WIFI on your phone.\n\n2. You should see a WIFI network called 'SmartVase', please connect to it and then click on **[here](http://192.168.4.1/?user_id={current_user['user_id']})** \n\n3. Once you have completed the steps, please connect to the internet, and check your new list of Smart Vases ⬇️"
    print('User want to add a new device')
    if update.callback_query:
        message = update.callback_query.message
    else:
        message = update.message
    keyboard = [
        [InlineKeyboardButton(
            "Refresh my Vase List", callback_data='vase_list')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    no_vase_found_message = message.reply_text(
        f"{addingVaseInstructions}", parse_mode='Markdown', reply_markup=reply_markup)

def get_user_vase_list(update: Update, context: CallbackContext):
    global resource_catalog_address, no_vase_found_message
    current_user = context.user_data.get("current_user")
    vase_list = context.user_data.get("vase_list")
    device_list = context.user_data.get("device_list")

    if no_vase_found_message != None:
        #remove_message(update, context, no_vase_found_message, True)
        no_vase_found_message = None
    vase_list_response = requests.get(f'{resource_catalog_address}/listVase')
    device_list_response = requests.get(f'{resource_catalog_address}/listDevice')

    addingVaseInstructions = f" If you already have got a smart vase, please follow these steps to activate it:\n\n1. Please turn on the vase and WIFI on your phone.\n\n2. You should see a WIFI network called 'SmartVase', please connect to it and then click on **[here](http://192.168.4.1/?user_id={current_user['user_id']})** \n\n3. Once you have completed the steps, please connect to the internet, and check your new list of Smart Vases ⬇️"
    print('Getting list vase')
    keyboard_list = []
    if vase_list_response.status_code == 200:
        global_vase_list = vase_list_response.json()
        for vase in global_vase_list:
            if vase['user_id'] == current_user['user_id'] and not vase in vase_list:
                vase_list.append(vase)
                print(f"{vase_list}")
                
    if device_list_response.status_code == 200 and vase_list_response.status_code == 200:
        global_device_list = device_list_response.json()
        for device in global_device_list:
            if device['user_id'] == current_user['user_id'] and not device in device_list:
                device_list.append(device)
                print(f"{device_list}")

        if device_list:
            print('User has some devices')
            for dev in device_list:
                name = "Vase "+ dev['device_id']
                vase = find_device_in_list_via_device_id(dev['device_id'], vase_list)
                if vase:
                     name = vase["vase_name"]
                callback_data = f'vase_info_{dev["device_id"]}'
                keyboard_list.append([InlineKeyboardButton(name, callback_data=callback_data)])
                
            if update.callback_query:
                message = update.callback_query.message
            else:
                message = update.message
            
            keyboard = keyboard_list
            reply_markup = InlineKeyboardMarkup(keyboard)
            vase_found_message = message.reply_text(
                f"Here all your vases!", parse_mode='Markdown', reply_markup=reply_markup)
        
        else:
            print('User has NO devices')
            if update.callback_query:
                message = update.callback_query.message
            else:
                message = update.message
            keyboard = [
                [InlineKeyboardButton(
                    "Refresh my Vase List", callback_data='vase_list')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            no_vase_found_message = message.reply_text(
                f"You have no smart vases connected!\n {addingVaseInstructions}", parse_mode='Markdown', reply_markup=reply_markup)
            
def show_graph(name: str, field_number: int, channel_id: str, days: int, context: CallbackContext) -> None:
    
    chart_url = f"http://thingspeak.duck.pictures/{channel_id}/{field_number}?title={name}%20chart&days={str(days)}"
    #chart_url = f"http://localhost:5300/{channel_id}/{field_number}?title={name}%20chart&days={str(days)}"
    # Local

    current_user = context.user_data.get("current_user")
    chat_id = current_user['telegram_chat_id']
    live_chart = f"https://thingspeak.com/channels/{channel_id}/charts/{field_number}?bgcolor=%23ffffff&color=%23d62020&dynamic=true&days={days}&type=line&update=15&title={str(name).capitalize}%20chart"
    # Send feedback to the user that the chart is being generated
    bot = Bot(token="7058374905:AAFJc4qnJjW5TdDyTViyjW_R6PzcSqR22CE")
    bot.send_message(chat_id=chat_id, text=f"Plotting the {name} chart, please wait...")

    # Set up retries and timeouts
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    try:
        # Increase the timeout to 60 seconds
        response = session.get(chart_url, timeout=60)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Send the chart image to the Telegram chat
            bot.send_photo(chat_id=chat_id, photo=response.content, caption=f"{name} chart\nYou can see the {name} chart here:\n {live_chart}")
        else:
            bot.send_message(chat_id=chat_id, text=f"Failed to generate {name} chart. Please try again later. You can see the {name} chart here: {live_chart}")
            print(f"Failed to get chart: {response.status_code}")

    except requests.exceptions.Timeout:
        # Handle timeout errors and notify the user
        bot.send_message(chat_id=chat_id, text=f"Timeout while generating {name} chart. Please try again later.")
        print(f"Request timed out for {chart_url}")

    except requests.exceptions.RequestException as e:
        # Handle other possible exceptions and notify the user
        bot.send_message(chat_id=chat_id, text=f"Error while generating {name} chart. Please try again later.")
        print(f"Error occurred: {e}")
        
# Callback action dispatcher
def button(update: Update, context: CallbackContext) -> None:
    global global_device_id
    query = update.callback_query
    query.answer()

    if query.data.startswith('configure'):
        # Extract device_id from callback_data
        device_id = query.data.split('_')[1]
        global_device_id = device_id
        query.edit_message_text(
            text="First, please send me an image of your plant so that I can identify it!")
    elif query.data.startswith('chart_'):
        parameter_type = query.data.split('_')[1]
        channel_id = query.data.split('_')[2]
        x = query.data.split('_')[3]
        days=1
        if x=="month":
            days=30
        if x=="year":
            days=365
        if x=="week":
            days=7

        if parameter_type == 'temperature':
            show_graph("temperature", 1, channel_id, days, context)
        elif parameter_type == 'light':
            show_graph("light", 3, channel_id, days, context)
        elif parameter_type == 'watertank':
            show_graph("watertank", 4, channel_id, days, context)
        elif parameter_type == 'soil':
            show_graph("soil_mosture", 2, channel_id, days, context)
        
            
    elif query.data.startswith('details_'):
        parameter_type = query.data.split('_')[1]
        channel_id = query.data.split('_')[2]
        keyboard = [
                [
                InlineKeyboardButton(
                    f"1 day", callback_data='chart_temperature_'+str(channel_id)+"_day"), 
                InlineKeyboardButton(
                    f"last 7 days", callback_data='chart_light_'+str(channel_id)+"_week")],   
                [InlineKeyboardButton(
                    f"last 30 days", callback_data='chart_watertank_'+str(channel_id)+"_month"), 
                InlineKeyboardButton(
                    f"last year", callback_data='chart_soil_'+str(channel_id)+"_year")
                ]
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.callback_query.message.reply_text(text=f"Select the time range for the chart", reply_markup=reply_markup) 

       
    elif query.data.startswith('no_details_'):
        parameter_type = query.data.split('_')[2]
        update.callback_query.message.reply_text(text=f"Sorry, still no data for {parameter_type}")    
    elif query.data == 'add_vase':
        global_device_id = ""
        add_vase(update, context)
    elif query.data == 'vase_list':
        global_device_id = ""
        get_user_vase_list(update, context)
    elif query.data.startswith('vase_info_'):
        # Extract device_id from callback_data
        device_id = query.data.split('_')[2]
        vase_details(update, context, device_id)
        
def find_device_in_list_via_device_id(device_id, item_list):
    for item in item_list:
        if item['device_id'] == device_id:
            return item  # Restituisce l'oggetto dispositivo se trovato
    return None  # Restituisce None se non trovato

def vase_details(update: Update, context: CallbackContext, device_id: str):
    vase_list = context.user_data.get("vase_list")
    device_list = context.user_data.get("device_list")
    vase = find_device_in_list_via_device_id(device_id, vase_list)
    dev = find_device_in_list_via_device_id(device_id, device_list)
    channel_id = dev['channel_id']
    print(channel_id)
    if vase:
        res = requests.get(f"https://api.thingspeak.com/channels/{str(channel_id)}/feeds.json?results=1").json()
        if len(res["feeds"])>0:
            data = res['feeds'][0]
            temperature = data['field1']
            light_level = data['field3']
            watertank_level = data['field4']
            soil_moisture = data['field2']
            keyboard = [
                [
                InlineKeyboardButton(
                    f"Temperature = {temperature}", callback_data='details_temperature_'+str(channel_id)), 
                InlineKeyboardButton(
                    f"Light = {light_level}", callback_data='details_light_'+str(channel_id))],   
                [
                InlineKeyboardButton(
                    f"Watertank = {watertank_level}", callback_data='details_watertank_'+str(channel_id)), 
                InlineKeyboardButton(
                    f"Soil = {soil_moisture}", callback_data='details_soil_'+str(channel_id))],
                [
                InlineKeyboardButton(
                    "Go back", callback_data='vase_list')]     
            ]
        else:
            keyboard = [
                [
                InlineKeyboardButton(
                    f"Temperature", callback_data='no_details_temperature'), 
                InlineKeyboardButton(
                    f"Light", callback_data='no_details_light')],   
                [
                InlineKeyboardButton(
                    f"Watertank", callback_data='no_details_watertank'), 
                InlineKeyboardButton(
                    f"Soil", callback_data='no_details_soil')],
                [
                InlineKeyboardButton(
                    "Go back", callback_data='vase_list')]     
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.callback_query.message.reply_text('<b>'+f"Details for Vase:\n {vase['vase_name']}\nSuggested moisture(humidity) of the ground: \nMin:{int(vase['plant']['soil_moisture_min'])*10}\nMax:{int(vase['plant']['soil_moisture_max'])*10}\nSuggested temperature range: \nMin:\n{vase['plant']['temperature_min']}\nMax:{vase['plant']['temperature_max']}\n\nDescription:\n{vase['plant']['description']}"+'</b>', parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    else:
        device = find_device_in_list_via_device_id(device_id, vase_list)

        keyboard = [
                [InlineKeyboardButton(
                    "Yes", callback_data='configure_'+device_id), 
                InlineKeyboardButton(
                    "No", callback_data='vase_list')],
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.callback_query.message.reply_text(f"Do you want to setup this vase now?", parse_mode='Markdown', reply_markup=reply_markup)
        
        
def handle_photo(update: Update, context: CallbackContext) -> None:
    global global_device_id
    if not global_device_id:
        update.message.reply_text("Make sure to select a vase before trying to upload")
        return
    
    photo_file = update.message.photo[-1].get_file()
    file_path = f"{photo_file.file_id}.jpg"
    photo_file.download(file_path)
    update.message.reply_text(
        "Image received, let's see...")
    url = "http://recommendationservice.duck.pictures"
    try:
        with open(file_path, 'rb') as file:
            files = {'images': (file_path, file, 'image/jpeg')}
            response = requests.post(url, files=files)

        if response.status_code == 200:

            update.message.reply_text('Image uploaded to server successfully!')

            print("Raw response text:", repr(response.text))
            
            # Remove extra backslashes and parse
            cleaned_json_string = response.text.replace('\\n', '').replace('\\"', '"')

            print("Cleaned JSON string:", cleaned_json_string)
            try:
                chat_response = json.loads(cleaned_json_string)
            except json.JSONDecodeError as json_err:
                print(f"Failed to parse JSON: {json_err}")
                update.message.reply_text('Failed to parse the server response.')
                return
            
            # Ensure that chat_response is a valid dictionary
            if chat_response and isinstance(chat_response, dict):
                print("Creating vase")
                # Check if required keys are present
                required_keys = ['plant_name', 'soil_moisture_min', 'hours_sun_suggested', 
                                'soil_moisture_max', 'temperature_min', 'temperature_max', 'description']
                missing_keys = [key for key in required_keys if key not in chat_response]
                if missing_keys:
                    print(f"Missing keys in response: {missing_keys}")
                    update.message.reply_text(f'Missing data in response: {", ".join(missing_keys)}')
                    return

                # Construct the new vase dictionary
                new_vase = {
                    'device_id': global_device_id,
                    'vase_name': "Vase" + chat_response['plant_name'],  # Using the plant name from the response
                    'user_id': context.user_data['current_user']['user_id'],
                    'vase_status': 'active',
                    'plant': {
                        'plant_name': chat_response['plant_name'],
                        'plant_schedule_water': chat_response['soil_moisture_min'],
                        'plant_schedule_light_level': chat_response['hours_sun_suggested'],  # Use hours of sunlight suggestion
                        'soil_moisture_min': chat_response['soil_moisture_min'],
                        'soil_moisture_max': chat_response['soil_moisture_max'],
                        'hours_sun_min': chat_response['hours_sun_suggested'],
                        'temperature_min': chat_response['temperature_min'],
                        'temperature_max': chat_response['temperature_max'],
                        'description': chat_response['description']
                    }
                }

                print("Post add vase")
                res = requests.post(f"{resource_catalog_address}/vase", json=new_vase)

                if res.status_code == 200:
                    update.message.reply_text(f"Vase with {chat_response['plant_name']} added successfully")
                else:
                    update.message.reply_text('Vase not added, error')

        else:
            print(response.text)
            update.message.reply_text(
                'Failed to upload the image.')
    except Exception as e:
        print(e)
        update.message.reply_text('Somthing went wrong...')


def main() -> None:
    updater = Updater("7058374905:AAFJc4qnJjW5TdDyTViyjW_R6PzcSqR22CE")
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("vase_list", get_user_vase_list))
    dispatcher.add_handler(CommandHandler("add_vase", add_vase))
    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(MessageHandler(Filters.photo, handle_photo))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
