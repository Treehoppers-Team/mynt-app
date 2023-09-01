import logging
import requests
from telegram import (
    Update,InlineKeyboardButton,InlineKeyboardMarkup, 
)
from telegram.ext import (
    ContextTypes, ConversationHandler,
)
import re
import os
from dotenv import load_dotenv

from bot_utils import send_default_message, update_default_start_message

ROUTE, NEW_USER, NEW_USER_NAME, SHOW_QR = range(4)

load_dotenv()
endpoint_url = os.getenv("BACKEND_ENDPOINT", "http://localhost:3000")

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def new_user_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Create Profile", callback_data="create_profile"),],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = ("👋 Hello and welcome to Mynt Connect! 🎉\n\n"
               "Our goal is to help the Mynt community connect through various events.\n\n"
               "You can explore, engage, and even purchase tickets for events using this platform.\n\n"
               "Click 'Create Profile' to get started! \n\n")
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            text=message, 
            parse_mode="markdown", 
            reply_markup=reply_markup
        )
    else:
        original_message = await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text=message, 
            parse_mode="markdown", 
            reply_markup=reply_markup
        )
        context.user_data['original_message'] = original_message
        
async def existing_user_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Mynt Now!", callback_data="event_options"),]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = ("👋 Hello and welcome to Mynt Connect! 🎉\n\n"
                "Our goal is to help the Mynt community connect through various events.\n\n"
                "You can explore, engage, and even purchase tickets for events using this platform.\n\n"
               "To get started, you can either register for free events or top up your wallet.\n\n"
               "Once you have sufficient balance in your Mynt wallet, you can purchase a ticket for an event by selecting Register for an Event.\n\n"
               "You can access other *wallet* & *event* functionalities by clicking on the respective buttons below.")

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            text=message, 
            parse_mode="markdown", 
            reply_markup=reply_markup
        )
    else:
        original_message = await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text=message, 
            parse_mode="markdown", 
            reply_markup=reply_markup
        )
        context.user_data['original_message'] = original_message


""""
=============================================================================================
create_profile: Prompt new user for their name
get_new_user_name: Input validation for name & prompt for number
register_new_user: Input validation for number and send API request to save record if successful
send_message_new_profile: if the user successfully creates wallet returns this message
=============================================================================================
"""

async def create_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text=("To facilitate the creation of your profile, "
          "kindly provide your *full* name in the specified format: \n\n"
          "'John Walker'.\n\n"
          "Please ensure that there is a *space* between the *first* and *last* names."
          )
    await update_default_start_message(update, context, text)
    return NEW_USER_NAME

async def get_new_user_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.message.text
    name_parts = user_name.split()

    # code below deletes users message to the bot
    message = update.message

    if message.text == "/start": # if the user presses start then bring them back to the front page
        chat_id = message.chat_id
        message_id = message.message_id
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)

        original_message = context.user_data['original_message'] # initialized during the start function
        if original_message != None:
          await original_message.delete()

        text = ("If you would like to go back to the main menu please press the button below")

        await send_default_message(update, context, text)

        return NEW_USER

    if message != None:
        chat_id = message.chat_id
        message_id = message.message_id
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    
    if len(name_parts) != 2:
        # code below deletes the old bot message that is stored in the context
        original_message = context.user_data['original_message'] # initialized during the start function
        await original_message.delete()

        error_text = ("You have provided an invalid name format.\n\n" 
                      "Please provide your full name with a space between the first and last names.")
        await send_default_message(update, context, error_text)
        return NEW_USER_NAME
    
    else:
        # code below deletes the old bot message that is stored in the context
        original_message = context.user_data['original_message'] # initialized during the start function
        if original_message != None:
          await original_message.delete()

        context.user_data['new_user_name'] = user_name
        text = (f"Thank you for providing your name {user_name}. \n\n"
                "Kindly provide your contact number, consisting of 8 digits,"
                "in the specified format: '81818181'.")
        await send_default_message(update, context, text)
        return NEW_USER

def is_valid_singapore_number(number):
    pattern = r"^(?:\+65|65)?[689]\d{7}$"
    return re.match(pattern, number) is not None

async def register_new_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact_number = update.message.text
    message = update.message

    if message.text == "/start": # if the user presses start then bring them back to the front page
        chat_id = message.chat_id
        message_id = message.message_id
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)

        original_message = context.user_data['original_message'] # initialized during the start function
        if original_message != None:
          await original_message.delete()

        text = ("If you would like to go back to the main menu please press the button below")

        await send_default_message(update, context, text)

        return NEW_USER

    # code below deletes users message to the bot
    message = update.message
    if message != None:
        chat_id = message.chat_id
        message_id = message.message_id
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)

    # code below deletes the old bot message that is stored in the context
    original_message = context.user_data['original_message'] # initialized during the start function
    await original_message.delete()
    
    if not is_valid_singapore_number(contact_number):
        error_text = ("You have provided an invalid number.\n" 
                      "Please provide a valid Singapore number with 8 digits.")
        await send_default_message(update, context, error_text)
        return NEW_USER
    
    else:
        context.user_data['new_contact_number'] = contact_number
        user_id = update.message.from_user.id
        user_handle = update.message.from_user.username
        user_name = context.user_data["new_user_name"]
        user_contact = context.user_data["new_contact_number"]
        data = {
            'user_id': user_id,
            'user_handle': user_handle,
            'user_name': user_name,
            'user_contact': user_contact,
            'chat_id' : update.effective_chat.id
        }
        logger.info(f'Saving records of new user {user_id}')

        response = requests.post(endpoint_url + "/uploadUserInfo", json=data)
        if response.status_code == 200:
            await send_message_new_profile(update, context)
            return ROUTE

        else:
            await update.message.reply_text('An unexpected error occurred')
            return ConversationHandler.END
    
async def send_message_new_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("< Back to Menu", callback_data="start"),],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        text="You have successfully created your profile!\n\n"
              "Head back to the menu to view and register for ongoing events!",
        reply_markup=reply_markup
    )