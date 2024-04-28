from playwright.async_api import async_playwright

import asyncio
import random

from work_with_xlsx_file import get_start_data_from_excel_table, save_excel_table
from parsing_html import parsing_data
from browser_page import BasePage


URL = 'https://www.avito.ru/'
# FILE - имя таблицы, из которой будет собраны стартовые данные (в папке start_table)
# таблица заполняется в соответствии предварительными договоренностями
FILE = 'sample.xlsx'
# логин / пароль для входа на страницу с аналитикой (заполнить перед запуском)
LOGIN = ''
PASSWORD = ''


async def main():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(viewport={'width': 1440, 'height': 1250})

    page = await context.new_page()
    await page.goto(URL, wait_until='domcontentloaded')

    await page.wait_for_timeout(random.randint(1500, 5500))

    # Согласие с городом по умолчанию (нужный город будет выбран после перехода к категории)
    elements = await page.locator('div > div > div > button > span', has_text='Да').all()
    if len(elements) > 0:
        await elements[0].click()

    await page.wait_for_timeout(random.randint(1500, 5500))

    data_from_table = get_start_data_from_excel_table(FILE)

    base_page = BasePage(page)

    await base_page.go_to_last_category(data_from_table['categories'])
    await page.wait_for_timeout(random.randint(1500, 5500))

    await base_page.fill_search_query(data_from_table['search_query'])
    await page.wait_for_timeout(random.randint(1500, 5500))

    final_data: dict = {}

    flag = True
    for row, city in data_from_table['cities'].items():
        sample_set = {el.lower().strip() for el in city.split(', ')}
        if flag:
            await base_page.open_modal_with_cities()
            await page.wait_for_timeout(random.randint(2500, 5500))

        inputs_tag = await page.get_by_placeholder('Город или регион').all()

        for tag in inputs_tag:
            if await tag.is_visible():
                await tag.fill(city)

        await page.wait_for_timeout(random.randint(1500, 2500))

        flag = await base_page.get_all_cities_and_press_button(sample_set)
        if flag:
            await page.wait_for_timeout(random.randint(3500, 5500))
            final_data[row] = parsing_data(await page.content())
        else:
            final_data[row] = 'Город отсутствует в поиске', 'Город отсутствует в поиске'

    save_excel_table(final_data)


if __name__ == '__main__':
    asyncio.run(main())
