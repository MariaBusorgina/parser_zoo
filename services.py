import asyncio

from bs4 import BeautifulSoup as bs

import aiofiles
from aiocsv import AsyncWriter
import random

from config import BASE_URL
from session import async_session

# список из списков ссылок по-странично
all_paginated_links = []

# Список с деталями о всех продуктах [[название, артикул, цена], [], [],..]
all_product_details = []


async def fetch_catalog_categories(url):
    """
    Получение списка категорий из раздела каталога на сайте.

    Args:
        url (str): Базовый URL сайта для получения каталога.
    Returns:
        list: Список категорий, содержащий названия и относительный URL подкатегорий.
    """
    url = url + 'catalogue/'
    catalog_cats = []  # название и урл категории
    response = await async_session(url=url)
    soup = bs(response, 'html.parser')
    category_sections = soup.find_all('div', class_='item_block col-md-6 col-sm-6')

    for category_section in category_sections:
        section_data = category_section.find_all('td', class_='section_info')
        name = section_data[0].find('a').text.strip()
        link = section_data[0].find('a').get('href')
        section_info = name, link
        catalog_cats.append(section_info)
    return catalog_cats


async def fetch_all_paginated_pages(category_url):
    """
    Функция для получения всех страниц с товарами в указанной категории.
        - Определяет количество страниц в категории через секцию пагинации.
        - Для каждой страницы создаёт задачу для асинхронного получения карточек товаров.
        - Собирает задачи и выполняет их параллельно с помощью asyncio.gather.

    Args:
        category_url (str): Относительный URL категории каталога, для которой необходимо получить все страницы.
    """
    full_url = BASE_URL[:-1] + category_url

    response = await async_session(url=full_url)
    soup = bs(response, 'html.parser')
    pagination_section = soup.find('div', class_='module-pagination')
    pagination_links = pagination_section.find_all('a', class_='dark_link')
    total_pages = int(pagination_links[-1].text)

    tasks = []

    # for page_number in range(1, total_pages + 1):
    for page_number in range(1, 2):  # для исключения блокировки
        task = asyncio.create_task(fetch_product_links(full_url, page_number))
        tasks.append(task)

    await asyncio.gather(*tasks)


async def fetch_product_links(url, page_number):
    """
    Извлекает ссылки на карточки товаров с указанной страницы каталога.

    Args:
        url (str): URL раздела каталога.
        page_number (int): Номер страницы пагинации для запроса.

    Returns:
        list: Список ссылок на товары с уникальными offer-id.
    """
    product_links = []
    paginated_url = url + f'?PAGEN_1={page_number}'

    await asyncio.sleep(2)
    response = await async_session(url=paginated_url)
    soup = bs(response, 'html.parser')

    product_container = soup.find('div', class_='bth-products-list-container')
    if product_container:
        product_cards = product_container.find_all('section', class_='bth-card-element')

        for product in product_cards:
            product_url = product.find('a', class_='bth-card-img-link').get('href')
            favorite_divs = product.find_all('div', class_='ixi_favorite')
            offer_ids = [offer_id.get('data-offer-id') for offer_id in favorite_divs]

            if offer_ids:
                for offer_id in offer_ids:
                    full_active_link = BASE_URL[:-1] + product_url + f"?oid={offer_id}"
                    product_links.append(full_active_link)
                all_paginated_links.append(product_links)

    return product_links


async def fetch_all_product_details(product_urls):
    """
    Создает и выполняет асинхронные задачи для извлечения информации о продуктах по предоставленным ссылкам.

    Параметры:
    cards (list): Список ссылок на карточки товаров.
    """
    tasks = []
    # for url in product_urls:
    for url in product_urls[:3]:  # для исключения блокировки
        task = asyncio.create_task(fetch_product_details(url))
        tasks.append(task)

    await asyncio.gather(*tasks)


async def fetch_product_details(product_url):
    """
    Извлекает информацию о товаре из карточки по предоставленной ссылке.

    Args:
        product_url (str): Ссылка на карточку товара.
    Returns:
        list: Список, содержащий название товара, его артикул (SKU) и цену.
    """
    try:
        product_details = []

        await asyncio.sleep(random.randint(2, 4))

        response = await async_session(url=product_url)
        soup = bs(response, 'html.parser')

        # НАЗВАНИЕ
        name = soup.find('h1').text.strip()
        product_details.append(name)

        # СКЮ
        articule_div = soup.find('div', attrs={'data-articule': True})
        if articule_div:
            product_code = articule_div['data-articule']
            product_details.append(product_code)

        # ЦЕНА
        price_meta = soup.find('meta', itemprop='price')
        if price_meta:
            price = price_meta.get('content')
            product_details.append(price)

        all_product_details.append(product_details)

        return product_details
    except Exception as e:
        print(f"Произошла ошибка: {e}")


def fetch_all_stored_product_details():
    """
    Возвращает список всех сохраненных данных о продуктах, которые были собраны
    с помощью асинхронных задач для каждой карточки товара.

    Returns:
        list: Список с деталями о всех продуктах (например, название, артикул, цена).
    """
    return all_product_details


def fetch_all_product_links():
    """
    Возвращает список всех собранных ссылок на карточки товаров.
    """
    return all_paginated_links


async def save_to_csv(data: list, filename: str = 'output.csv'):
    """
    Асинхронно сохраняет данные в CSV файл.

    Args:
        data (list): Список данных для записи в CSV файл.
        filename (str): Название CSV файла. По умолчанию 'output.csv'.
    """
    headers = ['Name', 'SKU', 'Price']

    async with aiofiles.open(filename, mode='w') as file:
        writer = AsyncWriter(file)
        await writer.writerow(headers)
        await writer.writerows(data)
