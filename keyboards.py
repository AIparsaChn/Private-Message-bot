from telebot.types import (ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
        KeyboardButtonRequestUsers, KeyboardButtonRequestChat,
        InlineKeyboardButton, InlineKeyboardMarkup)


def create_request_chat_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        row_width=1
    ).add(
        KeyboardButton(
            text="Choose the group you want to send your private message.",
            request_chat=KeyboardButtonRequestChat(
                request_id=1,
                chat_is_channel=False,
                chat_is_forum=False
            )
        ),
        KeyboardButton(
            text="Cancel",
        )
    )


def create_request_users_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        row_width=1
    ).add(
        KeyboardButton(
            text="Choose the user you want him or her to recieve your private message.",
            request_users=KeyboardButtonRequestUsers(
                request_id=2,
                user_is_bot=False
            )
        ),
        KeyboardButton(
            text="Cancel",
        )
    )


def create_affirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton(
            text="Yes!",
            callback_data="affirmation:yes"
        ),
        InlineKeyboardButton(
            text="No",
            callback_data="affirmation:no"
        )
    )


def create_private_message_keyboard(user_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton(
            text="Show the message.",
            callback_data=f"private_message:{user_id}"
        )
    )


def create_linked_message_keyboard(group_username: str, message_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton(
            text="Show the sent message.",
            url=f"https://t.me/{group_username}/{message_id}"
        )
    )


def create_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(resize_keyboard=True).add(
        KeyboardButton(
            text="Cancel"
        )
    )


def remove_keyboard():
    return ReplyKeyboardRemove()
