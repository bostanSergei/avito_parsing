import openpyxl
from loguru import logger

from datetime import date, datetime
import os


def get_path(flag: bool = True) -> str:
    if flag:
        folder = 'start_table'
    else:
        folder = 'table_after_parsing'

    if os.name == 'posix':
        path_to_file = f'{folder}/'
    else:
        path_to_file = f'{folder}\\'

    return path_to_file


def get_start_data_from_excel_table(name: str = 'sample.xlsx') -> dict:
    """
    Данный метод позволит открыть стартовый excel документ для получения необходимых данных для последующего парсинга.
    # name - имя стартовой таблицы (по умолчанию 'sample.xlsx')
    """
    result_data: dict = {
        'search_query': None,       # предполагается строка для последующей отправки запроса
        'categories': None,         # предполагается список с категориями, где первый элемент - верхний уровень
        'cities': None              # предполагается словарь, где ключ - это номер ячейки, в которой находится город,
                                    # а значение - сам город (этот финт нужен для последующей записи полученных данных)
    }

    if f'{name}' not in os.listdir(f'start_table/' if os.name == 'posix' else f'start_table\\'):
        logger.error('ТАБЛИЦА НЕ НАЙДЕНА')
        raise FileNotFoundError

    workbook = openpyxl.load_workbook(f'{get_path()}{name}')
    sheet = workbook.active

    logger.info(f'Открыта стартовая таблица с именем {name}')

    result_data['search_query'] = sheet['B3'].value.strip()
    result_data['categories'] = [value.strip() for value in sheet['B2'].value.split('\n')]

    start_column, start_row = 'A', 8
    column_values: dict = {}
    uniq_cities: set = set()

    for row in range(start_row, sheet.max_row + 1):
        cur_value = sheet[f'{start_column}{row}'].value
        if cur_value is None:
            break
        else:
            final_string = cur_value
            if final_string not in uniq_cities:
                uniq_cities.add(final_string)
                column_values[f'{row}'] = final_string

    result_data['cities'] = column_values
    workbook.close()

    logger.info('Данные извлечены из таблицы и переданы на следующий уровень')
    return result_data


def save_excel_table(final_data: dict) -> str:
    logger.info('Открываем таблицу для сохранения данных по результатам поисковых запросов')
    workbook = openpyxl.load_workbook(filename=f'{get_path()}sample.xlsx')
    sheet = workbook.active

    for row, tpl in final_data.items():
        if len(tpl) == 2:
            sheet[f'C{row}'] = tpl[0]
            sheet[f'D{row}'] = tpl[1]

    curr_date = date.today().strftime('%d_%m_%Y')

    workbook.save(filename=f'{get_path(False)}parsing_{curr_date}.xlsx')
    workbook.close()

    logger.info(f'Таблица сохранена и закрыта с именем: parsing_{curr_date}.xlsx')
    return curr_date


def save_analytic_part(final_data: dict, search_query: list, curr_date: str) -> None:
    logger.info('Открываем таблицу для сохранения данных по результатам аналитики')
    workbook = openpyxl.load_workbook(filename=f'{get_path(False)}parsing_{curr_date}.xlsx')
    sheet = workbook.active

    for row, lst in final_data.items():
        if len(lst) == len(search_query):
            string = ''
            for i in range(len(search_query)):
                string += f'{search_query[i]} - {str(lst[i])}\n'

            sheet[f'B{row}'] = string.strip()

    curr_date = datetime.now().strftime('%d_%m_%Y_%H_%M')
    workbook.save(filename=f'{get_path(False)}parsing_{curr_date}.xlsx')
    workbook.close()

    logger.info(f'Таблица сохранена и закрыта с именем: parsing_{curr_date}.xlsx')


def get_analytic_data(curr_date: str) -> dict:
    logger.info('Открываем таблицу для получения данных на этап аналитики')
    path_to_file = f'{get_path(flag=False)}parsing_{curr_date}.xlsx'

    result_data: dict = {
        'search_query': None,       # предполагается список со строками для поискового запроса
        'category': None,           # предполагается строка с категорией для поиска
        'cities': None              # предполагается словарь, где ключ - это номер ячейки, в которой находится город,
                                    # а значение - сам город (этот финт нужен для последующей записи полученных данных)
                                    # к тому же в словаре будут отсутствовать города, не найденные на предыдущем шаге
    }

    workbook = openpyxl.load_workbook(f'{path_to_file}')
    sheet = workbook.active

    result_data['search_query'] = [value.strip().lower() for value in sheet['B4'].value.split('\n')]
    result_data['category'] = sheet['B5'].value.strip().lower()

    start_column, start_row = 'A', 8
    column_values: dict = {}

    for row in range(start_row, sheet.max_row + 1):
        cur_value = sheet[f'{start_column}{row}'].value
        if cur_value is None:
            break
        else:
            final_string = cur_value
            if (curr_data := sheet[f'C{row}'].value) is not None and str(curr_data).isdigit():
                column_values[f'{row}'] = final_string.strip()

    result_data['cities'] = column_values
    workbook.close()

    logger.info('Данные сохранены - таблица закрыта!')
    return result_data
