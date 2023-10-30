import asyncio
import logging
import sys
import sqlite3
from os import getenv

from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types.message import ContentType
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types.message import ContentType
from aiogram.utils.markdown import hbold
from constants import LINK_REPLY
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import aiohttp

# Bot token can be obtained via https://t.me/BotFather
TOKEN = getenv("BOT_TOKEN")

# All handlers should be attached to the Router (or Dispatcher)
bot = Bot(TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)

class Form(StatesGroup):
    link = State()

TEMPLATE_API = "https://api.technodom.kz/katalog/api/v1/products/"
CHAT_ID = None

connection = sqlite3.connect("db.sql")
db_cursor = connection.cursor()

@dp.message_handler(commands="start")
async def handle_start_command(message: Message) -> None:
    global CHAT_ID
    CHAT_ID = message.chat.id
    await message.answer(f"Hello, {hbold(message.from_user.full_name)}!")

@dp.message_handler(commands="link")
async def handle_link_command(message: Message) -> None:
    await Form.link.set()
    await message.answer(LINK_REPLY)

@dp.message_handler(state=Form.link, content_types=ContentType.TEXT)
async def handle_link(message: types.Message, state: FSMContext):
    await Form.next()
    parts = message.text.split("?")
    suburl = parts[0]
    subparts = suburl.split("-")
    sku = subparts[-1]
    url = TEMPLATE_API + sku
    print(url)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response_json = await response.json()
            link_id = response_json.get("sku")
            print(link_id)
            price = int(response_json.get("price"))
            print(price)
            title = response_json.get("title")
            source = "TECHNODOM"
            db_cursor.execute(
                    "INSERT INTO cart (chat_id, link_id, source, title, price) VALUES (?, ?, ?, ?, ?)",
                    (CHAT_ID, link_id, source, title, price),
                )
            first_price = db_cursor.execute(
                "SELECT price FROM cart WHERE chat_id=? AND link_id=? ORDER BY created_at ASC",
                (CHAT_ID, link_id),
            ).fetchone()
            print(first_price[0], price)
            connection.commit()
            await session.close()
            await message.answer(f"h{message.text} {first_price} {price}")
            return f"{message.text} {first_price} {price}"   
    db_cursor.close()
    connection.close()
    return ""



async def main() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(TOKEN)
    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())