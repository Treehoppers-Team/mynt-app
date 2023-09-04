import logging
import json
import pyqrcode
import requests
import datetime
import io
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, PhotoSize, InputFile
)
from telegram.ext import (
    ContextTypes, ConversationHandler, CallbackContext,
)
import os
from dotenv import load_dotenv

from bot_utils import (send_default_event_message,
                       update_default_event_message)

ROUTE, NEW_USER, NEW_USER_NAME, SHOW_QR = range(4)

load_dotenv()
endpoint_url = os.getenv("BACKEND_ENDPOINT", "http://localhost:3000")
PROVIDER_TOKEN = os.getenv("PROVIDER_TOKEN")

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def get_user_id_from_query(update):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    return user_id

""""
=============================================================================================
redeem: Displays events that the user has successfully registered for and are yet to be redeemed. 
    After user picks an event, show_QR will be called that will display a QR code containing information 
    on the user's id, event status and event title
check_authorisation (merchant): should be in the merchant side. we get the telegram id, 
    use getRegistrations Firebase to see what the user has registered for, compare to the current event 
    and send a message back to the user and authoriser saying {handle} has been verified for XX event
=============================================================================================
"""

def get_successful_registrations(response_data):
    registered_events = {}
    reply_string = ''
    count = 1

    for events in response_data:
        eventTitle = events['eventTitle']
        status = events['status']
        user_id = events['userId']
        try:  
          verification = events['verification']
        except Exception:
          verification = "UNVERIFIED"
          print("verification has not been set, check server.js and helper.js")
        if status =="SUCCESSFUL" and verification == "VERIFIED": 
            registered_events[eventTitle] = {
                'userId': user_id, 'status': status, 'eventTitle': eventTitle}
            reply_string += f'\n {count}. {eventTitle}'
            count += 1
            
    return registered_events, reply_string
    
    
async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loading_message = "Checking your tickets..."
    message = await context.bot.send_message(chat_id=update.effective_chat.id, text=loading_message)
    user_id = await get_user_id_from_query(update)
    logger.info(f"Retrieving registrations for User: {user_id}")
    response = requests.get(endpoint_url + f"/getRegistrations/{user_id}")
    response_data = response.json()

    await message.delete()
    if len(response_data) <= 0:
        await update_default_event_message(update, context, f"You have no registered events")
        return ROUTE

    else:
        query = update.callback_query
        registered_events, reply_string = get_successful_registrations(response_data)
        if len(registered_events) == 0: # if raffle was not successful - he did not get the ticket
            await update_default_event_message(update, context, f"You have no successful registrations")
            return ROUTE
        else:
            reply_string += '\n\n Which one would you like to redeem?'
            context.user_data['registered_events'] = registered_events
            keyboard = [[InlineKeyboardButton("< Back to Menu", callback_data="event_options"),]]
            for event in registered_events:
                keyboard.append([InlineKeyboardButton(event, callback_data=f'show_QR_{event}')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="You have available tickets! Which would you like to redeem?",
                reply_markup=reply_markup
            )
            return ROUTE


async def show_QR(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ticket = update.callback_query.data[8:] ## (show_qr_xx) The title starts from 8th index
    user_id = await get_user_id_from_query(update)
    user_chat_id = update.effective_chat.id
    registered_events = context.user_data['registered_events']
    registered_events[ticket]['chatId'] = user_chat_id
    qr_information = registered_events[ticket]
    qr_information_str = json.dumps(qr_information)

    # await context.bot.send_message(
    #     chat_id= user_chat_id,
    #     text = f'Show this QR code to redeem your ticket for {ticket}'
    # )

    original_message = context.user_data['original_message'] # initialized during the start function
    await original_message.delete()

    url = pyqrcode.create(qr_information_str)
    url.png(f'./qr_codes/{user_id}.png', scale=6)
    with open(f'./qr_codes/{user_id}.png', 'rb') as f:
        bio = io.BytesIO(f.read())

    bio.seek(0)
    QR = await context.bot.send_photo(chat_id=user_chat_id, photo=InputFile(bio, filename='qr_code.png'),caption=f'Show this QR code to redeem your ticket for {ticket}')

    context.user_data['QR'] = QR

    # add code to delete photo as well
    # current_path = os.getcwd()
    # if platform != 'darwin':  # windows
    #     picture_path = current_path + f'\qr_codes\{user_id}.png'
    # else:  # mac or linux
    #     picture_path = current_path + f'/qr_codes/{user_id}.png'
    # # print(f'Your current path is {picture_path}')
    # os.remove(picture_path)
    await send_default_event_message(
        update, 
        context, 
        "Head back to the menu if your verification was successful"
    )
    return ROUTE

""""
=============================================================================================
view_events: View ongoing events
check_registration: View status for users' registrations
get_previous_registrations: API call to retrive previous registrations
validate_registration: Validate event title and check previous registrations
process_registration: Check whether user has sufficient balance in in-app wallet
complete_purchase: Send API request to save payment records
complete_registration: Send API request to save registration records
check_balance: Check the users balance against the event price (deprecated)
=============================================================================================
"""

def get_current_capacity(event_title):
    registrations = requests.get(endpoint_url + "/getEventRegistrations/" + event_title)
    registration_data = registrations.json()
    num_registered_users = len(registration_data)
    num_verification_rejected = 0

    for registration in registration_data:
        if registration['verification'] == 'REJECTED':
            num_verification_rejected += 1

    num_available = num_registered_users - num_verification_rejected
    return num_available

def format_event_data(response_data, context: ContextTypes.DEFAULT_TYPE):
    
    event_array = [] # Contains message, button and photo to be sent for each event
    events_dict = {} # Contains mapping of event titles and price, to be used in validate_registration
    
    for event in response_data:
        try:
            event_title = event['title']
            event_description = event['description']
            event_time = event['time']
            event_venue = event['venue']
            event_price = event['price']
            event_type = event['eventType']
            event_capacity = event['capacity']
            keyboard = []

            if event_type == 'fcfs':
                current_capacity = get_current_capacity(event_title)

                text = f"Event Title: *{event_title}*\n" \
                        f"Description: {event_description}\n\n" \
                        f"Event Type: *First-come-first-serve*\n" \
                        f"Capacity: {current_capacity}/{event_capacity}\n\n" \
                        f"Time: {event_time}\n" \
                        f"Venue: {event_venue}\n" \
                        f"Price: *{event_price}*\n\n"
                        
                if current_capacity >= int(event_capacity):
                    text += "*This event has reached maximum capacity.*"
                else:
                    keyboard = [[InlineKeyboardButton(text='Register for Event', callback_data=f'title_{event_title}_{event_type}')],]
                    reply_markup = InlineKeyboardMarkup(keyboard)


            elif event_type =='raffle':
                text = f"Event Title: *{event_title}*\n" \
                        f"Description: {event_description}\n\n" \
                        f"Event Type: *Raffle*\n" \
                        f"Capacity: {event_capacity}\n\n" \
                        f"Time: {event_time}\n" \
                        f"Venue: {event_venue}\n" \
                        f"Price: *{event_price}*\n\n"
                keyboard = [[InlineKeyboardButton(text='Register for Event', callback_data=f'title_{event_title}_{event_type}')],]
                reply_markup = InlineKeyboardMarkup(keyboard)
                        
            
            photo_url = f"https://firebasestorage.googleapis.com/v0/b/treehoppers-mynt.appspot.com/o/{event_title}{event_time}?alt=media&token=07ddd564-df85-49a5-836a-c63f0a4045d6"
            photo = PhotoSize(
                file_id=photo_url,
                file_unique_id="some_random_id",
                width=400,
                height=400
            )
            if len(keyboard) > 0:
                event_array.append((text, reply_markup, photo))
            else:
                event_array.append((text, photo))
            
            events_dict[event_title] = event_price
        
        except Exception as e:
            print(f'an exception occured in getting events; format_event_data: {e} is missing')
            print(f"This exception occured for {event['title']}")
        
    context.user_data["events_dict"] = events_dict
    return event_array


async def view_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Retrieving Events Information")

    # Send loading message to user
    loading_message = "Loading events..."
    message = await context.bot.send_message(chat_id=update.effective_chat.id, text=loading_message)

    query = update.callback_query
    await query.answer()
    
    response = requests.get(endpoint_url + "/viewEvents")
    response_data = response.json()
    event_array = format_event_data(response_data, context)
    await message.delete()

    events_messages = [] # To store the event messages tags later on

    if len(event_array) == 0:
        await update_default_event_message(update, context, "There are currently no ongoing events to register for")
    
    else:
        for event_info in event_array:
            
            ## No keyboard rendered (for fully registered events)
            if(len(event_info) == 2):
                text, photo = event_info
                try:
                    event_message = await context.bot.send_photo(
                        chat_id=update.effective_chat.id, 
                        photo=photo,
                        caption=text, 
                        parse_mode="markdown", 
                    )
                    events_messages.append(event_message)

                except Exception as e:
                    logger.error(f"Error sending photo for event: {e}")
                    fallback_url ="https://ipfs.io/ipfs/QmfDTSqRjx1pgD1Jk6kfSyvGu1PhPc5GEx837ojK8wfGNi"
                    photo = PhotoSize(
                        file_id=fallback_url,
                        file_unique_id="some_random_id",
                        width=400,
                        height=400
                    )
                    event_message = await context.bot.send_photo(
                        chat_id=update.effective_chat.id, 
                        photo=photo,
                        caption=text, 
                        parse_mode="markdown", 
                    )
                    events_messages.append(event_message)
                
            elif (len(event_info) == 3):
                text, reply_markup, photo = event_info
                try:
                    event_message = await context.bot.send_photo(
                        chat_id=update.effective_chat.id, 
                        photo=photo,
                        caption=text, 
                        parse_mode="markdown", 
                        reply_markup=reply_markup
                    )
                    events_messages.append(event_message)

                except Exception as e:
                    logger.error(f"Error sending photo for event: {e}")
                    fallback_url ="https://ipfs.io/ipfs/QmfDTSqRjx1pgD1Jk6kfSyvGu1PhPc5GEx837ojK8wfGNi"
                    photo = PhotoSize(
                        file_id=fallback_url,
                        file_unique_id="some_random_id",
                        width=400,
                        height=400
                    )
                    event_message = await context.bot.send_photo(
                        chat_id=update.effective_chat.id, 
                        photo=photo,
                        caption=text, 
                        parse_mode="markdown", 
                        reply_markup=reply_markup
                    )
                    events_messages.append(event_message)
                    
        text = "Please click on the register button for the event you would like to register for."
        await send_default_event_message(update, context, text)

    context.user_data['events_messages'] = events_messages
        
    return ROUTE


def format_registration_data(response_data):
    text = ""
    if response_data: # User has previously registered for events
        text += "These are your current registered events!\n\n"
        for event in response_data:
            event_title = event['eventTitle']
            status = event['status']
            text += f"Event Title: *{event_title}*\n" \
                f"Registration Status: {status}\n\n" \

    else: # User has no previous registrations
        text += "You have not registered for any events!"
    return text
   
    
async def check_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loading_message = "Checking your registrations..."
    message = await context.bot.send_message(chat_id=update.effective_chat.id, text=loading_message)
    user_id = await get_user_id_from_query(update)
    logger.info(f'Checking status for {user_id}')
    response = requests.get(endpoint_url + f"/getRegistrations/{user_id}")
    response_data = response.json()
    text=format_registration_data(response_data)
    await message.delete()
    await update_default_event_message(update, context, text)
    return ROUTE
    

def get_previous_registrations(user_id, event_title):
    logger.info(f'Checking previous registrations for {user_id}')
    response = requests.get(endpoint_url + f"/getRegistrations/{user_id}")
    response_data = response.json()

    # Save event titles for events that user has previously registered for
    registered_events = []
    if response_data:
        for event in response_data:
            registered_events.append(event['eventTitle'])

    # Check if user is registering for the same event
    if event_title in registered_events:
        return True
        
    return False


def check_balance(user_id, event_price): # deprecated
    logger.info(f"Verifying balance for user {user_id}")
    response = requests.get(endpoint_url + f"/viewWalletBalance/{user_id}")
    response_data = response.json()
    user_balance = response_data['balance']
    if user_balance < event_price:
        return True
    else:
        return False


async def validate_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    try:
        if context.user_data['events_messages'] != None: # if I want to delete the events message that is being triggered by view_events in bot_utils
            event_messages = context.user_data['events_messages']

            for message in event_messages:
                await message.delete() # deleting each message

            context.user_data['events_messages'] = None # doing this in case there are errors later if the 'events_messages' is not found (already deleted)

    except Exception:
        print("event messages has not been set")

    logger.info("Validating registration for user")
    query = update.callback_query
    await query.answer()   
    
    callback_data = update.callback_query.data ## (title_xx) The title starts from 5th index
    data_parts = callback_data.split('_')
    event_title = data_parts[1]
    event_type = data_parts[2]

    context.user_data["event_title"] = event_title
    context.user_data["event_type"] = event_type

    events_dict = context.user_data["events_dict"]
    event_price = events_dict[event_title]
    context.user_data["event_price"] = event_price
    user_id = await get_user_id_from_query(update)
    
    user_id = query.from_user.id
    double_registration = get_previous_registrations(user_id, event_title)
    # invalid_balance = check_balance(user_id, event_price)

    if double_registration:
        text=("You have already registered for this event. \n"
            "You cannot register for the same event again.")
        await send_default_event_message(update, context, text)

    # elif invalid_balance: (not needed anymore)
    #     text=("You have insufficient funds. \n"
    #         "Please top up your wallet in the Wallet menu.")
    #     await send_default_event_message(update, context, text)
    
    else:
        # Prompt user for payment confirmation

        # code below deletes the old bot message that is stored in the context
        original_message = context.user_data['original_message'] # initialized during the start function
        await original_message.delete()

        keyboard = [
            [InlineKeyboardButton("< Back", callback_data="event_options")],
            [InlineKeyboardButton("Yes", callback_data="process_registration"),]
        ]
        if event_price == 0:
            original_message = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f'Do you wish to confirm your registration for the event: {event_title}?\n'
                "Reply with Yes to confirm",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="markdown",
            )
            context.user_data['original_message'] = original_message
        else:
            original_message = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f'Do you wish to make a payment of ${event_price} for the event using Paynow?\n'
                "Reply with Yes to confirm payment",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="markdown",
            )
            context.user_data['original_message'] = original_message
        
    return ROUTE


async def process_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    context.user_data["user_id"] = user_id
    await complete_purchase(update, context) # await complete_registration(update, context) - called within complete purchase
    return ROUTE


async def complete_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    event_price = context.user_data["event_price"]

    original_message = context.user_data['original_message'] 
    await original_message.delete()
    
    if event_price > 0:
        keyboard = [[InlineKeyboardButton("< Back to Menu", callback_data="event_options"),],[InlineKeyboardButton("Payment Completed", callback_data="complete_registration"),]]

        reply_markup = InlineKeyboardMarkup(keyboard)

        with open(f'./paynow/paynow_liam.jpg', 'rb') as f:
            bio = io.BytesIO(f.read())

        bio.seek(0)
        context.user_data["registration_confirmation"] = await context.bot.send_photo(
            chat_id=update.effective_chat.id, 
            photo=InputFile(
                bio, 
                filename='paynow_liam.jpg'
            ),
            caption = (f"Please make a payment of ${event_price} via PayNow to the QR code attached.\n\n"
                        "Alternatively, you can make a transfer to the following UEN: 12345678. \n\n"
                        "Once the payment has been made, click on 'Payment Completed'"),
            reply_markup = reply_markup)
        
    else:
        await complete_registration(update, context)
    

async def complete_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data["user_id"]
    event_title = context.user_data["event_title"]
    event_price = context.user_data["event_price"]
    event_type = context.user_data['event_type']
    registration_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f'{user_id} has successfully registered for {event_title} at {registration_time}')

    registration_confirmation = context.user_data["registration_confirmation"] # delete registration confirmation message
    await registration_confirmation.delete()

    if event_type == 'fcfs':
        status = 'SUCCESSFUL'
        verification = "UNVERIFIED"
        data = {
            'user_id': user_id,
            'amount': event_price,
            'transaction_type': "SALE",
            'timestamp': registration_time,
            'event_title': event_title,
        }
        response = requests.post(endpoint_url + "/ticketSale", json=data)
        logger.info("Saving payment records")
    else:  
        status = 'PENDING'
        verification = "VERIFIED"
    
    data = {
        'user_id': user_id,
        'event_title': event_title,
        'status': status,
        'verification': verification,
        'registration_time': registration_time,
    }
    response = requests.post(endpoint_url + "/insertRegistration", json=data)
    if response.status_code == 200:
        if event_type == 'raffle':
            text=(f"You have successfully registered for {event_title}. \n"
            "Please note that your registration does not guarantee a ticket, as we will be "
            "conducting a raffle to randomly select the winners. \n\n"
            "We will notify you of the outcome via a telegram message. \n\n"
            "Thank you for your interest and we hope to see you at the event!")
        else:
            text=(f"You have successfully registered for {event_title}. \n"
            "Please note that your registration does not guarantee a ticket. \n\n"
            "Once your payment has been verified, you will receive a ticket and be notified via a telegram message \n\n"
            "Thank you for your interest and we hope to see you at the event!")
        await send_default_event_message(update, context, text)
        return ROUTE
    else:
        await update.message.reply_text("Sorry, something went wrong with your registration")
        return ConversationHandler.END


""""
=============================================================================================
view_transaction_history: Display transaction history of user 
=============================================================================================
"""

def format_txn_history(response_data,user_balance=0):
    if len(response_data) > 0:
        text = f"Your transaction History is as follows\n" \
               f"Your amount you have paid in total is ${user_balance}\n\n"

        for transaction in response_data:
            transaction_type = transaction['transactionType']
            amount = transaction['amount']
            time = transaction['timestamp']
            event = transaction['eventTitle'] if 'eventTitle' in transaction else "-"

            text += f"Transaction Type: *{transaction_type}*\n" \
                f"Amount: ${amount}\n" \
                f"Time: {time}\n" \
                f"Event: {event}\n\n"
    else:
        text = "You have no prior transactions"
    return text
    
async def view_transaction_history(update: Update, context: CallbackContext):
    loading_message = "Retrieving transaction history..."
    message = await context.bot.send_message(chat_id=update.effective_chat.id, text=loading_message)
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    response_data = []

    response_data_registration = requests.get(endpoint_url + f"/getRegistrations/{user_id}")
    response_registration= response_data_registration.json()
    response_data_transaction = requests.get(endpoint_url + f"/viewTransactionHistory/{user_id}")
    response_transaction = response_data_transaction.json()

    user_balance = 0

    for event in response_registration[::-1]: # we want to push the latest registration to the top
      event_title = event['eventTitle']
      status = event['status']
      try:  
        verification = event['verification']
      except Exception:
        verification = "UNVERIFIED"

      if (status == "SUCCESSFUL" or status == "REDEEMED") and verification == 'VERIFIED':
          for transaction in response_transaction[::-1]: # in the event of duplicate transactions, we want only the latest one, so we reverse the list to push the latest transaction to the top
              event = transaction['eventTitle'] if 'eventTitle' in transaction else "-"
              if event_title == event:
                  amount = transaction['amount']
                  user_balance += amount
                  response_data.append(transaction)
                  break # break the for loop because we locate the most recent transaction for that event in the case of duplicate tr
              
    # # push the latest transaction to the top
    # response_data.reverse()

    # Get the current page number from user_data, default to page 1
    page_num = int(query.data.split("_")[-1])
    context.user_data['page_num'] = page_num

    # Calculate the starting and ending index of transactions to display
    num_per_page = 3
    start_idx = (page_num - 1) * num_per_page
    end_idx = start_idx + num_per_page

    # Slice the transactions to display only the ones for the current page
    transactions = response_data[start_idx:end_idx]

    # Format the transactions as text
    text = format_txn_history(transactions,user_balance)
    await message.delete()

    # Create the inline keyboard for pagination
    keyboard = [[InlineKeyboardButton("< Back to Menu", callback_data="event_options"),],]
    if start_idx > 0:
        # Add "Previous" button if not on the first page
        keyboard.append([InlineKeyboardButton("Previous", callback_data=f"view_transaction_history_{page_num-1}")])
    if end_idx < len(response_data):
        # Add "Next" button if not on the last page
        keyboard.append([InlineKeyboardButton("Next", callback_data=f"view_transaction_history_{page_num+1}")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the message with pagination and update user_data with the current page number
    await query.edit_message_text(text=text, reply_markup=reply_markup)

    return ROUTE