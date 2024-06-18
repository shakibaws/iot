from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import requests
import asyncio

resource_catalog_address = ''
service_expose_endpoint = 'http://0.0.0.0:8082'
users_list = []
current_user = None


def start(update: Update, context: CallbackContext) -> None:

    handle_endpoints()
    if not is_logged_in():
        login(update)

    # keyboard = [
    #     [InlineKeyboardButton(
    #         "Let's learn more about your plant!", callback_data='start')],
    #     [InlineKeyboardButton(
    #         "Add a vase", callback_data='add_vase')],
    # ]
    # reply_markup = InlineKeyboardMarkup(keyboard)
    # update.message.reply_text(
    #     "Welcome to the Smart Vase bot assitance, where you can indentify your plan, get suggestions and so much more!", reply_markup=reply_markup)
    update.message.reply_text(
        "Welcome to the Smart Vase bot assitance, where you can indentify your plan, get suggestions and so much more!",)


def is_logged_in():
    print(f'is user logged in: {current_user != None}')
    return current_user != None


def login(update: Update):
    global resource_catalog_address, users_list, current_user
    users_response = requests.get(f'{resource_catalog_address}/listUser')
    print(users_response.status_code)
    if users_response.status_code == 200:
        users_list = users_response.json()
        for user in users_list:
            if user['telegram_chat_id'] == update.message.chat_id:
                current_user = user
                print('User found and logged in')
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


def signup(update: Update):
    global current_user
    print('Signing up')
    signup_response = requests.post(
        f'{resource_catalog_address}/user',
        json={'telegram_chat_id': update.message.chat_id}
    )
    if signup_response.status_code == 200:
        print('User signed up')


def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    if query.data == 'start':
        query.edit_message_text(
            text="First, please send me an image of your plant so that I can identify it!")


def handle_photo(update: Update, context: CallbackContext) -> None:
    photo_file = update.message.photo[-1].get_file()
    file_path = f"{photo_file.file_id}.jpg"
    photo_file.download(file_path)
    update.message.reply_text(
        "Image recieved, let's see...")
    url = ""
    try:
        with open(file_path, 'rb') as file:
            files = {'file': (file_path, file, 'image/jpeg')}
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
    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(MessageHandler(Filters.photo, handle_photo))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
