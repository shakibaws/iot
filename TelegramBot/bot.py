from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import requests
import time

resource_catalog_address = ''
service_expose_endpoint = 'http://serviceservice.duck.pictures'
users_list = []
vase_list = []
device_list = []
current_user = None
current_context = None
welcome_message = None
no_vase_found_message = None


def start(update: Update, context: CallbackContext) -> None:
    global current_context, welcome_message, users_list, vase_list, current_user
    welcome_message = update.message.reply_text(
        "Welcome to the Smart Vase bot assitance, where you can indentify your plan, get suggestions and so much more!",)
    users_list = []
    vase_list = []
    device_list = []
    current_user = None
    current_context = context
    handle_endpoints()
    if not is_logged_in(update):
        login(update)
    else:
        handle_main_actions(update)


def is_logged_in(update: Update):
    isLoggedIn = current_user != None and current_user['telegram_chat_id'] == update.message.chat_id

    print(
        f'is user logged in: {isLoggedIn} loggin_user={current_user} \n chat_id={update.message.chat_id}')
    return isLoggedIn


def login(update: Update):
    global resource_catalog_address, users_list, current_user
    users_response = requests.get(f'{resource_catalog_address}/listUser')
    print(users_response.status_code)
    if users_response.status_code == 200:
        users_list = users_response.json()
        for user in users_list:
            if user['telegram_chat_id'] == update.message.chat_id:
                current_user = user
                print(f'User found and logged in. User = {current_user}')
                handle_main_actions(update)
                break
        if current_user == None:
            print('User not found')
            signup(update)


def handle_endpoints():
    global resource_catalog_address, service_expose_endpoint
    resource_endpoint_response = requests.get(f'{service_expose_endpoint}/all')
    if resource_endpoint_response.status_code == 200:
        resource_catalog_address = resource_endpoint_response.json(
        )['services']['resource_catalog_address']


def remove_message(update: Update, message, is_query: bool = False):
    global current_context
    current_context.bot.delete_message(
        chat_id=update.callback_query.message.chat_id if is_query else update.message.chat_id, message_id=message.message_id)


def signup(update: Update):
    global current_user, welcome_message
    time.sleep(1)
    remove_message(update, welcome_message)
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
        remove_message(update, signup_message)
        signup_confirm_message = update.message.reply_text(
            "Done 🎉, now let's get started!"
        )
        time.sleep(1)
        login(update)
        remove_message(update, signup_confirm_message)


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


def add_vase():
    global resource_catalog_address, current_user


def get_user_vase_list(update: Update, context: CallbackContext):
    global resource_catalog_address, vase_list, current_user, no_vase_found_message
    if no_vase_found_message != None:
        remove_message(update, no_vase_found_message, True)
        no_vase_found_message = None
    vase_list_response = requests.get(f'{resource_catalog_address}/listVase')
    device_list_response = requests.get(f'{resource_catalog_address}/listDevice')

    addingVaseInstructions = f" If you already have got a smart vase, please follow these steps to activate it:\n\n1. Please turn on the vase and WIFI on your phone.\n\n2. You should see a WIFI network called 'SmartVase', please connect to it and then click on **[here](http://192.168.4.1/?user_id={current_user['user_id']})** \n\n3. Once you have completed the steps, please connect to the internet, and check your new list of Smart Vases ⬇️"
    print('Getting list vase')
    keyboard_list = []
    if vase_list_response.status_code == 200:
        global_vase_list = vase_list_response.json()
        for vase in global_vase_list:
            if vase['user_id'] == current_user['user_id']:
                vase_list.append(vase)
                print(f"{vase_list}")
                
    if device_list_response.status_code == 200:
        global_device_list = device_list_response.json()
        for device in global_device_list:
            if device['user_id'] == current_user['user_id']:
                device_list.append(device)
                print(f"{device_list}")

        if device_list:
            print('User has some devices')
            for dev in device_list:
                name = "Vase "+dev['device_id']
                for v in vase_list:
                    if v["device_id"] == dev["device_id"]:
                        name = v["vase_name"]
                        break
                keyboard_list.append([InlineKeyboardButton(name, callback_data='vase_info')])
                
            if update.callback_query:
                message = update.callback_query.message
            else:
                message = update.message
            
            keyboard = keyboard_list
            reply_markup = InlineKeyboardMarkup(keyboard)
            no_vase_found_message = message.reply_text(
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
                f"You have no smart vases connected! {addingVaseInstructions}", parse_mode='Markdown', reply_markup=reply_markup)


def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    if query.data == 'start':
        query.edit_message_text(
            text="First, please send me an image of your plant so that I can identify it!")
    if query.data == 'vase_list':
        get_user_vase_list(update, context)


def handle_photo(update: Update, context: CallbackContext) -> None:
    photo_file = update.message.photo[-1].get_file()
    file_path = f"{photo_file.file_id}.jpg"
    photo_file.download(file_path)
    update.message.reply_text(
        "Image recieved, let's see...")
    url = "http://recommendationservice.duck.pictures"
    try:
        with open(file_path, 'rb') as file:
            files = {'images': (file_path, file, 'image/jpeg')}
            response = requests.post(url, files=files)

        if response.status_code == 200:
            update.message.reply_text(
                'Image uploaded to server successfully!')
        else:
            update.message.reply_text(
                'Failed to upload the image.')
    except Exception as e:
        update.message.reply_text('Somthing went wrong...')


def main() -> None:
    updater = Updater("7058374905:AAFJc4qnJjW5TdDyTViyjW_R6PzcSqR22CE")
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("vase_list", get_user_vase_list))
    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(MessageHandler(Filters.photo, handle_photo))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
