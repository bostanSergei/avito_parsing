from bs4 import BeautifulSoup


def parsing_data(html_file: str) -> tuple:
    """
    Задача функции - получить на вход html-страницу и извлечь данные по общему количеству объявлений,
    и о количестве продвигаемых объявлений. Изначально проблема заключается в том, что Авито к каждому
    классу генерирует случайный хвост для защиты от парсинга.
    Функция возвращает кортеж вида: (общее_количество_объявлений, количество_продвигаемых_объявлений)
    """
    soup = BeautifulSoup(html_file, 'lxml')

    count, result = '', 0

    count_items = soup.find_all('span')
    for tag in count_items:
        if 'class' in tag.attrs:
            cur_classes = tag.attrs['class']
            if isinstance(cur_classes, list):
                if any(['page-title-count' in one_class for one_class in cur_classes]):
                    count = tag.text
                    break

    if count != '':
        result = ''.join([i for i in count if i.isdigit()])
        try:
            result = int(result)
        except ValueError:
            print('В процессе перевода количества объявлений в целое число произошла ошибка')

    arrow_count = 0

    arrow_items = soup.find_all('div', attrs={'data-marker': 'catalog-serp'})
    if len(arrow_items) > 0:
        for tag in arrow_items[0].find_all('div'):
            if 'class' in tag.attrs:
                cur_classes = tag.attrs['class']
                if isinstance(cur_classes, list):
                    if any(['styles-arrow' in one_class for one_class in cur_classes]):
                        arrow_count += 1

    return result, arrow_count
