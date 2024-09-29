import asyncio

from config import BASE_URL
from services import fetch_catalog_categories, fetch_all_product_details, fetch_all_stored_product_details, \
    fetch_all_product_links, fetch_all_paginated_pages, save_to_csv


def main():
    catalog_cats = asyncio.run(fetch_catalog_categories(BASE_URL))

    # for task in catalog_cats:
    for task in catalog_cats[:1]:  # для исключения блокировки берем 1
        asyncio.run(fetch_all_paginated_pages(task[1]))

    cards = fetch_all_product_links()

    # for card in cards:
    for card in cards[:1]:      # для исключения блокировки берем 1
        asyncio.run(fetch_all_product_details(card))

    final_product_info = fetch_all_stored_product_details()

    asyncio.run(save_to_csv(final_product_info))


if __name__ == '__main__':
    main()
