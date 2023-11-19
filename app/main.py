import asyncio
import math
import sqlite3
import time
from string import Template

import aiohttp

from bot import send_message

BASE_URL = Template(
    "https://api.technodom.kz/katalog/api/v1/products/category/${category}?city_id=5f5f1e3b4c8a49e692fefd70&limit=${limit}&page=${page}"
)
SOURCE = "TECHNODOM"

connection = sqlite3.connect("db.sql")
db_cursor = connection.cursor()


async def get_by_type(category: str, limit: int = 1, page: int = 1):
    url = BASE_URL.substitute(category=category, limit=limit, page=page)
    results = []
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response_json = await response.json()
            data = response_json.get("payload")
            for object in data:
                external_id = object.get("sku")
                price = int(object.get("price"))
                source = SOURCE
                uri = object.get("uri")
                title = object.get("title")
                row = db_cursor.execute(
                    "SELECT id FROM items WHERE external_id=? AND source=?",
                    (external_id, source),
                ).fetchone()
                if not row:
                    db_cursor.execute(
                        "INSERT INTO items (external_id, uri, source, title) VALUES (?, ?, ?, ?)",
                        (external_id, uri, source, title),
                    )
                    connection.commit()
                    row = db_cursor.execute(
                        "SELECT id FROM items WHERE external_id=? AND source=?",
                        (external_id, source),
                    ).fetchone()
                (item_id,) = row
                item_last_price_row = db_cursor.execute(
                    "SELECT price FROM prices WHERE item_id=? ORDER BY created_at DESC",
                    (int(item_id),),
                ).fetchone()
                if not item_last_price_row or int(item_last_price_row[0]) != int(price):
                    db_cursor.execute(
                        "INSERT INTO prices (item_id, price) VALUES (?, ?)",
                        (int(item_id), price),
                    )
                    connection.commit()
                    await session.close()
                    results.append(f"{title} - https://www.technodom.kz/p/{uri} - старая цена {price} - новая цена {item_last_price_row}")
    return "\n".join(results)


async def main():
    async with aiohttp.ClientSession() as session:
        categories = ["vstraivaemye-poverhnosti", "stiral-nye-mashiny", "vstraivaemye-duhovki"]
        for category in categories: 
            response = await session.get(BASE_URL.substitute(category=category, limit=5, page=1))
            response_json = await response.json()
            limit = response_json["limit"]
            total = response_json["total"]
            number_of_pages = math.ceil(total / limit)
            tasks = []
            for page in range(1, number_of_pages + 1):
                task = asyncio.create_task(get_by_type(category=category, limit=limit, page=page)) # coroutine
                tasks.append(task) # list[coroutine]
            results = await asyncio.gather(*tasks) # list[str]
            for result in results: # str in list[str]
                if not result: continue # coroutine == "" 
                try:
                    await send_message(result) # send
                except Exception as e:
                    print(e)
                time.sleep(10)
        


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
