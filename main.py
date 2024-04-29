from playwright.async_api import async_playwright

import asyncio
import random

from work_with_xlsx_file import get_start_data_from_excel_table, save_excel_table
from work_with_xlsx_file import get_analytic_data, save_analytic_part
from parsing_html import parsing_data, check_string
from browser_page import BasePage
# логин / пароль для входа на страницу с аналитикой (заполнить перед запуском)
from PATH import LOGIN, PASSWORD

URL = 'https://www.avito.ru/'
# FILE - имя таблицы, из которой будет собраны стартовые данные (в папке start_table)
# таблица заполняется в соответствии предварительными договоренностями
FILE = 'sample.xlsx'


async def main():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(viewport={'width': 1440, 'height': 1250})

    # страница с авторизацией
    auth_page = await context.new_page()
    await auth_page.goto(URL, wait_until='domcontentloaded')

    await auth_page.wait_for_timeout(random.randint(1500, 5500))

    auth_object_page = BasePage(auth_page)
    await auth_object_page.find_and_click(placeholder='Вход и регистрация', locator='div > div > a', by_placeholder=False)
    await auth_object_page.find_and_fill(placeholder='Телефон или почта', filler=LOGIN)
    await auth_object_page.find_and_fill(placeholder='Пароль', filler=PASSWORD)
    await auth_object_page.find_and_click(placeholder='Войти', locator='button > span', by_placeholder=False)

    await auth_page.wait_for_timeout(25_000)
    await auth_page.goto('https://www.avito.ru/analytics/wordstat', wait_until='domcontentloaded')

    # под вторую страницу откроем новый браузер
    s_browser = await playwright.chromium.launch(headless=False)
    s_context = await s_browser.new_context(viewport={'width': 1440, 'height': 1250})

    page = await s_context.new_page()
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
            final_data[row] = ['Город отсутствует в поиске'] * 2

    curr_date = save_excel_table(final_data)
    await page.close()
    await s_browser.close()

    analytic_table = get_analytic_data(curr_date)
    for i in range(len(analytic_table['search_query'])):
        if i == 0:
            placeholder = 'Введите слово или фразу'
        else:
            placeholder = 'Введите ещё одно слово или фразу'

        phrase = analytic_table['search_query'][i]
        await auth_object_page.find_and_fill(placeholder=placeholder, filler=phrase)

        search_elements = await auth_page.locator('div > button > div > div').all()
        for elem in search_elements:
            if await elem.is_visible():
                if check_string(query_from_site=await elem.text_content(), query_from_table=phrase):
                    await elem.click()
                    break
        await auth_page.wait_for_timeout(random.randint(3500, 5500))

    await auth_object_page.find_and_fill(placeholder='Категория', filler=analytic_table['category'])
    search_elements = await auth_page.locator('div > button > div > div').all()
    for elem in search_elements:
        if await elem.is_visible():
            if check_string(query_from_site=await elem.text_content(), query_from_table=analytic_table['category']):
                await elem.click()
                break
    await auth_page.wait_for_timeout(random.randint(3500, 5500))

    analytic_dict = await auth_object_page.parsing_table(analytic_table)
    save_analytic_part(analytic_dict, analytic_table['search_query'], curr_date)

    await auth_page.close()
    await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
