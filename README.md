## avito-парсер по заказу с фриланс-биржи

**Задачи парсера:**
1. Собрать статистику по количеству размещенных объявлений по заданному ключевому запросу и заданным ГЕО. 
2. Собрать статистику о количестве продвигаемых объявлений по указанным параметрам (см п.1)
3. Собрать статистику из личного кабинета заказчика о количестве поисковых запросов (используется платный бизнес аккаунт)

*Парсер работает по следующему принципу:*
- Перед запуском требуется подготовить excel таблицу в соответствии с оговоренными требованиями. В таблице должен присутствовать поисковый запрос, дерево категорий, в которых будет осуществляться поиск и список городов, по которым нужно пройтись. Список городов ничем не ограничен. Первая пустая ячейка считается концом списка. Таблица должна находиться в папке start_table. Имя таблицы может быть любым. Это имя нужно будет прописать как константу в файле main.
- Парсер открывает указанный файл, переходит на стартовую страницу avito, проваливается по дереву категорий, осуществляет поиск по ключевому запросу и начинает перебирать города из списка, обрабатывая каждую страницу.
- Города, которые avito не находит в списке - игнорируются (в финальной таблице напротив этих городов будет стоять соответствующая пометка). Дубли - не обрабатываются (напротив дублей будет стоять пустая ячейка).
- По итогу формируется новая таблица (копия стартовой) с именем в котором присутствует дата запуска парсера.

### Инструкция по установке (для unix-подобных систем)

1. Склонировать проект на локальную машину
```
git clone https://github.com/bostanSergei/avito_parsing.git
```
2. Провалиться в папку с проектом, установить виртуальное окружение (проект написан и протестирован на python 3.11) и активировать его.
```
cd avito_parsing
python3 -m venv venv
source venv/bin/activate
```
3. Подгрузить все зависимости из файла requirements.txt
```
pip install -r requirements.txt
```
4. Так же потребуется установить playwright браузеры
```
playwrigt install
```
5. Заполнить поля login и password в файле path.py
6. Подготовить стартовую таблицу (пример есть в папке start_table). При заполнении таблицы важно с особым вниманием подойти к формату данных, которые должны располагаться в тех или иных ячейках. Если в ячейке категории, по которым должен провалиться парсер указаны каждая с новой строки - значит нужно указать путь именно в таком формате. Если мы собираемся искать город Орёл - значит именно так его указывать и нужно.

Парсер собирает данные в два этапа: сбор общего количества и количества продвигаемых объявлений по ключевым запросам и ГЕО (<- все это первый этап) И сбор статистики по ключевым запросам из кабинета бизнес аккаунта.
Второй этап - будет выполнен только после первого, поскольку поиск по городам происходит на основе предварительных данных с первого этапа (к примеру, если указанный город на первом этапе не удалось найти - мы не будем его искать и на втором).

Работа парсера забирает достаточно много времени: это связано с задержками в 2, 3, 5-10 секунд между действиями, чтобы имитировать поведения настоящего человека.
В процессе написания этого кода, предполагалось, что он будет запускаться в ручном режиме один-два раза в день. Как следствие - капчу, которую требуется пройти в момент первого "холодного" закпуска скрипта - проходит тот, кто этот скрипт запускает.
После успешной авторизации парсер сохраняет state-файл и дальнейшие запуски в течении одного календарного дня будут выполняться с предварительной загрузкой state-состояния без необходимости выполнять повторный вход в решение капчи.

По вопросам работы скрипта, а также с предложениями, можно писать:
```
tg:@bosmc
```
