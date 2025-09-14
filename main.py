import os
import json
import asyncio
import logging
from datetime import datetime

import telebot
from telebot.formatting import munderline, mcite
from telebot.async_telebot import AsyncTeleBot, ExceptionHandler
from telebot.types import Message, ChatFullInfo, User, CallbackQuery
from telebot.states import State, StatesGroup
from telebot.states.asyncio.context import StateContext
from telebot.asyncio_storage import StateRedisStorage
from telebot.asyncio_filters import StateFilter
from telebot.states.asyncio.middleware import StateMiddleware

import sql_database
import keyboards
import messages
from redis_database import RedisDatabase as rd

logger = telebot.async_telebot.logger
logger.setLevel("INFO")

#error_logger just handles ERROR and CRITICAL 
error_logger = logging.getLogger(__name__)
error_logger.setLevel(logging.ERROR)
stream_handler = logging.StreamHandler()
file_handler = logging.FileHandler('error.log', encoding='utf-8')
file_handler.setLevel(logging.ERROR)
stream_handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)
error_logger.addHandler(stream_handler)
error_logger.addHandler(file_handler)

# Constants
# Number of characters for private messsage.
# It sends as an answerCallbackQuery which is limited to 200 characters.
LIMIT_PRIVATE_MESSAGE_CHARS = 200
LIMIT_DESCRIPTION_CHARS = 1000 # Limit of the description which is sent to a public group or supergroup.

class BotExceptionHandler(ExceptionHandler):
    async def handle(self, exception):
        error_logger.info(exception, exc_info=True)

TOKEN = os.environ.get("bot_token", None)
if not TOKEN:
    raise ValueError("The token doesn't exist.")

bot = AsyncTeleBot(
    token=TOKEN,
    exception_handler=BotExceptionHandler(),
    state_storage=StateRedisStorage()
)

class PrivateMessageStates(StatesGroup):
    shared_user = State()
    shared_chat = State()
    description = State()
    private_message = State()
    affirmation = State()

bot.add_custom_filter(StateFilter(bot))
bot.setup_middleware(StateMiddleware(bot))


@bot.message_handler(func=lambda mg: mg.text == "Cancel")
async def cancel_operation(message: Message, state: StateContext):
    await state.delete()
    await bot.send_message(
        chat_id=message.chat.id,
        text=messages.CANCELED_OPERATION,
        reply_markup=keyboards.remove_keyboard()
    )
    return None

@bot.message_handler(commands=["private_message"], chat_types=["private"])
async def start_private_message_process(message: Message, state: StateContext):
    try:
        await bot.send_message(
            chat_id=message.chat.id,
            text=messages.REQUEST_GROUP_MESSAGE,
            reply_markup=keyboards.create_request_chat_keyboard()
        )
        await state.set(PrivateMessageStates.shared_user)

    except Exception as ex:
        error_logger.error(ex, exc_info=True)

    return None


@bot.message_handler(
    content_types=["chat_shared"], chat_types=["private"],
    state=PrivateMessageStates.shared_user)
async def recieve_target_chat(message: Message, state: StateContext):
    try:
        if not await rd.check_chat_id(message.chat_shared.chat_id):
            await bot.send_message(
                chat_id=message.chat.id,
                text=messages.BOT_NOT_JOINED_MESSAGE
            )
            return None

        await state.add_data(
            target_group_chat_id=message.chat_shared.chat_id,
            target_group_title=sql_database.get_group_title(message.chat_shared.chat_id),
            target_group_username = sql_database.get_group_username(message.chat_shared.chat_id)
        )

        await bot.send_message(
            chat_id=message.chat.id,
            text=messages.REQUEST_USER_MESSAGE,
            reply_markup=keyboards.create_request_users_keyboard()
        )
        await state.set(PrivateMessageStates.shared_user)

    except Exception as ex:
        error_logger.error(ex, exc_info=True)

    return None


@bot.message_handler(
    content_types=["users_shared"], chat_types=["private"],
    state=PrivateMessageStates.shared_user)
async def recieve_target_user(message: Message, state: StateContext):
    try:
        async with state.data() as data:
            group_chat_id = data.get("target_group_chat_id")
            user_id = message.users_shared.users[-1].user_id
        try:
            target_user_info = await bot.get_chat_member(group_chat_id, user_id)
        except:
            await bot.send_message(
                chat_id=message.chat.id,
                text=messages.USER_NOT_JOINED_MESSAGE
            )
            return None

        await state.add_data(
            target_user_id=target_user_info.user.id,
            target_first_name=target_user_info.user.first_name,
            sender_first_name=message.from_user.first_name
        )
        await bot.send_message(
            chat_id=message.chat.id,
            text=messages.REQUEST_PRIVATE_MESSAGE,
            reply_markup=keyboards.create_cancel_keyboard(),
            parse_mode="markdown"

        )
        await state.set(PrivateMessageStates.private_message)

    except Exception as ex:
        error_logger.error(ex, exc_info=True)

    return None


@bot.message_handler(content_types=['text'], chat_types=["private"],
        state=PrivateMessageStates.private_message)
async def recieve_private_message(message: Message, state: StateContext):
    try:
        if len(message.text) > LIMIT_PRIVATE_MESSAGE_CHARS:
            await bot.send_message(
                chat_id=message.chat.id,
                text=messages.WARNING_LIMIT_PRIVATE_MESSAGE.format(
                    LIMIT_PRIVATE_MESSAGE_CHARS,
                    len(message.text)
                ),
                parse_mode="markdown"
            )

        await state.add_data(private_message=message.text)
        await bot.send_message(
            chat_id=message.chat.id,
            text=messages.REQUEST_DESCRIPTION_MESSAGE,
            parse_mode="html",
            reply_markup=keyboards.create_cancel_keyboard()
        )

        await state.set(PrivateMessageStates.description)

    except Exception as ex:
        error_logger.error(ex, exc_info=True)

    return None


@bot.message_handler(content_types=["text"], chat_types=["private"],
        state=PrivateMessageStates.description)
async def recieve_private_message(message: Message, state: StateContext):
    try:
        if message.text == "/no_description":
            description = None
        if len(message.text) > LIMIT_DESCRIPTION_CHARS:
            await bot.send_message(
                chat_id=message.chat.id,
                text=messages.WARNING_LIMIT_DESCRIPTION_MESSAGE.format(
                    LIMIT_DESCRIPTION_CHARS,
                    len(message.text)
                )
            )
            return None
        elif message.text == "/no_description":
            description = "Nothing"
        else:
            description = message.text

        await state.add_data(description=description)

        async with state.data() as data:
            target_first_name = data.get("target_first_name")
            description = data.get("description")
            private_message = data.get("private_message")
            target_group_title = data.get("target_group_title")


        await bot.send_message(
            chat_id=message.chat.id,
            text=messages.AFFIRMATION_MESSAGE.format(
                target_first_name,
                target_group_title,
                description,
                private_message
            ),
            reply_markup=keyboards.create_affirmation_keyboard(),
            parse_mode="markdown"
        )
        await state.set(PrivateMessageStates.affirmation)

    except Exception as ex:
        error_logger.error(ex, exc_info=True)

    return None


@bot.callback_query_handler(state=PrivateMessageStates.affirmation)
async def verify_private_message(call: CallbackQuery, state: StateContext):
    try:
        affirmation = call.data.split(":")[-1]
        if affirmation == "yes":
            async with state.data() as data:
                target_user_id = data.get("target_user_id")
                target_group_chat_id = data.get("target_group_chat_id")
                private_message = data.get("private_message")
                description = data.get("description")
                target_first_name = data.get("target_first_name")
                target_group_title = data.get("target_group_title")
                sender_first_name = data.get("sender_first_name")
                target_group_username = data.get("target_group_username")

            # Sends the message to the group that the user selected.
            sent_message_info = await bot.send_message(
                    chat_id=target_group_chat_id,
                    text=messages.GROUP_NOTIFICATION_MESSAGE.format(
                        target_first_name, sender_first_name, description
                    ),
                reply_markup=keyboards.create_private_message_keyboard(
                    user_id=target_user_id
                )
            )

            await rd.store_private_message(
                target_user_id=target_user_id,
                target_group_chat_id=target_group_chat_id,
                private_message_id=sent_message_info.id,
                private_message_text=private_message
            )

            await asyncio.sleep(2) #Prevent too many reqeusts error (429 Http code)

            # Sends the message to the user's private chat.
            await bot.send_message(
                chat_id=call.message.chat.id,
                text=messages.SENT_TO_GROUP,
                reply_markup=keyboards.create_linked_message_keyboard(
                    group_username=target_group_username,
                    message_id=sent_message_info.id
                )
            )


        elif affirmation == "no":
            await bot.send_message(
                chat_id=call.message.chat.id,
                text=messages.CANCELED_OPERATION
            )

        await state.delete()

    except Exception as ex:
        error_logger.error(ex, exc_info=True)

    return None


@bot.message_handler(state="*", chat_types=["private"])
async def warn_user(message: Message):
    await bot.send_message(
        chat_id=message.chat.id,
        text=messages.WARNING_FOLLOW_STRUCTURE,
        reply_markup=keyboards.create_cancel_keyboard()
    )
    return None


@bot.my_chat_member_handler()
async def recieve_group_info(message: Message):
    group_info: ChatFullInfo = await bot.get_chat(message.chat.id)

    #Add info to sqlite database
    sql_database.store_group_info(
        chat_id=group_info.id,
        username=group_info.username,
        chat_type=group_info.type,
        title=group_info.title,
        description=group_info.description,
        is_forum=group_info.is_forum,
        bio=group_info.bio,
        date_membership=str(datetime.now()),
        json_photos=json.dumps(group_info.photo.__dict__) if group_info.photo is not None else None
    )

    #Store chat_id in single set redis key
    await rd.add_chat_id(group_info.id)

    logger.info("A new group was added to database.")


if __name__ == "__main__":
    asyncio.run(bot.infinity_polling())


