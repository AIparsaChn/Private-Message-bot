import os
import asyncio

import telebot
from telebot.async_telebot import AsyncTeleBot, ExceptionHandler

import database

logger = telebot.async_telebot.logger
logger.setLevel("INFO")

class BotExceptionHandler(ExceptionHandler):
    async def handle(self, exception):
        logger.info(exception, exc_info=True)

TOKEN = os.environ.get("bot_token", None)
if not TOKEN:
    raise ValueError("The token doesn't exist.")

database.create_database_and_table()

bot = AsyncTeleBot(
    token=TOKEN,
    exception_handler=BotExceptionHandler()
)




if __name__ == "__main__":
    asyncio.run(bot.infinity_polling())


