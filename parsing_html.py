from bs4 import BeautifulSoup


# def parsing_data(html_file: str) -> tuple:
#     """
#     Задача функции - получить на вход html-страницу и извлечь данные по общему количеству объявлений,
#     и о количестве продвигаемых объявлений. Изначально проблема заключается в том, что Авито к каждому
#     классу генерирует случайный хвост для защиты от парсинга.
#     Функция возвращает кортеж вида: (общее_количество_объявлений, количество_продвигаемых_объявлений)
#
#     UPD от 01.12.2024
#     Функция будет возвращать словарь. Данных со страницы будем парсить больше!
#     Нам нужно понимать:
#         какие компании выкладывают объявления
#         какое количество объявлений у этой компании общее
#         какое количество объявлений у этой компании продвигается
#     """
#     soup = BeautifulSoup(html_file, 'lxml')
#
#     count, result = '', 0
#
#     count_items = soup.find_all('span')
#     for tag in count_items:
#         if 'class' in tag.attrs:
#             cur_classes = tag.attrs['class']
#             if isinstance(cur_classes, list):
#                 if any(['page-title-count' in one_class for one_class in cur_classes]):
#                     count = tag.text
#                     break
#
#     if count != '':
#         result = ''.join([i for i in count if i.isdigit()])
#         try:
#             result = int(result)
#         except ValueError:
#             print('В процессе перевода количества объявлений в целое число произошла ошибка')
#
#     arrow_count = 0
#
#     arrow_items = soup.find_all('div', attrs={'data-marker': 'catalog-serp'})
#     if len(arrow_items) > 0:
#         for tag in arrow_items[0].find_all('div'):
#             if 'class' in tag.attrs:
#                 cur_classes = tag.attrs['class']
#                 if isinstance(cur_classes, list):
#                     if any(['styles-arrow' in one_class for one_class in cur_classes]):
#                         arrow_count += 1
#
#     return result, arrow_count

def parsing_data(html_file: str) -> dict:
    """
    NEW VERSION
    Задача функции - получить на вход html-страницу и извлечь данные по общему количеству объявлений,
    и о количестве продвигаемых объявлений. Изначально проблема заключается в том, что Авито к каждому
    классу генерирует случайный хвост для защиты от парсинга.

    UPD от 01.12.2024
    Функция будет возвращать словарь. Данных со страницы будем парсить больше!
    Нам нужно понимать:
        какие компании выкладывают объявления
        какое количество объявлений у этой компании общее
        какое количество объявлений у этой компании продвигается
    """
    final_result = {
        'all_ads': None,
        'promoted_ads': None,
        'companies': {}
    }

    soup = BeautifulSoup(html_file, 'lxml')

    count, all_count_ads = '', 0

    count_items = soup.find_all('span')
    for tag in count_items:
        if 'class' in tag.attrs:
            cur_classes = tag.attrs['class']
            if isinstance(cur_classes, list):
                if any(['page-title-count' in one_class for one_class in cur_classes]):
                    count = tag.text
                    break

    if count != '':
        all_count_ads = ''.join([i for i in count if i.isdigit()])
        try:
            all_count_ads = int(all_count_ads)
        except ValueError:
            print('В процессе перевода количества объявлений в целое число произошла ошибка')

    promoted_ads = 0
    place_number = 0

    arrow_items = soup.find_all('div', attrs={'data-marker': 'catalog-serp'})
    if len(arrow_items) > 0:
        all_div_tags = arrow_items[0].find_all('div', attrs={'data-marker': 'item'})

        for tag in all_div_tags:
            pay_flag = False

            icon_tags = tag.find_all('i')
            if len(icon_tags) > 0:
                promoted_ads += 1
                pay_flag = True

            iva_item_aside_divs = tag.find(
                name='div',
                class_=lambda x: x is not None and x.startswith('iva-item-sellerInfo-')
            )

            place_number += 1

            # next_step = iva_item_aside_divs.find(
            #     name='div',
            #     class_=lambda x: x is not None and x.startswith('iva-item-userInfoStep-')
            # )

            link = iva_item_aside_divs.find('a')
            if link:
                paragraph = link.find('p')
                if paragraph:
                    company_name = paragraph.text.strip()
                    if company_name not in final_result['companies']:
                        final_result['companies'][company_name] = {}
                        final_result['companies'][company_name]['count'] = 0
                        final_result['companies'][company_name]['places'] = []
                        final_result['companies'][company_name]['pay_places'] = []

                    final_result['companies'][company_name]['count'] += 1
                    final_result['companies'][company_name]['places'].append(place_number)

                    if pay_flag:
                        final_result['companies'][company_name]['pay_places'].append(place_number)

    final_result['all_ads'] = all_count_ads
    final_result['promoted_ads'] = promoted_ads

    return final_result


def check_string(query_from_site: str, query_from_table: str) -> bool:
    """
    Проверка кнопки в процессе поиска нужного города при парсинге раздела аналитика.
    Предполагается, что к этому моменту все города были проверены и информация о них точно есть на авито
    """
    first_dict, second_dict = {}, {}
    for symbol in query_from_site.lower():
        if symbol.isalpha():
            if symbol not in first_dict:
                first_dict[symbol] = 0
            first_dict[symbol] += 1

    for symbol in query_from_table.lower():
        if symbol.isalpha():
            if symbol not in second_dict:
                second_dict[symbol] = 0
            second_dict[symbol] += 1

    if first_dict != second_dict:
        for symbol in 'асть':
            if symbol not in second_dict:
                second_dict[symbol] = 0
            second_dict[symbol] += 1

    return first_dict == second_dict


def find_query_numbers(html_file: str) -> list:
    soup = BeautifulSoup(html_file, 'lxml')

    legend_markers = soup.find_all('div', attrs={'data-marker': 'totals-legend'})

    analytic_list = []

    if len(legend_markers) > 0:
        for tag in legend_markers[0].find_all('div'):
            if 'class' in tag.attrs:
                cur_classes = tag.attrs['class']
                if isinstance(cur_classes, list):
                    if any(['styles-plate' in one_class for one_class in cur_classes]):
                        count = tag.text
                        analytic_list.append(count)

    for i in range(len(analytic_list)):
        result = ''.join([j for j in analytic_list[i] if j.isdigit()])
        try:
            result = int(result)
            analytic_list[i] = result
        except ValueError:
            print('В процессе перевода количества объявлений в целое число произошла ошибка')

    if len(analytic_list) == 0:
        num = ''
        all_data = soup.find_all('h3')
        if len(all_data) > 0:
            num = ''
            for tag in all_data:
                curr_text = tag.text
                if 'Всего запросов:'.lower() in curr_text.lower().strip():
                    for symb in curr_text:
                        if symb.isdigit():
                            num += symb
                    break
        if len(num) > 0:
            try:
                analytic_list.append(int(num))
            except:
                pass

    return analytic_list
