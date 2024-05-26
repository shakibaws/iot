from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import requests


def start(update: Update, context: CallbackContext) -> None:
    keyboard = [[InlineKeyboardButton(
        "Let's learn more about your plant!", callback_data='start')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "Welcome to the Smart Vase bot assitance, where you can indentify your plan, get suggestions and so much more!", reply_markup=reply_markup)


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
