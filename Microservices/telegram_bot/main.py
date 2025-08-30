
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext
import requests
import time
import json
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import asyncio
import aiohttp
import aiofiles
import CustomerLogger
import os
from dotenv import load_dotenv
import datetime
import sys

resource_catalog_address = ''
telegramgroups_address = ''
service_expose_endpoint = 'http://service_catalog:5001'
vase_list = []
device_list = []
current_context = None
welcome_message = None
no_vase_found_message = None
vase_found_message = None
logger = CustomerLogger.CustomLogger(service_name="telegram_bot")

#lets the bot handle many users and requests concurrently 
#without spawning threads or freezing while waiting for network responses
async def start(update: Update, context: CallbackContext) -> None:
    logger.info(f"Start command received from chat_id: {update.message.chat_id}")
    welcome_message = await update.message.reply_text(
        "*Welcome to the Smart Vase bot assistance!*\n"
        "🌱 *Identify your plant*, get suggestions, and so much more! Let's get started 🚀.",
        parse_mode='Markdown'
    )
    context.user_data["vase_list"]=[]
    context.user_data["device_list"]=[]
    context.user_data["current_user"]=None

    await handle_endpoints()
    if not await is_logged_in(update, context):
        print("login")
        logger.info("User not logged in, proceeding to login")
        await login(update, context)
    else:
        print("handle main actions")
        logger.info("User already logged in, handling main actions")
        await handle_main_actions(update)


async def is_logged_in(update: Update, context: CallbackContext):
    current_user = context.user_data.get("current_user")
    isLoggedIn = current_user != None and current_user['telegram_chat_id'] == update.message.chat_id

    print(
        f'is user logged in: {isLoggedIn} loggin_user={current_user} \n chat_id={update.message.chat_id}')
    logger.info(f"Login check - isLoggedIn: {isLoggedIn}, chat_id: {update.message.chat_id}")
    return isLoggedIn


async def login(update: Update, context: CallbackContext):
    global resource_catalog_address
    logger.info(f"Login attempt for chat_id: {update.message.chat_id}")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{resource_catalog_address}/listUser') as response:
            if response.status == 200:
                logger.info("Successfully retrieved user list from resource catalog")
                users_list =json.loads(await response.text())
                for user in users_list:
                    if user['telegram_chat_id'] == update.message.chat_id:
                        context.user_data["current_user"]=user
                        print ("user", user)
                        print ("user['user_id']", user['user_id'])
                        logger.setUserId(user['user_id'])
                        await update.message.reply_text(
                            "✅ *Login successful!*\n"
                            "You're now logged in and ready to manage your Smart Vases.",
                            parse_mode='Markdown'
                        )
                        logger.info("user logged in")
                        await handle_main_actions(update)
                        break
                if context.user_data["current_user"] == None:
                    print('User not found')
                    logger.info("User not found in database, proceeding to signup")
                    await signup(update, context)
            else:
                logger.error(f"Failed to retrieve user list. Status: {response.status}")


async def handle_endpoints():
    global resource_catalog_address, telegramgroups_address, service_expose_endpoint
    logger.info("Handling endpoints to get service catalog")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{service_expose_endpoint}/all') as response:
                if response.status == 200:
                    json_response =json.loads(await response.text())
                    resource_catalog_address = json_response['services']['resource_catalog']
                    telegramgroups_address = json_response['services'].get('telegram_groups')
                    logger.info(f"Successfully retrieved resource catalog address: {resource_catalog_address}")
                    logger.info(f"Successfully retrieved telegramgroups address: {telegramgroups_address}")
                else:
                    logger.error(f"Error performing get /all on service catalog. Status: {response.status}")
    except Exception as e:
        logger.error(f"Exception in handle_endpoints(): {str(e)}")


""" def remove_message(update: Update, context: CallbackContext,message, is_query: bool = False):
    context.bot.delete_message(
        chat_id=update.callback_query.message.chat_id if is_query else update.message.chat_id, message_id=message.message_id)
"""

# Signup function
async def signup(update: Update, context):
    global resource_catalog_address
    logger.info(f"Signup attempt for chat_id: {update.message.chat_id}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{resource_catalog_address}/user', json={'telegram_chat_id': update.message.chat_id}) as response:
                if response.status == 200:
                    logger.info("User signup successful, proceeding to login")
                    await login(update, context)
                else:
                     logger.error(f"Error performing signup. Status: {response.status}")
    except Exception as e:
        logger.error(f"Exception in signup(): {str(e)}")


async def handle_main_actions(update: Update):
    logger.info("Displaying main actions menu")
    keyboard = [
    [InlineKeyboardButton("🌱 Add a new Smart Vase", callback_data='add_vase')],
    [InlineKeyboardButton("📜 See the list of connected Smart Vases", callback_data='vase_list')],
    [InlineKeyboardButton("🏥 Identify Plant Disease", callback_data='identify_disease')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "💡 *What would you like to do?*", reply_markup=reply_markup, parse_mode='Markdown'
    )

async def add_vase(update: Update, context):
    current_user = context.user_data.get("current_user")
    logger.info(f"Add vase request from user_id: {current_user['user_id'] if current_user else 'unknown'}")
    instructions = (
        "🛠️ *Follow these steps to add a new Smart Vase:*\n\n" +
        "1️⃣ *Turn on* the vase and your phone's Wi-Fi.\n" +
        f"2️⃣ *Connect* to the 'SmartVase' network and click [here](http://0.0.0.0:5004/?user_id={current_user['user_id']}).\n" +
        "3️⃣ *Reconnect* to the internet and check your vase list."
    )
    if update.callback_query:
        message = update.callback_query.message
    else:
        message = update.message
    
    await message.reply_text(instructions, parse_mode='Markdown')
   
async def get_user_vase_list(update: Update, context):
    global resource_catalog_address
    current_user = context.user_data.get("current_user")
    vase_list = context.user_data.get("vase_list")
    device_list = context.user_data.get("device_list")
    logger.info(f"Getting vase list for user_id: {current_user['user_id'] if current_user else 'unknown'}")
    try:
        async with aiohttp.ClientSession() as session:
            if update.callback_query:
                    message = update.callback_query.message
            else:
                    message = update.message

            vase_list_response = await session.get(f"{resource_catalog_address}/listVaseByUser/{current_user['user_id']}")
            device_list_response = await session.get(f"{resource_catalog_address}/listDeviceByUser/{current_user['user_id']}")
            if vase_list_response.status == 200:
                vase_list = await vase_list_response.json()
                logger.info(f"Successfully retrieved vase list for user")
            else: 
                logger.error(f"Error on vase_list in get_user_vase_list(). Status: {vase_list_response.status}")
                await message.reply_text("Something went wrong...", reply_markup=reply_markup, parse_mode='Markdown')
                return

            if device_list_response.status == 200:
                device_list = await device_list_response.json()
                logger.info(f"Successfully retrieved device list for user")
            else:
                logger.error(f"Error on device_list in get_user_vase_list(). Status: {device_list_response.status}")
                await message.reply_text("Something went wrong...", reply_markup=reply_markup, parse_mode='Markdown')
                return
            # Generate response based on the retrieved devices
            if device_list:
                keyboard_list = []
                print('User has some devices')
                logger.info(f"User has {len(device_list)} devices")
                for dev in device_list:
                    name = "🌸 Vase " + dev['device_id']
                    vase = find_device_in_list_via_device_id(dev['device_id'], vase_list)
                    if vase:
                        print(f"vase found : {vase}")
                        logger.info(f"Vase found for device {dev['device_id']}: {vase['vase_name']}")
                        name = f"🌿 {vase['vase_name']}"
                    else:
                        logger.info(f"No vase configuration found for device {dev['device_id']}")
                    callback_data = f'vase_info_{dev["device_id"]}'
                   
                    keyboard_list.append([InlineKeyboardButton(name, callback_data=callback_data)])            
                if update.callback_query:
                    message = update.callback_query.message
                else:
                    message = update.message           
                reply_markup = InlineKeyboardMarkup(keyboard_list)
                await message.reply_text("*Here are your connected vases:*", reply_markup=reply_markup, parse_mode='Markdown')
            else:
                logger.info("User has no devices connected")
                keyboard = [[InlineKeyboardButton("🔄 Refresh my Vase List", callback_data='vase_list')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                if update.callback_query:
                    message = update.callback_query.message
                else:
                    message = update.message
                await message.reply_text(
                    "⚠️ *No smart vases connected!*",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                ) 
    except Exception as e:
        logger.error(f"Exception on get_user_vase_list(): {str(e)}")

# Show graph for a vase
async def show_graph(name: str, field_number: int, channel_id: str, days: int, context, update: Update):
    logger.info(f"Generating chart for {name}, channel_id: {channel_id}, days: {days}")
    service_catalog = requests.get(f"{service_expose_endpoint}/all").json()
    chart_service = service_catalog['services']['chart_service']

    chart_url = f"{chart_service}/{channel_id}/{field_number}?title={name}%20chart&days={str(days)}"
    live_chart = f"https://thingspeak.com/channels/{channel_id}/charts/{field_number}?dynamic=true&days={days}"

    await update.callback_query.message.reply_text(text=f"📊 *Plotting the {name} chart*, please wait...", parse_mode='Markdown')
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(chart_url, timeout=60) as response:
                if response.status == 200:
                    image_data = await response.read()
                    logger.info(f"Successfully generated chart for {name}")
                    await update.callback_query.message.reply_photo(photo=image_data, caption=f"{name} chart\nYou can see the {name} chart here:\n {live_chart})")
                else:
                    #logger.error("error while getting chart:" + response)
                    await update.callback_query.message.reply_text(text=f"Failed to generate {name} chart.")
                    print("here")
                    logger.error(f"Error while getting chart: HTTP status code {response.status}")
        except asyncio.TimeoutError:
            logger.error("Timeout while generating chart in show_graph()")
            await update.callback_query.message.reply_text(text="Timeout while generating chart.")
 

# Handle button presses
async def button(update: Update, context):
    query = update.callback_query
    logger.info(f"Button pressed: {query.data}")
    try:
        await query.answer()

        if query.data.startswith('configure'):
            # Extract device_id from callback_data
            device_id = query.data.split('_')[1]
            context.user_data["global_device_id"] = device_id
            await query.edit_message_text(
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

            logger.info(f"Chart request for {parameter_type}, channel_id: {channel_id}, time period: {x} ({days} days)")

            if parameter_type == 'temperature':
                await show_graph("temperature", 1, channel_id, days, context, update)
            elif parameter_type == 'light':
                await show_graph("light", 3, channel_id, days, context, update)
            elif parameter_type == 'watertank':
                await show_graph("watertank", 4, channel_id, days, context, update)
            elif parameter_type == 'soil':
                await show_graph("soil_mosture", 2, channel_id, days, context, update)
            
                
        elif query.data.startswith('details_'):
            parameter_type = query.data.split('_')[1]
            channel_id = query.data.split('_')[2]
            print(parameter_type)
            logger.info(f"Details request for {parameter_type}, channel_id: {channel_id}")
            keyboard = [
                    [
                    InlineKeyboardButton(
                        f"1 day", callback_data=f'chart_{parameter_type}_'+str(channel_id)+"_day"), 
                    InlineKeyboardButton(
                        f"last 7 days", callback_data=f'chart_{parameter_type}_'+str(channel_id)+"_week")],   
                    [InlineKeyboardButton(
                        f"last 30 days", callback_data=f'chart_{parameter_type}_'+str(channel_id)+"_month"), 
                    InlineKeyboardButton(
                        f"last year", callback_data=f'chart_{parameter_type}_'+str(channel_id)+"_year")
                    ]
                ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.message.reply_text(text=f"Select the time range for the chart", reply_markup=reply_markup) 
        elif query.data.startswith('no_details_'):
            parameter_type = query.data.split('_')[2]
            await update.callback_query.message.reply_text(text=f"Sorry, still no data for {parameter_type}")    
        elif query.data.startswith('edit_vase_'):
            device_id = query.data.split('_')[2]
            context.user_data["global_device_id"] = device_id
            logger.info(f"Edit vase request for device_id: {device_id}")
            keyboard = [
                [InlineKeyboardButton("🌸 Vase Name", callback_data='edit_params_vasename')],
                [InlineKeyboardButton("☀️ Min Hours of Light", callback_data='edit_params_hourssun')],
                [InlineKeyboardButton("💧 Min Soil Moisture", callback_data='edit_params_minsoilmoisture')],
                [InlineKeyboardButton("🌊 Max Soil Moisture", callback_data='edit_params_maxsoilmoisture')],
                [InlineKeyboardButton("🌡️ Min Temperature", callback_data='edit_params_mintemperature')],
                [InlineKeyboardButton("🔥 Max Temperature", callback_data='edit_params_maxtemperature')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.message.reply_text(
                text=(
                    "⚙️ *Edit Vase Parameters*\n\n"
                    "Please select a parameter to update from the list below:\n\n"
                    "🌸 *Vase Name*: The identifier for your vase.\n"
                    "☀️ *Min Hours of Light*: Minimum daily light hours.\n"
                    "💧 *Min Soil Moisture*: Lowest acceptable soil moisture.\n"
                    "🌊 *Max Soil Moisture*: Highest acceptable soil moisture.\n"
                    "🌡️ *Min Temperature*: Lowest acceptable temperature.\n"
                    "🔥 *Max Temperature*: Highest acceptable temperature."
                ),
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )

        elif query.data.startswith('edit_params_'):
            param = query.data.split('_')[2]
            # save param to context
            context.user_data["param_to_edit"] = param
            match(param):
                case 'vasename':
                    await update.callback_query.message.reply_text(
                        text="✏️ *Rename Vase*\n\nWrite the new name for your vase.",
                        parse_mode="Markdown"
                    )
                case 'hourssun':
                    await update.callback_query.message.reply_text(
                        text="☀️ *Edit Minimum Hours of Light*\n\nInsert the new value in Hours.\n\n Range: \\[*Min*: 1, *Max*: 24\\]",
                        parse_mode="Markdown"
                    )
                case 'minsoilmoisture':                    
                    await update.callback_query.message.reply_text(
                        text="💧 *Edit Minimum Soil Moisture*\n\nInsert the new value in %.\n\n Range: \\[*Min*: 10, *Max*: 90\\]",
                        parse_mode="Markdown"
                    )
                case 'maxsoilmoisture':
                    await update.callback_query.message.reply_text(
                        text="🌊 *Edit Maximum Soil Moisture*\n\nInsert the new value in %.\n\n Range: \\[*Min*: 10, *Max*: 90\\]",
                        parse_mode="Markdown"
                    )
                case 'mintemperature':                    
                    await update.callback_query.message.reply_text(
                        text="🌡️ *Edit Minimum Temperature*\n\nInsert the new value in °C.\n\n Range: \\[*Min*: 0, *Max*: 50\\]",
                        parse_mode="Markdown"
                    )
                case 'maxtemperature':
                    await update.callback_query.message.reply_text(
                        text="🔥 *Edit Maximum Temperature*\n\nInsert the new value in °C.\n\n Range: \\[*Min*: 0, *Max*: 50\\]",
                        parse_mode="Markdown"
                    )
        elif query.data == 'add_vase':
            context.user_data["global_device_id"] = ""
            logger.info("Add vase button pressed")
            await add_vase(update, context)
        elif query.data == 'vase_list':
            context.user_data["global_device_id"] = ""
            logger.info("Vase list button pressed")
            await get_user_vase_list(update, context)
        elif query.data.startswith('vase_info_'):
            # Extract device_id from callback_data
            device_id = query.data.split('_')[2]
            logger.info(f"Vase info request for device_id: {device_id}")
            await vase_details(update, context, device_id)
        elif query.data == 'identify_disease':
            logger.info("Disease identification request")
            await handle_disease_identification_request(update, context)
    except Exception as e:
            logger.error(f"Exception on button(): {str(e)}")
      
def find_device_in_list_via_device_id(device_id, item_list):
    for item in item_list:
        if item['device_id'] == device_id:
            print(f"item found: {item}")
            logger.info(f"Device found in list: {device_id}")
            return item  
    logger.info(f"Device not found in list: {device_id}")
    return None  

async def vase_details(update: Update, context, device_id: str):
    logger.info(f"Getting vase details for device_id: {device_id}")
    try:
        service_catalog = requests.get(f"{service_expose_endpoint}/all").json()
        data_analysis_service = service_catalog['services']['data_analysis']
        async with aiohttp.ClientSession() as session:
            res = await session.get(f"{resource_catalog_address}/device/{device_id}")
            dev = await res.json()
            res = await session.get(f"{resource_catalog_address}/vaseByDevice/{device_id}")
            vase = await res.json()
        
        channel_id = dev['channel_id']
        if vase:
            print(f"vase details: {vase}")
            logger.info(f"Vase configuration found: {vase['vase_name']}")
            async with aiohttp.ClientSession() as session:
                response = await session.get(f"{data_analysis_service}/{str(device_id)}")
                res = json.loads(await response.text())
                print(f"response: {res}")
                logger.info(f"Data analysis response received for device {device_id}")
                temperature = res.get('temperature', 0)
                light_level = res.get('light_level', 0)
                watertank_level = res.get('watertank_level', 0)
                soil_moisture = res.get('soil_moisture', 0)

                # Update the buttons with emojis and improve formatting
                keyboard = [
                    [
                        InlineKeyboardButton(f"🌡️ Temperature: {float(temperature):.2f} °C", callback_data=f'details_temperature_{channel_id}')],
                    [
                        InlineKeyboardButton(f"☀️ Light: {float(light_level):.2f} lx", callback_data=f'details_light_{channel_id}')
                    ],
                    [
                        InlineKeyboardButton(f"💧 Watertank: {watertank_level}%", callback_data=f'details_watertank_{channel_id}')],
                    [
                        InlineKeyboardButton(f"🌱 Soil Moisture: {float(soil_moisture):.2f}%", callback_data=f'details_soil_{channel_id}')
                    ],
                    [InlineKeyboardButton("⚙️ Edit Vase", callback_data=f'edit_vase_{device_id}')],
                    [InlineKeyboardButton("🔙 Go Back", callback_data='vase_list')]
                ]


            reply_markup = InlineKeyboardMarkup(keyboard)

            # Build a beautiful message with proper Markdown formatting
            message = f"**🌿 Details for Vase: {vase['vase_name']}**\n\n"
            if res['watered_times']:
                message += f"In the last 14 days your plant has been watered {res['watered_times']} time(s)\nThis is the equivalent of {res['watered_times']*25}ml"
            # Add alerts with emojis and warnings
            alert = res.get('temperature_alert')
            if alert:
                if alert == "low":
                    message += "⚠️ _Warning: The temperature is too low! Consider moving the plant to a warmer place._\n"
                elif alert == "high":
                    message += "⚠️ _Warning: The temperature is too high! Consider moving the plant to a cooler place._\n"

            alert = res.get('soil_moisture_alert')
            if alert:
                if alert == "low":
                    message += "💧 _Warning: The soil moisture is too low! Your plant might not be getting enough water._\n"
                elif alert == "high":
                    message += "💧 _Warning: The soil moisture is too high! Your plant might be getting too much water._\n"

            alert = res.get('light_level_alert')
            if alert:
                if alert == "low":
                    message += "☀️ _Warning: The light level is too low! Consider moving the plant to a brighter area._\n"
                elif alert == "high":
                    message += "☀️ _Warning: The light level is too high! Consider moving the plant to a darker place._\n"

            await update.callback_query.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
        else:
            logger.info(f"No vase configuration found for device {device_id}, prompting for configuration")
            keyboard = [
                [InlineKeyboardButton("✅ Yes", callback_data=f'configure_{device_id}'), 
                InlineKeyboardButton("❌ No", callback_data='vase_list')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.message.reply_text(
                "🌿 _It looks like this vase is not yet configured._\n\n"
                "**Would you like to set it up now?**", 
                parse_mode='Markdown', reply_markup=reply_markup
            )
    except Exception as e:
        logger.error("Exception on get_user_vase_list():" + str(e))

async def handle_message(update: Update, context: CallbackContext):
    logger.info(f"Message received: {update.message.text[:50]}...")
    if context.user_data["param_to_edit"] and context.user_data["global_device_id"]:
        param = context.user_data["param_to_edit"]
        device_id = context.user_data["global_device_id"]
        logger.info(f"Editing parameter '{param}' for device_id: {device_id}")
        if update.callback_query:
            message = update.callback_query.message
        else:
            message = update.message
        # get message from input
        new_value = update.message.text
        async with aiohttp.ClientSession() as session:
            res = await session.get(f"{resource_catalog_address}/vaseByDevice/{device_id}")
            vase = await res.json()        
            match(param):
                case 'vasename':
                    vase['vase_name'] = new_value
                    res = await session.put(f"{resource_catalog_address}/vase/{vase['vase_id']}", json=vase)
                    if res.status == 200:
                        await message.reply_text(text="Name updated successfully")
                case 'hourssun':
                    vase['plant']['hours_sun_min'] = new_value
                    vase['plant']['plant_schedule_light_level'] = new_value
                    res = await session.put(f"{resource_catalog_address}/vase/{vase['vase_id']}", json=vase)
                    if res.status == 200:
                        await message.reply_text(text="Hours of sun updated successfully")
                case 'minsoilmoisture':    
                    vase['plant']['soil_moisture_min'] = new_value
                    res = await session.put(f"{resource_catalog_address}/vase/{vase['vase_id']}", json=vase)
                    if res.status == 200:
                        await message.reply_text(text="Soil moisture updated successfully")                
                case 'maxsoilmoisture':
                    vase['plant']['soil_moisture_max'] = new_value
                    res = await session.put(f"{resource_catalog_address}/vase/{vase['vase_id']}", json=vase)
                    if res.status == 200:
                        await message.reply_text(text="Soil moisture updated successfully")
                case 'mintemperature':    
                    vase['plant']['temperature_min'] = new_value
                    res = await session.put(f"{resource_catalog_address}/vase/{vase['vase_id']}", json=vase)
                    if res.status == 200:
                        await message.reply_text(text="Temperature updated successfully")                
                case 'maxtemperature':
                    vase['plant']['temperature_max'] = new_value
                    res = await session.put(f"{resource_catalog_address}/vase/{vase['vase_id']}", json=vase)
                    if res.status == 200:
                        await message.reply_text(text="Temperature updated successfully")
        # clear user related param
        del context.user_data["param_to_edit"]
        logger.info(f"Parameter '{param}' updated successfully for device_id: {device_id}")

async def handle_photo(update: Update, context: CallbackContext):
    logger.info("Photo received from user")
    try:
        # Check if user is waiting for a disease identification image
        if context.user_data.get("waiting_for_disease_image"):
            logger.info("Processing photo for disease identification")
            # Download the photo
            photo_file = await update.message.photo[-1].get_file()
            file_path = f"{photo_file.file_id}.jpg"
            await photo_file.download_to_drive(file_path)
            
            # Store the file path in user data for later use
            context.user_data["uploaded_photo_path"] = file_path
            
            # Handle the disease identification
            await handle_plant_health_check(update, context)
            return
        
        # Original plant identification logic
        service_catalog = requests.get(f"{service_expose_endpoint}/all").json()
        recommendation_service = service_catalog['services']['recommendation_service']
        logger.info(f"Processing photo for plant identification using service: {recommendation_service}")

        if not context.user_data["global_device_id"]:
            logger.warning("Photo uploaded without selecting a vase first")
            await update.message.reply_text("Make sure to select a vase before trying to upload.")
            return
        
        # Download the photo
        photo_file = await update.message.photo[-1].get_file()
        file_path = f"{photo_file.file_id}.jpg"
        await photo_file.download_to_drive(file_path)

        await update.message.reply_text("Image received, let's see...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Open the image file asynchronously
                async with aiofiles.open(file_path, 'rb') as file:
                    form = aiohttp.FormData()
                    form.add_field('images', file, filename=file_path, content_type='image/jpeg')

                    # Send the request to the server
                    async with session.post(recommendation_service, data=form) as response:
                        if response.status == 200:
                            logger.info("Image successfully uploaded to recommendation service")
                            await update.message.reply_text('Image uploaded to server successfully!')

                            # Parse the response JSON
                            try:
                                chat_response =json.loads(await response.text())
                                logger.info("Successfully parsed recommendation service response")
                            except json.JSONDecodeError as json_err:
                                logger.error(f"Failed to parse recommendation service response: {str(json_err)}")
                                await update.message.reply_text('Failed to parse the server response.')
                                raise json_err
                            if isinstance(chat_response, list):
                                chat_response = chat_response[0]
                            # Ensure that chat_response is a valid dictionary
                            if chat_response and isinstance(chat_response, dict):
                                print("Creating vase")
                                logger.info("Creating new vase configuration from plant identification")
                                
                                # Check if required keys are present
                                required_keys = [
                                    'plant_name', 'soil_moisture_min', 'hours_sun_suggested', 
                                    'soil_moisture_max', 'temperature_min', 'temperature_max', 'description'
                                ]
                                missing_keys = [key for key in required_keys if key not in chat_response]
                                if missing_keys:
                                    print(f"Missing keys in response: {missing_keys}")
                                    logger.error(f"Missing keys in recommendation response: {missing_keys}")
                                    await update.message.reply_text(f'Missing data in response: {", ".join(missing_keys)}')
                                    return

                                # Construct the new vase dictionary
                                new_vase = {
                                    'device_id': context.user_data["global_device_id"],
                                    'vase_name': chat_response['plant_name'],  # Using the plant name from the response
                                    'user_id': context.user_data['current_user']['user_id'],
                                    'vase_status': 'active',
                                    'plant': {
                                        'plant_name': chat_response['plant_name'],
                                        'plant_type': chat_response.get('plant_type', 'indoor'),
                                        'plant_schedule_water': chat_response['soil_moisture_min'],
                                        'plant_schedule_light_level': chat_response['hours_sun_suggested'],  # Use hours of sunlight suggestion
                                        'soil_moisture_min': chat_response['soil_moisture_min'],
                                        'soil_moisture_max': chat_response['soil_moisture_max'],
                                        'hours_sun_min': chat_response['hours_sun_suggested'], # duplicated data
                                        'temperature_min': chat_response['temperature_min'],
                                        'temperature_max': chat_response['temperature_max'],
                                        'description': chat_response['description']
                                    }
                                }

                                # Send the new vase data to the resource catalog
                                async with session.post(f"{resource_catalog_address}/vase", json=new_vase) as res:
                                    print(f"res: {res} res.status: {res.status}")
                                    if res.status == 200:
                                        logger.info(f"Successfully created vase for plant: {chat_response['plant_name']}")
                                        await update.message.reply_text(
                                            f"🌱 *Vase Added Successfully!* 🌱\n\n"
                                            f"*Plant Name*: {chat_response['plant_name']}\n\n"
                                            f"*Plant Type*: {chat_response.get('plant_type', 'indoor')}\n\n"
                                            f"*Auto-detected Parameters:*\n"
                                            f"  - 🌡️ *Temperature Range*: {chat_response['temperature_min']}°C to {chat_response['temperature_max']}°C\n"
                                            f"  - 💧 *Soil Moisture*: {chat_response['soil_moisture_min']}% to {chat_response['soil_moisture_max']}%\n"
                                            f"  - ☀️ *Light Level*: {chat_response['hours_sun_suggested']} hours/day\n\n"
                                            f"💡 *Suggestions*: {chat_response['description']}\n\n"
                                            f"Thank you for adding a new plant to your vase! 🌿",
                                            parse_mode='Markdown'
                                        )

                                    else:
                                        logger.error(f"Failed to create vase. Status: {res.status}")
                                        await update.message.reply_text('Failed to add the vase.')

                                # Get telegram group for plant type using the telegramgroups microservice
                                plant_type = chat_response.get('plant_type', 'indoor')
                                async with session.get(f"{telegramgroups_address}/{plant_type}") as res:
                                    print(f"Telegram groups service response: {res.status}")
                                    if res.status == 200:
                                        group = await res.json()
                                        print(f"Found group: {group}")
                                        await update.message.reply_text(
                                            f"🌱 *Join the community!* 🌱\n\n"
                                            f"Don't take care of your *{chat_response['plant_name']}* alone! 🌿\n\n"
                                            f"Join the community of [{group['name']}]({group['link']})! 🌿\n\n",
                                            parse_mode='Markdown'
                                        )
                                    elif res.status == 404:
                                        logger.info(f"No telegram group found for plant type: {plant_type}")
                                        # Continue without error - not having a community group is not critical
                                    else:
                                        logger.error(f"Failed to get telegram group. Status: {res.status}")
                                        # Continue without error - this is not critical to vase creation                                       

                        else:
                            print(await response.text())
                            logger.error(f"Failed to upload image to recommendation service. Status: {response.status}")
                            await update.message.reply_text('Failed to upload the image.')

        except Exception as e:
            raise e
        finally:
            # Clean up the temporary file for plant identification
            if 'file_path' in locals() and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.error(f"Error cleaning up file {file_path}: {str(e)}")

    except Exception as e:
        logger.error(f"Exception on handle_photo(): {str(e)}") 

async def handle_disease_identification_request(update: Update, context: CallbackContext):
    """Handle the request to identify plant disease"""
    logger.info("Disease identification request initiated")
    try:
        # Set a flag in user data to indicate we're waiting for a disease identification image
        context.user_data["waiting_for_disease_image"] = True
        
        await update.callback_query.edit_message_text(
            "🏥 *Plant Disease Identification*\n\n"
            "Please upload a photo of your plant that you'd like me to check for diseases.\n\n"
            "I'll analyze the image and provide you with health assessment and treatment recommendations.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Exception on handle_disease_identification_request(): {str(e)}")
        await update.callback_query.edit_message_text("Sorry, there was an error. Please try again.")

async def handle_plant_health_check(update: Update, context: CallbackContext):
    """Handle plant health checking using the plant health service"""
    logger.info("Plant health check initiated")
    try:
        service_catalog = requests.get(f"{service_expose_endpoint}/all").json()
        plant_health_service = service_catalog['services']['plant_health']
        logger.info(f"Using plant health service: {plant_health_service}")
        
        file_path = context.user_data.get("uploaded_photo_path")
        if not file_path:
            logger.warning("No image found for plant health check")
            await update.message.reply_text("No image found. Please upload an image first.")
            return
        
        await update.message.reply_text("🏥 *Checking plant health...*", parse_mode='Markdown')
        
        try:
            async with aiohttp.ClientSession() as session:
                # Open the image file asynchronously
                async with aiofiles.open(file_path, 'rb') as file:
                    form = aiohttp.FormData()
                    form.add_field('images', file, filename=file_path, content_type='image/jpeg')

                    # Send the request to the plant health service
                    async with session.post(plant_health_service, data=form) as response:
                        if response.status == 200:
                            logger.info("Successfully received plant health assessment")
                            try:
                                health_response = json.loads(await response.text())
                                logger.info("Successfully parsed plant health response")
                            except json.JSONDecodeError as json_err:
                                logger.error(f"Failed to parse plant health response: {str(json_err)}")
                                await update.message.reply_text('Failed to parse the health assessment response.')
                                raise json_err
                            
                            # Format the health response
                            is_healthy = health_response.get('is_healthy', True)
                            suggestions = health_response.get('suggestions', [])
                            gemini_advice = health_response.get('gemini_advice', 'No specific advice available.')
                            
                            if is_healthy:
                                logger.info("Plant health assessment: Plant appears healthy")
                                message = (
                                    f"✅ *Plant Health Assessment* ✅\n\n"
                                    f"🎉 *Great news!* Your plant appears to be healthy.\n\n"
                                    f"💡 *General Care Tips:*\n{gemini_advice}"
                                )
                            else:
                                logger.info(f"Plant health assessment: Issues detected. Suggestions count: {len(suggestions)}")
                                message = (
                                    f"⚠️ *Plant Health Assessment* ⚠️\n\n"
                                    f"🔍 *Health Issues Detected:*\n"
                                )
                                
                                if suggestions:
                                    for i, suggestion in enumerate(suggestions, 1):
                                        name = suggestion.get('name', 'Unknown')
                                        probability = suggestion.get('probability', 0)
                                        message += f"  {i}. *{name}* (Probability: {probability:.1%})\n"
                                        logger.info(f"Health issue detected: {name} (Probability: {probability:.1%})")
                                
                                message += f"\n💡 *Treatment Recommendations:*\n{gemini_advice}"
                            
                            await update.message.reply_text(message, parse_mode='Markdown')
                        else:
                            logger.error(f"Failed to check plant health. Status: {response.status}")
                            await update.message.reply_text('Failed to check plant health. Please try again.')

        except Exception as e:
            await update.message.reply_text(f'Error during health check: {str(e)}')
            raise e

    except Exception as e:
        logger.error(f"Exception on handle_plant_health_check(): {str(e)}")
        await update.message.reply_text("Sorry, there was an error checking your plant's health. Please try again.")
    finally:
        # Clean up the temporary file and reset the flag
        file_path = context.user_data.get("uploaded_photo_path")
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                del context.user_data["uploaded_photo_path"]
            except Exception as e:
                logger.error(f"Error cleaning up file {file_path}: {str(e)}")
        
        # Reset the disease identification flag
        context.user_data["waiting_for_disease_image"] = False

def main(TOKEN):
    logger.info("Starting Telegram bot application")
    token = TOKEN

    application = Application.builder().token(token).concurrent_updates(True).build()
    logger.info("Application built successfully")

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("vase_list", get_user_vase_list))
    application.add_handler(CommandHandler("add_vase", add_vase))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))  
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    logger.info("All handlers registered successfully")
    application.run_polling() 

if __name__ == '__main__':
    try:
        logger.info("Loading environment variables")
        load_dotenv()

        TOKEN = os.getenv("TOKEN")
        if not TOKEN:
            logger.error("TOKEN is missing from environment variables")
            raise ValueError("TOKEN is missing from environment variables")
        logger.info("Environment variables loaded successfully")
        main(TOKEN)
    except Exception as e:
        print(e)
        logger.error(f"Critical error during startup: {str(e)}")
        print("ERROR OCCUREDD, DUMPING INFO...")
        path = os.path.abspath('./logs/ERROR_telegrambot.err')
        with open(path, 'a') as file:
            date = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
            file.write(f"Crashed at : {date}")
            file.write(f"Unexpected error: {e}")
        
        print("EXITING...")
        sys.exit(1) 