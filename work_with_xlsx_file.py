import openpyxl

from datetime import date
import os


def get_path() -> str:
    if os.name == 'posix':
        path_to_file = 'start_table/'
    else:
        path_to_file = 'start_table\\'

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

    workbook = openpyxl.load_workbook(f'{get_path()}{name}')
    sheet = workbook.active

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
            final_string = cur_value.replace('ё', 'е')
            if final_string not in uniq_cities:
                uniq_cities.add(final_string)
                column_values[f'{row}'] = final_string

    result_data['cities'] = column_values
    workbook.close()

    return result_data


def save_excel_table(final_data: dict) -> None:
    workbook = openpyxl.load_workbook(filename=f'{get_path()}sample.xlsx')
    sheet = workbook.active

    for row, tpl in final_data.items():
        if len(tpl) == 2:
            sheet[f'C{row}'] = tpl[0]
            sheet[f'D{row}'] = tpl[1]

    curr_date = date.today().strftime('%d_%m_%Y')

    workbook.save(filename=f'parsing_{curr_date}.xlsx')
    workbook.close()
