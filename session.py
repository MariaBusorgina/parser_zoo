import asyncio

import aiohttp
import random

from config import HEADERS


async def async_session(url: str, headers: dict = HEADERS):
    """
    Асинхронная функция для получения содержимого страницы по указанному URL.

    Args:
        url (str): URL страницы, с которой необходимо получить данные.
        headers (dict): Заголовки для запроса (по умолчанию - HEADERS).
    """
    async with aiohttp.ClientSession() as session:
        try:
            delay = random.uniform(1, 3)
            await asyncio.sleep(delay)

            response = await session.get(url, headers=headers)

            if response.status == 200:
                return await response.text()
            else:
                print(f"Запрос не удался с кодом {response.status}. Повтор через 5 секунд.")
                await asyncio.sleep(5)

        except aiohttp.ClientError as e:
            print(f"Произошла ошибка при запросе: {e}")
            await asyncio.sleep(5)
