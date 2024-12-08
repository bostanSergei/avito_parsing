from playwright.async_api import async_playwright
from loguru import logger

import threading
import datetime
import asyncio
import random
import os

from work_with_xlsx_file import get_start_data_from_excel_table, save_excel_table
from work_with_xlsx_file import get_analytic_data, save_analytic_part
from parsing_html import parsing_data, check_string
from browser_page import BasePage
# логин / пароль для входа на страницу с аналитикой (заполнить перед запуском)
from settings import LOGIN, PASSWORD, FILE

URL = 'https://www.avito.ru/'


logger.add('debug.log', format="{time} | {level} | {message}")


async def main():
    path_to_state_folder = f'state_files/' if os.name == 'posix' else f'state_files\\'
    start_date = datetime.datetime.today().strftime('%d_%m_%Y')

    logger.info('Парсер запущен')

    all_state_files = [file for file in os.listdir(path_to_state_folder) if file.endswith('.json')]
    if len(all_state_files) == 0:
        current_number = 0
        find_file_flag = False

        logger.info('State-файл не найден')
    else:
        state_dict = {}
        for file in all_state_files:
            file_id = file.split('_')[1].split('.')[0]
            state_dict[int(file_id)] = file

        current_number = max(state_dict.keys())
        find_file_flag = True

        logger.info('Найден state-файл. Будет выполнена попытка входа')

    # if f'state_{start_date}.json' in os.listdir(path_to_state_folder):
    #     new_context = False
    #     logger.info('Найден state-файл. Авторизация не требуется')
    # else:
    #     new_context = True
    #     logger.info('State-файл не найден')

    analytic_dict = {}
    d = {}

    # блок работы с первым браузером
    # def work_with_analytic_browser():
    #     async def wrapper():
    #         await asyncio.sleep(5)
    playwright = await async_playwright().start()

    browser = await playwright.chromium.launch(headless=False)
    logger.info('Запущен первый браузер')
    if not find_file_flag:
        context = await browser.new_context(
            viewport={'width': 1440, 'height': 1250}
        )
    else:
        context = await browser.new_context(
            viewport={'width': 1440, 'height': 1250},
            storage_state=f'{path_to_state_folder}state_{current_number}.json'
        )

    # context = await browser.new_context(
    #     viewport={'width': 1440, 'height': 1250}, storage_state=f'{path_to_state_folder}okna_30_11_2024.json'
    # )

    # страница с авторизацией
    auth_page = await context.new_page()
    response = await auth_page.goto(URL, wait_until='domcontentloaded')
    if response.status != 200:
        await auth_page.reload()

    await auth_page.wait_for_timeout(random.randint(5500, 10000))
    auth_object_page = BasePage(auth_page)
    enter_block = await auth_object_page.page.locator('div > a:visible', has_text='Вход и регистрация').all()

    if len(enter_block) > 0:
        await enter_block[0].click()
        await auth_object_page.page.wait_for_timeout(random.randint(3_500, 5_500))

        find_account = False

        button = await auth_object_page.page.locator('button:visible').all()
        for el in button:
            user = await el.get_attribute('class')
            if 'UserAccount-button-' in user:
                find_account = True
                await el.click()
                await auth_object_page.page.wait_for_timeout(2_500)

                for symbol in PASSWORD:
                    await auth_object_page.page.keyboard.press(symbol)
                    await auth_object_page.page.wait_for_timeout(350)

                await auth_object_page.page.locator('button > span:visible', has_text='Войти').click()
                await auth_page.wait_for_timeout(30_000)
                await auth_page.wait_for_timeout(30_000)
                break

        if not find_account:
            await auth_object_page.find_and_fill(placeholder='Телефон или почта', filler=LOGIN)
            await auth_object_page.find_and_fill(placeholder='Пароль', filler=PASSWORD)
            await auth_object_page.find_and_click(placeholder='Войти', locator='button > span', by_placeholder=False)

            await auth_page.wait_for_timeout(30_000)
            await auth_page.wait_for_timeout(30_000)

        logger.info('Сохраняем контекст')
        await context.storage_state(path=f'{path_to_state_folder}state_{current_number + 1}.json')

    logger.info('Переходим на страницу аналитики')
    await auth_page.goto('https://www.avito.ru/analytics/wordstat', wait_until='domcontentloaded')
    await auth_page.wait_for_timeout(random.randint(5500, 10000))

    analytic_table = get_analytic_data()

    # print(analytic_table)

    d['search_query'] = analytic_table['search_query']

    logger.info(f'Получено ключевых запросов: {len(analytic_table["search_query"])}')
    for i in range(len(analytic_table['search_query'])):
        if i == 0:
            placeholder = 'Введите слово или фразу'
        else:
            placeholder = 'Введите ещё одно слово или фразу'

        phrase = analytic_table['search_query'][i].strip()
        await auth_object_page.find_and_fill(placeholder=placeholder, filler=phrase)

        find_words = False
        search_elements = await auth_page.locator('div > button > div > div:visible').all()
        logger.info('Начинаем поиск по выпадающему списку')
        for elem in search_elements:
            if await elem.is_visible():
                if check_string(query_from_site=await elem.text_content(), query_from_table=phrase):
                    logger.info('Ключевая фраза найдена в списке')
                    await elem.click()
                    find_words = True
                    break
        await auth_page.wait_for_timeout(random.randint(3500, 5500))

        if not find_words:
            b = await auth_page.locator('button > span > span:visible', has_text='Смотреть аналитику').all()
            for el in b:
                await el.click()
                break

    logger.info(f"Начинаем заполнять поле с категорией {analytic_table['category']}")
    await auth_object_page.find_and_fill(placeholder='Категория', filler=analytic_table['category'])
    search_elements = await auth_page.locator('div > button > div > div').all()
    all_category = []
    for elem in search_elements:
        if await elem.is_visible():
            if check_string(query_from_site=await elem.text_content(), query_from_table=analytic_table['category']):
                all_category.append(elem)
                # await elem.click()
                # logger.info('Категория найдена')
                # break

    if len(all_category) == 1:
        await all_category[0].click()
    elif len(all_category) > 1 or len(all_category) == 0:
        await auth_page.wait_for_timeout(30_000)
        await auth_page.wait_for_timeout(30_000)
        await auth_page.wait_for_timeout(30_000)

    await auth_page.wait_for_timeout(random.randint(3500, 5500))

    logger.info('Выполнить переключение кнопки - 30 дней')
    await auth_object_page.find_and_click(
        placeholder='30 дней', locator='label > span > span > span', by_placeholder=False
    )

    logger.info('Начинаем сбор аналитики по городам')
    result = await auth_object_page.parsing_table(analytic_table)
    for key, value in result.items():
        analytic_dict[key] = value

    await auth_page.close()
    await browser.close()
            # await playwright.stop()

        # current_loop = asyncio.new_event_loop()
        # current_loop.run_until_complete(wrapper())

    # блок для работы с первым браузером
    data_from_table = get_start_data_from_excel_table(FILE)
    final_data: dict = {}

    # def work_with_find_browser() -> None:
    #     async def wrapper():
    #         playwright = await async_playwright().start()
    # под вторую страницу откроем новый браузер
    logger.info('Открываем второй браузер')
    s_browser = await playwright.chromium.launch(headless=False)
    s_context = await s_browser.new_context(viewport={'width': 1440, 'height': 1250})

    page = await s_context.new_page()
    response = await page.goto(URL, wait_until='domcontentloaded')
    if response.status != 200:
        await page.reload()

    await page.wait_for_timeout(random.randint(5500, 7500))

    # Согласие с городом по умолчанию (нужный город будет выбран после перехода к категории)
    elements = await page.locator('div > div > div > button > span', has_text='Да').all()
    if len(elements) > 0:
        logger.info('Выбор города по умолчанию')
        await elements[0].click()

    await page.wait_for_timeout(random.randint(2500, 5500))

    base_page = BasePage(page)

    await base_page.go_to_last_category(data_from_table['categories'])
    await page.wait_for_timeout(random.randint(2500, 5500))

    await base_page.fill_search_query(data_from_table['search_query'])
    await page.wait_for_timeout(random.randint(2500, 5500))

    flag = True
    logger.info(f'Всего найдено городов: {len(data_from_table["cities"])}')
    logger.info('Переходим к поиску по каждому из них')
    for row, city in data_from_table['cities'].items():
        logger.info(f'Начинаем поиск по городу {city}')
        sample_set = {el.lower().strip() for el in city.split(', ')}

        for i in range(3):
            if flag:
                await base_page.open_modal_with_cities()
                await page.wait_for_timeout(random.randint(2500, 5500))

            inputs_tag = await page.get_by_placeholder('Город или регион').all()

            for tag in inputs_tag:
                if await tag.is_visible():
                    logger.info(f'Заполняем поле ввода для города {city}')
                    await tag.fill(city)

            await page.wait_for_timeout(random.randint(2500, 2500))

            flag = await base_page.get_all_cities_and_press_button(sample_set)

            if flag:
                await page.wait_for_timeout(random.randint(3500, 5500))
                final_data[row] = parsing_data(await page.content())
                break
            else:
                logger.info(f"Перезагружем страницу для повтороного поиска. Номер запроса: {i + 1}")
                await page.reload(wait_until='domcontentloaded')
                flag = True
                await page.wait_for_timeout(random.randint(7500, 15000))
                final_data[row] = None

        logger.info(f'По городу {city} получены данные: {final_data[row]}')

    logger.info(f'Первая часть данных получена и сохранена')
    logger.info(f'Второй браузер закрыт')
    await page.close()
    await s_browser.close()
    await playwright.stop()

        # current_loop = asyncio.new_event_loop()
        # current_loop.run_until_complete(wrapper())

    # threads = [
    #     threading.Thread(target=work_with_analytic_browser),
    #     threading.Thread(target=work_with_find_browser),
    # ]
    #
    # for thread in threads:
    #     thread.start()
    #
    # for thread in threads:
    #     thread.join()

    curr_date = save_excel_table(final_data, data_from_table['company_name'])
    save_analytic_part(analytic_dict, d['search_query'], curr_date)

    logger.info('Страница закрыта. Браузер закрыт. Парсер закончил свою работу!')


if __name__ == '__main__':
    asyncio.run(main())
