#!/bin/bash
cd "$(dirname "$0")" || exit 1
# настройки подключения: переменные PG* из окружения или из .env в корне проекта
[ -f .env ] && set -a && . .env && set +a
DATABASE="${PGDATABASE:-taxi}"
# Windows: psql выводит свои русские надписи («(1 строка)») в кодировке ANSI,
# в консоли UTF-8 они нечитаемы — там они на английском, данные остаются русскими
case "$OSTYPE" in msys*|cygwin*) export LC_MESSAGES=C ;; esac
PYTHON=python3
# в Windows python3 бывает заглушкой Microsoft Store, которая не запускается
"$PYTHON" -c "" 2>/dev/null || PYTHON=python

# числовой параметр: защищает запросы от подстановки произвольного текста
need_num() {
    if ! [[ "$1" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
        echo "ОШИБКА: ожидается число, получено '$1'"
        exit 1
    fi
}

# запрос через stdin, а не -c: в Windows аргументы командной строки
# доходят до psql в кодировке ANSI и кириллица в них ломается
sql() {
    printf '%s\n' "$1" | psql -d "$DATABASE"
}

# текстовый параметр для SQL: одинарные кавычки удваиваются
sql_str() {
    printf "%s" "${1//\'/\'\'}"
}

# SQL-файл с необязательным параметром arg1. Параметр задаётся командой \set
# через stdin, а не psql -v: по той же причине кириллица в -v ломается
sql_file() {
    if [ -z "$2" ]; then
        psql -d "$DATABASE" -f "$1"
        return
    fi
    # в \set внутри '...' обратная косая черта — спецсимвол, кавычка удваивается
    local value="${2//\\/\\\\}"
    value="${value//\'/\'\'}"
    { printf '\\set arg1 '"'"'%s'"'"'\n' "$value"; cat "$1"; } | psql -d "$DATABASE"
}

if [ -z "$1" ]; then
    echo "============================================="
    echo "  БАЗА ДАННЫХ TAXI (реальные поездки такси Чикаго)"
    echo "============================================="
    echo ""
    echo "================== ДАННЫЕ =================="
    echo "  ./help.sh fetch [дней] - скачать недостающие дни из открытых данных Чикаго"
    echo "  ./help.sh load - загрузить скачанные поездки в базу (только новые)"
    echo "  ./help.sh rebuild - полностью пересоздать базу и загрузить все поездки"
    echo ""
    echo "================== ОСНОВНЫЕ ЗАДАЧИ =================="
    echo "  ./help.sh task1 - выручка по сезонам"
    echo "  ./help.sh task2 - выручка по сезонам и таксопаркам"
    echo "  ./help.sh task3 - выручка по дням недели и водителям"
    echo "  ./help.sh task4 день - выручка по водителям за день"
    echo ""
    echo "================== ПРОСМОТР ДАННЫХ =================="
    echo "  ./help.sh 01 - все таксопарки"
    echo "  ./help.sh 02 - водители (первые 50)"
    echo "  ./help.sh 03 - типы клиентов"
    echo "  ./help.sh 04 - количество поездок"
    echo "  ./help.sh 05 - последние поездки"
    echo "  ./help.sh 06 - типы клиентов с числом поездок"
    echo "  ./help.sh 16 - структура таблиц"
    echo ""
    echo "================== ДЕМОНСТРАЦИЯ JOIN =================="
    echo "  ./help.sh 07 - INNER JOIN"
    echo "  ./help.sh 08 - LEFT JOIN"
    echo "  ./help.sh 09 - RIGHT JOIN"
    echo "  ./help.sh 10 - FULL JOIN"
    echo "  ./help.sh 11 - CROSS JOIN"
    echo "  ./help.sh 12 - SELF JOIN"
    echo ""
    echo "================== ПОКАЗАТЬ ДО/ПОСЛЕ =================="
    echo "  ./help.sh 60 - ДО UPDATE"
    echo "  ./help.sh 61 - ВЫПОЛНИТЬ UPDATE"
    echo "  ./help.sh 62 - ПОСЛЕ UPDATE"
    echo "  ./help.sh 63 - ДО DELETE"
    echo "  ./help.sh 64 - ВЫПОЛНИТЬ DELETE"
    echo "  ./help.sh 65 - ПОСЛЕ DELETE"
    echo ""
    echo "================== АНАЛИТИКА =================="
    echo "  ./help.sh 17 - топ-10 районов по выручке"
    echo "  ./help.sh 18 - топ-10 водителей по выручке"
    echo "  ./help.sh 19 - выручка по месяцам"
    echo "  ./help.sh 20 - средний чек"
    echo "  ./help.sh 21 - поездки по часам"
    echo "  ./help.sh 22 - статистика по таксопаркам"
    echo "  ./help.sh 23 - загруженность водителей"
    echo "  ./help.sh 24 - средние чаевые по типам клиентов"
    echo "  ./help.sh 25 - выручка по дням недели"
    echo "  ./help.sh 26 - выручка по типам клиентов"
    echo "  ./help.sh 27 - средний пробег по таксопаркам"
    echo "  ./help.sh 28 - распределение поездок по часам"
    echo "  ./help.sh 29 - средний чек по часам"
    echo "  ./help.sh 30 - топ-10 водителей по чаевым"
    echo ""
    echo "================== ЗАПРОСЫ С ПАРАМЕТРАМИ =================="
    echo "  ./help.sh 31 текст - таксопарки по части названия"
    echo "  ./help.sh 32 код - информация о водителе"
    echo "  ./help.sh 33 код - последние поездки водителя"
    echo "  ./help.sh 34 сумма - поездки дороже суммы"
    echo "  ./help.sh 35 сумма - водители с выручкой выше суммы"
    echo "  ./help.sh 40 код название - переименовать таксопарк"
    echo "  ./help.sh 41 код описание - изменить описание типа клиента"
    echo "  ./help.sh 42 код - удалить водителя вместе с поездками"
    echo "  ./help.sh 43 название - добавить таксопарк"
    echo "  ./help.sh 44 taxi_id - добавить водителя"
    echo "  ./help.sh 45 код_поездки код_таксопарка - сменить таксопарк поездки"
    echo "  ./help.sh 46 код_поездки сумма - изменить чаевые поездки"
    echo ""
    echo "================== ПРЕДСТАВЛЕНИЯ =================="
    echo "  ./help.sh 100 - создать пользовательское представление"
    echo "  ./help.sh 101 - создать технологическое представление"
    echo "  ./help.sh 102 - проверить представления"
    echo ""
    echo "================== ПОДЗАПРОСЫ =================="
    echo "  ./help.sh 110 - задача 1.1 отклонение стоимости поездки"
    echo "  ./help.sh 111 - задача 1.2 рейтинг таксопарков"
    echo "  ./help.sh 112 - задача 2.1 поездки дороже среднего по таксопарку"
    echo "  ./help.sh 113 - задача 2.2 статистика по таксопаркам"
    echo "  ./help.sh 114 - задача 3.1 топ-3 водителя в каждом таксопарке"
    echo "  ./help.sh 115 код - задача 4.1 поездки дороже среднего по водителю"
    echo "  ./help.sh 116 - задача 4.2 водители без поездок дешевле \$10"
    echo "  ./help.sh 117 - задача 4.3 лучшие водители"
    echo "  ./help.sh 118 - самые дорогие поездки"
    echo "  ./help.sh 199 - выполнить все запросы с подзапросами"
    echo ""
    echo "================== ФУНКЦИИ =================="
    echo "  ./help.sh 200 - создать все функции"
    echo "  ./help.sh 201 порог - водители с выручкой выше порога"
    echo "  ./help.sh 202 - выручка по таксопаркам и сезонам"
    echo "  ./help.sh 203 - сводная таблица (водители x способы оплаты)"
    echo "  ./help.sh 204 - выполнить всё"
    echo ""
    echo "================== ЗАПУСК SQL ФАЙЛОВ =================="
    echo "  ./help.sh файл.sql [параметр] - выполнить SQL-файл"
    echo "  ./help.sh h1 файл.sql [параметр] - выполнить SQL-файл через run_sql.sh"
    exit 1
fi

if [[ "$1" == *.sql ]]; then
    if [ -f "$1" ]; then
        sql_file "$1" "$2"
    else
        echo "ОШИБКА: Файл $1 не найден"
        exit 1
    fi
    exit 0
fi

if [ "$1" = "h1" ]; then
    shift
    ./run_sql.sh "$@"
    exit 0
fi

case "$1" in
    fetch) "$PYTHON" parser/chicago_fetch.py ${2:+--days "$2"} ;;
    load) "$PYTHON" parser/load_rides.py ;;
    rebuild) ./setup/rebuild.sh ;;
    task1) psql -d "$DATABASE" -f queries/tasks/01_revenue_by_season.sql ;;
    task2) psql -d "$DATABASE" -f queries/tasks/02_revenue_by_season_and_class.sql ;;
    task3) psql -d "$DATABASE" -f queries/tasks/03_revenue_by_day_and_driver.sql ;;
    task4)
        if [ -z "$2" ]; then
            echo "ОШИБКА: Укажите день недели 1-7"
            exit 1
        elif ! [[ "$2" =~ ^[0-9]+$ ]]; then
            echo "ОШИБКА: День должен быть числом"
            exit 1
        elif [ "$2" -lt 1 ] || [ "$2" -gt 7 ]; then
            echo "ОШИБКА: День должен быть от 1 до 7"
            exit 1
        else
            sql_file queries/tasks/04_revenue_by_driver_for_day.sql "$2"
        fi
        ;;
    01) psql -d "$DATABASE" -f helper/01_show_all_cars.sql ;;
    02) psql -d "$DATABASE" -f helper/02_show_all_drivers.sql ;;
    03) psql -d "$DATABASE" -f helper/03_show_all_clients.sql ;;
    04) sql "SELECT COUNT(*) AS поездок, MIN(дата)::date AS с, MAX(дата)::date AS по FROM ПОЕЗДКИ;" ;;
    05) sql "SELECT код_поездки, дата, расстояние_км, стоимость, чаевые FROM ПОЕЗДКИ ORDER BY дата DESC LIMIT 10;" ;;
    06) sql "SELECT К.код, К.тип, К.описание, COUNT(П.код_поездки) AS поездок FROM КЛИЕНТЫ К LEFT JOIN ПОЕЗДКИ П ON П.клиент = К.код GROUP BY К.код ORDER BY поездок DESC;" ;;
    07) sql "SELECT П.код_поездки, Т.название AS таксопарк, 'Водитель №' || В.код AS водитель, П.стоимость FROM ПОЕЗДКИ П INNER JOIN ТАКСОПАРКИ Т ON П.таксопарк = Т.код INNER JOIN ВОДИТЕЛИ В ON П.водитель = В.код LIMIT 10;" ;;
    08) sql "SELECT Р.название AS район, COUNT(П.код_поездки) AS поездок FROM РАЙОНЫ Р LEFT JOIN ПОЕЗДКИ П ON Р.код = П.откуда GROUP BY Р.код, Р.название ORDER BY поездок ASC LIMIT 10;" ;;
    09) sql "SELECT К.описание AS тип_клиента, COUNT(П.код_поездки) AS поездок FROM ПОЕЗДКИ П RIGHT JOIN КЛИЕНТЫ К ON П.клиент = К.код GROUP BY К.код, К.описание ORDER BY поездок DESC LIMIT 10;" ;;
    10) sql "SELECT Т.название AS таксопарк, К.описание AS тип_клиента FROM ТАКСОПАРКИ Т FULL JOIN КЛИЕНТЫ К ON Т.код = К.код LIMIT 10;" ;;
    11) sql "SELECT Т.название AS таксопарк, К.описание AS тип_клиента FROM ТАКСОПАРКИ Т CROSS JOIN КЛИЕНТЫ К LIMIT 10;" ;;
    12) sql "SELECT Р1.название AS район, Р2.название AS соседний_к_северу, ROUND(Р2.широта - Р1.широта, 3) AS разница_широт FROM РАЙОНЫ Р1 JOIN РАЙОНЫ Р2 ON Р2.широта > Р1.широта AND Р2.широта - Р1.широта < 0.02 AND ABS(Р2.долгота - Р1.долгота) < 0.02 AND Р1.код != Р2.код ORDER BY Р1.название LIMIT 10;" ;;
    16) sql "\d" ;;
    17) psql -d "$DATABASE" -f helper/17_top_10_cars_by_revenue.sql ;;
    18) psql -d "$DATABASE" -f helper/18_top_10_drivers_by_revenue.sql ;;
    19) sql "SELECT TO_CHAR(DATE_TRUNC('month', дата), 'YYYY-MM') AS месяц, COUNT(*) AS поездок, SUM(стоимость) AS выручка FROM ПОЕЗДКИ GROUP BY 1 ORDER BY 1;" ;;
    20) sql "SELECT ROUND(AVG(стоимость), 2) AS средний, MIN(стоимость) AS мин, MAX(стоимость) AS макс FROM ПОЕЗДКИ;" ;;
    21) sql "SELECT EXTRACT(HOUR FROM дата) AS час, COUNT(*) AS поездок, SUM(стоимость) AS выручка FROM ПОЕЗДКИ GROUP BY час ORDER BY час;" ;;
    22) psql -d "$DATABASE" -f helper/25_stats_by_class.sql ;;
    23) sql "SELECT 'Водитель №' || В.код AS водитель, COUNT(П.код_поездки) AS поездок, ROUND(SUM(П.время_мин) / 60.0, 1) AS часов_в_пути FROM ВОДИТЕЛИ В JOIN ПОЕЗДКИ П ON В.код = П.водитель GROUP BY В.код ORDER BY поездок DESC LIMIT 10;" ;;
    24) sql "SELECT К.описание AS тип_клиента, ROUND(AVG(П.чаевые), 2) AS средние_чаевые, ROUND(100.0 * AVG(П.чаевые / П.стоимость), 1) AS процент_от_стоимости FROM ПОЕЗДКИ П JOIN КЛИЕНТЫ К ON К.код = П.клиент GROUP BY К.описание ORDER BY средние_чаевые DESC;" ;;
    25) sql "SELECT EXTRACT(ISODOW FROM дата) AS день, COUNT(*) AS поездок, SUM(стоимость) AS выручка FROM ПОЕЗДКИ GROUP BY день ORDER BY день;" ;;
    26) sql "SELECT К.описание AS тип_клиента, COUNT(*) AS поездок, SUM(П.стоимость) AS выручка FROM КЛИЕНТЫ К JOIN ПОЕЗДКИ П ON К.код = П.клиент GROUP BY К.код, К.описание ORDER BY выручка DESC;" ;;
    27) sql "SELECT Т.название AS таксопарк, ROUND(AVG(П.расстояние_км), 2) AS средний_пробег_км FROM ПОЕЗДКИ П JOIN ТАКСОПАРКИ Т ON П.таксопарк = Т.код GROUP BY Т.название ORDER BY средний_пробег_км DESC;" ;;
    28) sql "SELECT EXTRACT(HOUR FROM дата) AS час, COUNT(*) AS поездок, ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS процент FROM ПОЕЗДКИ GROUP BY час ORDER BY час;" ;;
    29) sql "SELECT EXTRACT(HOUR FROM дата) AS час, ROUND(AVG(стоимость), 2) AS средний_чек FROM ПОЕЗДКИ GROUP BY час ORDER BY час;" ;;
    30) sql "SELECT 'Водитель №' || В.код AS водитель, COUNT(*) AS поездок, SUM(П.чаевые) AS чаевые FROM ПОЕЗДКИ П JOIN ВОДИТЕЛИ В ON П.водитель = В.код GROUP BY В.код ORDER BY чаевые DESC LIMIT 10;" ;;
    31) if [ -z "$2" ]; then echo "Укажите часть названия: ./help.sh 31 Cab"; else sql_file helper/15_demo_with_param.sql "$2"; fi ;;
    32) if [ -z "$2" ]; then echo "Укажите код: ./help.sh 32 1"; else need_num "$2"; sql "SELECT В.код, В.taxi_id, COUNT(П.код_поездки) AS поездок, SUM(П.стоимость) AS выручка, MIN(П.дата)::date AS первая, MAX(П.дата)::date AS последняя FROM ВОДИТЕЛИ В LEFT JOIN ПОЕЗДКИ П ON П.водитель = В.код WHERE В.код = $2 GROUP BY В.код;"; fi ;;
    33) if [ -z "$2" ]; then echo "Укажите код: ./help.sh 33 1"; else need_num "$2"; sql "SELECT * FROM v_rides_user WHERE водитель = 'Водитель №$2' ORDER BY дата DESC LIMIT 10;"; fi ;;
    34) if [ -z "$2" ]; then echo "Укажите сумму: ./help.sh 34 100"; else need_num "$2"; sql "SELECT * FROM ПОЕЗДКИ WHERE стоимость > $2 ORDER BY стоимость DESC LIMIT 10;"; fi ;;
    35) if [ -z "$2" ]; then echo "Укажите сумму: ./help.sh 35 10000"; else need_num "$2"; sql "SELECT 'Водитель №' || В.код AS водитель, SUM(П.стоимость) AS выручка FROM ВОДИТЕЛИ В JOIN ПОЕЗДКИ П ON В.код = П.водитель GROUP BY В.код HAVING SUM(П.стоимость) > $2 ORDER BY выручка DESC;"; fi ;;
    40) if [ -z "$2" ] || [ -z "$3" ]; then echo "Использование: ./help.sh 40 код название"; else need_num "$2"; sql "UPDATE ТАКСОПАРКИ SET название = '$(sql_str "$3")' WHERE код = $2; SELECT * FROM ТАКСОПАРКИ WHERE код = $2;"; fi ;;
    41) if [ -z "$2" ] || [ -z "$3" ]; then echo "Использование: ./help.sh 41 код описание"; else need_num "$2"; sql "UPDATE КЛИЕНТЫ SET описание = '$(sql_str "$3")' WHERE код = $2; SELECT * FROM КЛИЕНТЫ WHERE код = $2;"; fi ;;
    42) if [ -z "$2" ]; then echo "Использование: ./help.sh 42 код"; else need_num "$2"; sql "DELETE FROM ПОЕЗДКИ WHERE водитель = $2; DELETE FROM ВОДИТЕЛИ WHERE код = $2;"; echo "Водитель удалён"; fi ;;
    43) if [ -z "$2" ]; then echo "Использование: ./help.sh 43 название"; else sql "INSERT INTO ТАКСОПАРКИ (название) VALUES ('$(sql_str "$2")'); SELECT * FROM ТАКСОПАРКИ ORDER BY код DESC LIMIT 1;"; fi ;;
    44) if [ -z "$2" ]; then echo "Использование: ./help.sh 44 taxi_id"; else sql "INSERT INTO ВОДИТЕЛИ (taxi_id) VALUES ('$(sql_str "$2")'); SELECT * FROM ВОДИТЕЛИ ORDER BY код DESC LIMIT 1;"; fi ;;
    45) if [ -z "$2" ] || [ -z "$3" ]; then echo "Использование: ./help.sh 45 код_поездки код_таксопарка"; else need_num "$2"; need_num "$3"; sql "UPDATE ПОЕЗДКИ SET таксопарк = $3 WHERE код_поездки = $2; SELECT * FROM v_rides_user WHERE код_поездки = $2;"; fi ;;
    46) if [ -z "$2" ] || [ -z "$3" ]; then echo "Использование: ./help.sh 46 код_поездки сумма"; else need_num "$2"; need_num "$3"; sql "UPDATE ПОЕЗДКИ SET чаевые = $3 WHERE код_поездки = $2; SELECT * FROM v_rides_user WHERE код_поездки = $2;"; fi ;;
    60) psql -d "$DATABASE" -f helper/60_before_update.sql ;;
    61) psql -d "$DATABASE" -f helper/61_do_update.sql ;;
    62) psql -d "$DATABASE" -f helper/62_after_update.sql ;;
    63) psql -d "$DATABASE" -f helper/63_before_delete.sql ;;
    64) psql -d "$DATABASE" -f helper/64_do_delete.sql ;;
    65) psql -d "$DATABASE" -f helper/65_after_delete.sql ;;
    100) psql -d "$DATABASE" -f queries/views/01_create_rides_view.sql ;;
    101) psql -d "$DATABASE" -f queries/views/02_create_rides_tech.sql ;;
    102) psql -d "$DATABASE" -f queries/views/03_check_views.sql ;;
    110) psql -d "$DATABASE" -f queries/subqueries/01_price_deviation.sql ;;
    111) psql -d "$DATABASE" -f queries/subqueries/02_car_rating.sql ;;
    112) psql -d "$DATABASE" -f queries/subqueries/03_rides_above_avg.sql ;;
    113) psql -d "$DATABASE" -f queries/subqueries/04_class_stats.sql ;;
    114) psql -d "$DATABASE" -f queries/subqueries/05_top_drivers_lateral.sql ;;
    115) if [ -z "$2" ]; then echo "Использование: ./help.sh 115 код_водителя"; echo "Пример: ./help.sh 115 1"; else need_num "$2"; sql_file queries/subqueries/06_rides_above_avg_param.sql "$2"; fi ;;
    116) psql -d "$DATABASE" -f queries/subqueries/07_good_drivers_exists.sql ;;
    117) psql -d "$DATABASE" -f queries/subqueries/08_best_drivers_all.sql ;;
    118) sql "SELECT * FROM v_rides_user ORDER BY стоимость DESC LIMIT 10;" ;;
    199)
        echo "============================================="
        echo "ПРЕДСТАВЛЕНИЯ И ПОДЗАПРОСЫ - ВСЕ ЗАДАЧИ"
        echo "============================================="
        psql -d "$DATABASE" -f queries/views/03_check_views.sql
        psql -d "$DATABASE" -f queries/subqueries/01_price_deviation.sql
        psql -d "$DATABASE" -f queries/subqueries/02_car_rating.sql
        psql -d "$DATABASE" -f queries/subqueries/03_rides_above_avg.sql
        psql -d "$DATABASE" -f queries/subqueries/04_class_stats.sql
        psql -d "$DATABASE" -f queries/subqueries/05_top_drivers_lateral.sql
        psql -d "$DATABASE" -v arg1=1 -f queries/subqueries/06_rides_above_avg_param.sql
        psql -d "$DATABASE" -f queries/subqueries/07_good_drivers_exists.sql
        psql -d "$DATABASE" -f queries/subqueries/08_best_drivers_all.sql
        ;;
    200)
        echo "============================================="
        echo "СОЗДАНИЕ ФУНКЦИЙ"
        echo "============================================="
        psql -d "$DATABASE" -f queries/functions/01_create_functions_task1.sql
        psql -d "$DATABASE" -f queries/functions/02_create_functions_task2.sql
        psql -d "$DATABASE" -f queries/functions/03_create_functions_task3.sql
        echo " Все функции созданы"
        ;;
    201)
        if [ -z "$2" ]; then
            echo "Использование: ./help.sh 201 <порог>"
            echo "Пример: ./help.sh 201 10000"
            echo ""
            sql "SELECT * FROM drivers_above_revenue(10000) LIMIT 20;"
        else
            need_num "$2"
            sql "SELECT * FROM drivers_above_revenue($2) LIMIT 20;"
        fi
        ;;
    202)
        echo "============================================="
        echo "ВЫРУЧКА ПО ТАКСОПАРКАМ И СЕЗОНАМ"
        echo "============================================="
        sql "SELECT * FROM revenue_by_company_and_season();"
        ;;
    203)
        echo "============================================="
        echo "СВОДНАЯ ТАБЛИЦА (ВОДИТЕЛИ x СПОСОБЫ ОПЛАТЫ)"
        echo "============================================="
        sql "SELECT * FROM display_pivot_table();"
        ;;
    204)
        echo "============================================="
        echo "ФУНКЦИИ - ВСЕ ЗАДАЧИ"
        echo "============================================="
        ./help.sh 200
        echo ""
        echo "=== ЗАДАЧА 1 ==="
        ./help.sh 201 10000
        echo ""
        echo "=== ЗАДАЧА 2 ==="
        ./help.sh 202
        echo ""
        echo "=== ЗАДАЧА 3 ==="
        ./help.sh 203
        ;;
    *) echo "ОШИБКА: Неизвестная команда $1" ;;
esac
