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
from telebot.asyncio_filters import StateFilter, TextStartsFilter, AdvancedCustomFilter
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
        error_logger.error(exception, exc_info=True)

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

class CallbackTextStartsFilter(AdvancedCustomFilter):
    """Check if the callback data starts with a specific prefix."""
    key: str = "data_startswith"

    async def check(self, callback: CallbackQuery, text: str):
        return callback.data.startswith(text)

bot.add_custom_filter(StateFilter(bot))
bot.add_custom_filter(TextStartsFilter())
bot.add_custom_filter(CallbackTextStartsFilter())

bot.setup_middleware(StateMiddleware(bot))


@bot.message_handler(func=lambda mg: mg.text == "Cancel")
async def cancel_operation(message: Message, state: StateContext):
    """Cancel the user's state."""

    await state.delete()
    await bot.send_message(
        chat_id=message.chat.id,
        text=messages.CANCELED_OPERATION,
        reply_markup=keyboards.remove_keyboard()
    )
    return None


@bot.message_handler(commands=["private_message"], chat_types=["private"])
async def start_private_message_process(message: Message, state: StateContext):
    """Initiate the private message process by requesting target group selection.

    This command handler starts the PrivateMessageStates workflow in private chat.
    It requests the user to choose a group as shared_chat via a keyboard button.

    Raises:
        Exception: Logs any exceptions that occur during message sending or state transition.
    """
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
    """Process a shared chat selection and validate bot membership.

    This handler recieves the group chat shared by the user via a chat_shared content type.
    It verifies that the user is a member of the target group before proceeding with the private message workflow.

    Raises:
        Exception: Logs any exceptions that occur during processing but does not
        propagate them to maintain user experience.

    Workflow:
        1. Validates bot membership in the target group using rd.check_chat_id()
        2. If not a member, informs the user and terminates the process
        3. If valid, stores target group data (ID, title, username) in state
        4. Prompts user to select recipient users with a custom keyboard
        5. Maintains the shared_user state for the next step
    """
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
    """Process a shared user selection and validate group membership.

    This handler receives user information shared via the users_shared content type.
    It verifies that the selected user is member of the previously chosen target
        group before proceeding to request the private message content.

    Raises:
        Exception: Logs any exceptions that occur during processing but does not
        propagate them to maintain user experience.

    Workflow:
        1. Retrieves target group ID from conversation state
        2. Extracts user ID from the shared users list
        3. Validates user membership in the target group using get_chat_member()
        4. If user is not a member, informs the user and terminates the process
        5. If valid, stores target user data (ID, first name) and sender info in state
        6. Prompts user to enter the private message content with a cancel option
        7. Transitions state to PrivateMessageStates.private_message for message input
    """
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
    """Recieve and validate the private message content from the user.

    This handler captures the main message text that will be sent to the target user
        via an inline button in the public group. When the target user clicks the inline
        button, this message will be displayed to them as an answer to a callback query.

    Raises:
        Exception: Logs any exceptions that occur during processing but does not
        propagate them to maintain user experience.

    Workflow:
        1. Validates message length and warns if exceeded (non-blocking)
        2. Stores the private message text in PrivateMessageStates state
        3. Prompts user to provide an optional description with cancel option
            if the user doesn't want to provide any description
        4. Transitions state to PrivateMessageStates.description for description input
    """
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
async def recieve_description(message: Message, state: StateContext):
    """Receive and process the optional description for the private message.

    This handler captures the description text that provides concise decription
    for the main private message.
    It handles special commands and validates length before
    presenting a summary for user confirmation.

    Raises:
        Exception: Logs any exceptions but does not propagate them to maintain UX

    Special Commands:
        - /no_description: Skips description (sets to None or "Nothing")

    Validation:
        - Checks if message length exceeds LIMIT_DESCRIPTION_CHARS
        - If exceeded, sends warning message and blocks progression
        - Unlike private message validation, this is a blocking validation

    Workflow:
        1. Processes special command /no_description to skip description
        2. Validates description length (blocking if exceeded)
        3. Stores description in conversation state
        4. Retrieves all collected data (target user, message, description, group)
        5. Presents affirmation message with complete summary
        6. Provides affirmation keyboard for user confirmation/cancellation
        7. Transitions to PrivateMessageStates.affirmation for final decision
    """
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
    """Handler user affirmation decision for sending the private message.

    This callback handler processes the user's final confirmation (yes/no) to send
    the composed private message. It either executes the full message delivery
    workflow or cancels the operation based on the user's choice.

    Raises:
        Exception: Logs any exceptions but does not propagate them to maintain UX

    Workflow for 'yes' affirmation:
        1. Retrieves all stored data (target user, group, message, description, metadata)
        2. Sends group notification message with inline keyboard for the target user
        3. Stores message metadata in Redis for later callback handling
        4. Implements rate limiting delay to prevent HTTP 429 errors
        5. Sends confirmation to sender with link to the group message
        6. Clears conversation state

    Workflow for 'no' affirmation:
        1. Sends cancellation confirmation to user
        2. Clears conversation state without any message delivery
    """
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
    """Global fallback handler for unexpected messages in private chats.

    This handler catches any message that doesn't match other specific handlers
    throughout all states ('*'). It serves as a safety net to guide users back
    to the proper workflow when they send unexpected input.

    Note:
        This handler should have lower priority than specific state handlers
        to ensure it only catches truly unexpected messages.

    Raises:
        Exception: Logs any exceptions that occur during message sending or state transition.
    """
    try:
        await bot.send_message(
            chat_id=message.chat.id,
            text=messages.WARNING_FOLLOW_STRUCTURE,
            reply_markup=keyboards.create_cancel_keyboard()
        )
    except Exception as ex:
        error_logger.error(ex, exc_info=True)

    return None


@bot.callback_query_handler(data_startswith="private_message:")
async def display_private_message(callback: CallbackQuery):
    try:
        group_chat_id = callback.message.chat.id
        target_user_id = callback.data.split(":")[-1]
        user_id = str(callback.from_user.id)
        message_id = callback.message.id

        if target_user_id == user_id:
            private_message = await rd.get_private_message(
                target_user_id=user_id,
                target_group_chat_id=group_chat_id,
                private_message_id=message_id
            )
            await bot.answer_callback_query(
                callback_query_id=callback.id,
                text=private_message,
                show_alert=True
            )
        else:
            await bot.answer_callback_query(
                callback_query_id=callback.id,
                text=messages.NOT_ALLOWED_MESSAGE,
                show_alert=True
            )
    except Exception as ex:
        error_logger.error(ex, exc_info=True)


@bot.my_chat_member_handler()
async def recieve_group_info(message: Message):
    """Handle my_chat_member updates and store neccessary infomration about a group.

    Whenever some add the bot to a special group, this handler catches
        myChatMember updates and store neccessary infomration available in a message.

    Purpose:
        - Provide some basic information like username, chat_id, title and etc for PrivateMessageStates workflow

    Raises:
        Exception: Logs any exceptions that occur during message sending or state transition.
    """
    try:
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

    except Exception as ex:
        error_logger.error(ex, exc_info=True)

    return None


if __name__ == "__main__":
    asyncio.run(bot.infinity_polling())


