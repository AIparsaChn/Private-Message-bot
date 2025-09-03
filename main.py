import os
import json
import asyncio
import pprint
from datetime import datetime

import telebot
from telebot.async_telebot import AsyncTeleBot, ExceptionHandler
from telebot.types import Message, ChatFullInfo

import sql_database
from redis_database import RedisDatabase as rd

logger = telebot.async_telebot.logger
logger.setLevel("INFO")

class BotExceptionHandler(ExceptionHandler):
    async def handle(self, exception):
        logger.info(exception, exc_info=True)

TOKEN = os.environ.get("bot_token", None)
if not TOKEN:
    raise ValueError("The token doesn't exist.")

sql_database.create_database_and_table()

bot = AsyncTeleBot(
    token=TOKEN,
    exception_handler=BotExceptionHandler()
)


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


