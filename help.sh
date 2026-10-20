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

# psql по умолчанию продолжает работу после ошибки SQL и возвращает 0;
# с ON_ERROR_STOP он останавливается и возвращает ненулевой код (на этом держатся автотесты)
psql() {
    command psql -v ON_ERROR_STOP=1 "$@"
}

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
    echo "  Число перед описанием - прежний номер команды, он тоже работает:"
    echo "  ./help.sh companies и ./help.sh 01 делают одно и то же."
    echo ""
    echo "================== ДАННЫЕ =================="
    echo "  ./help.sh fetch [дней]                            скачать недостающие дни из открытых данных Чикаго"
    echo "  ./help.sh load [--all]                            загрузить новые дни в базу; --all - перечитать все файлы"
    echo "  ./help.sh rebuild                                 полностью пересоздать базу и загрузить все поездки"
    echo ""
    echo "================== ОСНОВНЫЕ ЗАДАЧИ =================="
    echo "  ./help.sh task1                                   выручка по сезонам"
    echo "  ./help.sh task2                                   выручка по сезонам и таксопаркам"
    echo "  ./help.sh task3                                   выручка по дням недели и водителям"
    echo "  ./help.sh task4 день                              выручка по водителям за день"
    echo ""
    echo "================== ПРОСМОТР ДАННЫХ =================="
    echo "  ./help.sh companies                           01  все таксопарки"
    echo "  ./help.sh drivers                             02  водители (первые 50)"
    echo "  ./help.sh clients                             03  типы клиентов"
    echo "  ./help.sh count                               04  количество поездок"
    echo "  ./help.sh latest                              05  последние поездки"
    echo "  ./help.sh clients-rides                       06  типы клиентов с числом поездок"
    echo "  ./help.sh tables                              16  список таблиц и представлений"
    echo "  ./help.sh columns                                 колонки и типы всех таблиц"
    echo ""
    echo "================== ДЕМОНСТРАЦИЯ JOIN =================="
    echo "  ./help.sh join-inner                          07  INNER JOIN"
    echo "  ./help.sh join-left                           08  LEFT JOIN"
    echo "  ./help.sh join-right                          09  RIGHT JOIN"
    echo "  ./help.sh join-full                           10  FULL JOIN"
    echo "  ./help.sh join-cross                          11  CROSS JOIN"
    echo "  ./help.sh join-self                           12  SELF JOIN"
    echo ""
    echo "================== ПОКАЗАТЬ ДО/ПОСЛЕ =================="
    echo "  ./help.sh update-before                       60  ДО UPDATE"
    echo "  ./help.sh update-do                           61  ВЫПОЛНИТЬ UPDATE"
    echo "  ./help.sh update-after                        62  ПОСЛЕ UPDATE"
    echo "  ./help.sh delete-before                       63  ДО DELETE"
    echo "  ./help.sh delete-do                           64  ВЫПОЛНИТЬ DELETE"
    echo "  ./help.sh delete-after                        65  ПОСЛЕ DELETE"
    echo ""
    echo "================== АНАЛИТИКА =================="
    echo "  ./help.sh top-areas                           17  топ-10 районов по выручке"
    echo "  ./help.sh top-drivers                         18  топ-10 водителей по выручке"
    echo "  ./help.sh by-month                            19  выручка по месяцам"
    echo "  ./help.sh avg-check                           20  средний чек"
    echo "  ./help.sh by-hour                             21  поездки по часам"
    echo "  ./help.sh company-stats                       22  статистика по таксопаркам"
    echo "  ./help.sh driver-load                         23  загруженность водителей"
    echo "  ./help.sh tips-by-client                      24  средние чаевые по типам клиентов"
    echo "  ./help.sh by-weekday                          25  выручка по дням недели"
    echo "  ./help.sh revenue-by-client                   26  выручка по типам клиентов"
    echo "  ./help.sh distance-by-company                 27  средний пробег по таксопаркам"
    echo "  ./help.sh hour-share                          28  распределение поездок по часам"
    echo "  ./help.sh check-by-hour                       29  средний чек по часам"
    echo "  ./help.sh top-tips                            30  топ-10 водителей по чаевым"
    echo ""
    echo "================== ЗАПРОСЫ С ПАРАМЕТРАМИ =================="
    echo "  ./help.sh find-company текст                  31  таксопарки по части названия"
    echo "  ./help.sh driver код                          32  информация о водителе"
    echo "  ./help.sh driver-rides код                    33  последние поездки водителя"
    echo "  ./help.sh rides-above сумма                   34  поездки дороже суммы"
    echo "  ./help.sh drivers-above сумма                 35  водители с выручкой выше суммы"
    echo "  ./help.sh rename-company код название         40  переименовать таксопарк"
    echo "  ./help.sh client-desc код описание            41  изменить описание типа клиента"
    echo "  ./help.sh delete-driver код                   42  удалить водителя вместе с поездками"
    echo "  ./help.sh add-company название                43  добавить таксопарк"
    echo "  ./help.sh add-driver taxi_id                  44  добавить водителя"
    echo "  ./help.sh set-ride-company поездка парк       45  сменить таксопарк поездки (коды)"
    echo "  ./help.sh set-tips поездка сумма              46  изменить чаевые поездки"
    echo ""
    echo "================== ПРЕДСТАВЛЕНИЯ =================="
    echo "  ./help.sh view-user                          100  создать пользовательское представление"
    echo "  ./help.sh view-tech                          101  создать технологическое представление"
    echo "  ./help.sh view-check                         102  проверить представления"
    echo ""
    echo "================== ПОДЗАПРОСЫ =================="
    echo "  ./help.sh sub-deviation                      110  задача 1.1 отклонение стоимости поездки"
    echo "  ./help.sh sub-company-rating                 111  задача 1.2 рейтинг таксопарков"
    echo "  ./help.sh sub-above-company-avg              112  задача 2.1 поездки дороже среднего по таксопарку"
    echo "  ./help.sh sub-company-stats                  113  задача 2.2 статистика по таксопаркам"
    echo "  ./help.sh sub-top3                           114  задача 3.1 топ-3 водителя в каждом таксопарке"
    echo "  ./help.sh sub-above-driver-avg код           115  задача 4.1 поездки дороже среднего по водителю"
    echo "  ./help.sh sub-good-drivers                   116  задача 4.2 водители без поездок дешевле \$10"
    echo "  ./help.sh sub-best-drivers                   117  задача 4.3 лучшие водители"
    echo "  ./help.sh sub-expensive                      118  самые дорогие поездки"
    echo "  ./help.sh sub-all                            199  выполнить все запросы с подзапросами"
    echo ""
    echo "================== ФУНКЦИИ =================="
    echo "  ./help.sh func-create                        200  создать все функции"
    echo "  ./help.sh func-drivers-above порог           201  водители с выручкой выше порога"
    echo "  ./help.sh func-company-season                202  выручка по таксопаркам и сезонам"
    echo "  ./help.sh func-pivot                         203  сводная таблица (водители x способы оплаты)"
    echo "  ./help.sh func-all                           204  выполнить всё"
    echo ""
    echo "================== ЗАПУСК SQL ФАЙЛОВ =================="
    echo "  ./help.sh файл.sql [параметр]                     выполнить SQL-файл"
    echo "  ./help.sh h1 файл.sql [параметр]                  выполнить SQL-файл через run_sql.sh"
    exit 1
fi

if [[ "$1" == *.sql ]]; then
    if [ -f "$1" ]; then
        sql_file "$1" "$2"
        exit $?
    else
        echo "ОШИБКА: Файл $1 не найден"
        exit 1
    fi
fi

if [ "$1" = "h1" ]; then
    shift
    ./run_sql.sh "$@"
    exit $?
fi

case "$1" in
    fetch) "$PYTHON" parser/chicago_fetch.py ${2:+--days "$2"} ;;
    load) "$PYTHON" parser/load_rides.py "${@:2}" ;;
    rebuild) ./setup/rebuild.sh ;;
    task1) psql -d "$DATABASE" -f queries/tasks/01_revenue_by_season.sql ;;
    task2) psql -d "$DATABASE" -f queries/tasks/02_revenue_by_season_and_company.sql ;;
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
    companies|01) psql -d "$DATABASE" -f helper/01_show_all_companies.sql ;;
    drivers|02) psql -d "$DATABASE" -f helper/02_show_all_drivers.sql ;;
    clients|03) psql -d "$DATABASE" -f helper/03_show_all_clients.sql ;;
    count|04) sql "SELECT COUNT(*) AS поездок, MIN(дата)::date AS с, MAX(дата)::date AS по FROM ПОЕЗДКИ;" ;;
    latest|05) psql -d "$DATABASE" -f helper/05_show_rides_sample.sql ;;
    clients-rides|06) sql "SELECT К.код, К.тип, К.описание, COUNT(П.код_поездки) AS поездок FROM КЛИЕНТЫ К LEFT JOIN ПОЕЗДКИ П ON П.клиент = К.код GROUP BY К.код ORDER BY поездок DESC;" ;;
    join-inner|07) sql "SELECT П.код_поездки, Т.название AS таксопарк, 'Водитель №' || В.код AS водитель, П.стоимость FROM ПОЕЗДКИ П INNER JOIN ТАКСОПАРКИ Т ON П.таксопарк = Т.код INNER JOIN ВОДИТЕЛИ В ON П.водитель = В.код LIMIT 10;" ;;
    join-left|08) sql "SELECT Р.название AS район, COUNT(П.код_поездки) AS поездок FROM РАЙОНЫ Р LEFT JOIN ПОЕЗДКИ П ON Р.код = П.откуда GROUP BY Р.код, Р.название ORDER BY поездок ASC LIMIT 10;" ;;
    join-right|09) sql "SELECT К.описание AS тип_клиента, COUNT(П.код_поездки) AS поездок FROM ПОЕЗДКИ П RIGHT JOIN КЛИЕНТЫ К ON П.клиент = К.код GROUP BY К.код, К.описание ORDER BY поездок DESC LIMIT 10;" ;;
    join-full|10) sql "SELECT Т.название AS таксопарк, К.описание AS тип_клиента FROM ТАКСОПАРКИ Т FULL JOIN КЛИЕНТЫ К ON Т.код = К.код LIMIT 10;" ;;
    join-cross|11) psql -d "$DATABASE" -f helper/08_demo_cross_join.sql ;;
    join-self|12) sql "SELECT Р1.название AS район, Р2.название AS соседний_к_северу, ROUND(Р2.широта - Р1.широта, 3) AS разница_широт FROM РАЙОНЫ Р1 JOIN РАЙОНЫ Р2 ON Р2.широта > Р1.широта AND Р2.широта - Р1.широта < 0.02 AND ABS(Р2.долгота - Р1.долгота) < 0.02 AND Р1.код != Р2.код ORDER BY Р1.название LIMIT 10;" ;;
    tables|16) sql "\d" ;;
    columns) psql -d "$DATABASE" -f helper/16_show_table_structure.sql ;;
    top-areas|17) psql -d "$DATABASE" -f helper/17_top_10_areas_by_revenue.sql ;;
    top-drivers|18) psql -d "$DATABASE" -f helper/18_top_10_drivers_by_revenue.sql ;;
    by-month|19) sql "SELECT TO_CHAR(DATE_TRUNC('month', дата), 'YYYY-MM') AS месяц, COUNT(*) AS поездок, SUM(стоимость) AS выручка FROM ПОЕЗДКИ GROUP BY 1 ORDER BY 1;" ;;
    avg-check|20) sql "SELECT ROUND(AVG(стоимость), 2) AS средний, MIN(стоимость) AS мин, MAX(стоимость) AS макс FROM ПОЕЗДКИ;" ;;
    by-hour|21) sql "SELECT EXTRACT(HOUR FROM дата) AS час, COUNT(*) AS поездок, SUM(стоимость) AS выручка FROM ПОЕЗДКИ GROUP BY час ORDER BY час;" ;;
    company-stats|22) psql -d "$DATABASE" -f helper/25_stats_by_company.sql ;;
    driver-load|23) sql "SELECT 'Водитель №' || В.код AS водитель, COUNT(П.код_поездки) AS поездок, ROUND(SUM(П.время_мин) / 60.0, 1) AS часов_в_пути FROM ВОДИТЕЛИ В JOIN ПОЕЗДКИ П ON В.код = П.водитель GROUP BY В.код ORDER BY поездок DESC LIMIT 10;" ;;
    tips-by-client|24) sql "SELECT К.описание AS тип_клиента, ROUND(AVG(П.чаевые), 2) AS средние_чаевые, ROUND(100.0 * AVG(П.чаевые / П.стоимость), 1) AS процент_от_стоимости FROM ПОЕЗДКИ П JOIN КЛИЕНТЫ К ON К.код = П.клиент GROUP BY К.описание ORDER BY средние_чаевые DESC;" ;;
    by-weekday|25) sql "SELECT EXTRACT(ISODOW FROM дата) AS день, COUNT(*) AS поездок, SUM(стоимость) AS выручка FROM ПОЕЗДКИ GROUP BY день ORDER BY день;" ;;
    revenue-by-client|26) sql "SELECT К.описание AS тип_клиента, COUNT(*) AS поездок, SUM(П.стоимость) AS выручка FROM КЛИЕНТЫ К JOIN ПОЕЗДКИ П ON К.код = П.клиент GROUP BY К.код, К.описание ORDER BY выручка DESC;" ;;
    distance-by-company|27) sql "SELECT Т.название AS таксопарк, ROUND(AVG(П.расстояние_км), 2) AS средний_пробег_км FROM ПОЕЗДКИ П JOIN ТАКСОПАРКИ Т ON П.таксопарк = Т.код GROUP BY Т.название ORDER BY средний_пробег_км DESC;" ;;
    hour-share|28) sql "SELECT EXTRACT(HOUR FROM дата) AS час, COUNT(*) AS поездок, ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS процент FROM ПОЕЗДКИ GROUP BY час ORDER BY час;" ;;
    check-by-hour|29) sql "SELECT EXTRACT(HOUR FROM дата) AS час, ROUND(AVG(стоимость), 2) AS средний_чек FROM ПОЕЗДКИ GROUP BY час ORDER BY час;" ;;
    top-tips|30) sql "SELECT 'Водитель №' || В.код AS водитель, COUNT(*) AS поездок, SUM(П.чаевые) AS чаевые FROM ПОЕЗДКИ П JOIN ВОДИТЕЛИ В ON П.водитель = В.код GROUP BY В.код ORDER BY чаевые DESC LIMIT 10;" ;;
    find-company|31) if [ -z "$2" ]; then echo "Укажите часть названия: ./help.sh find-company Cab"; else sql_file helper/15_demo_with_param.sql "$2"; fi ;;
    driver|32) if [ -z "$2" ]; then echo "Укажите код: ./help.sh driver 1"; else need_num "$2"; sql "SELECT В.код, В.taxi_id, COUNT(П.код_поездки) AS поездок, SUM(П.стоимость) AS выручка, MIN(П.дата)::date AS первая, MAX(П.дата)::date AS последняя FROM ВОДИТЕЛИ В LEFT JOIN ПОЕЗДКИ П ON П.водитель = В.код WHERE В.код = $2 GROUP BY В.код;"; fi ;;
    driver-rides|33) if [ -z "$2" ]; then echo "Укажите код: ./help.sh driver-rides 1"; else need_num "$2"; sql "SELECT * FROM v_rides_user WHERE водитель = 'Водитель №$2' ORDER BY дата DESC LIMIT 10;"; fi ;;
    rides-above|34) if [ -z "$2" ]; then echo "Укажите сумму: ./help.sh rides-above 100"; else need_num "$2"; sql "SELECT * FROM ПОЕЗДКИ WHERE стоимость > $2 ORDER BY стоимость DESC LIMIT 10;"; fi ;;
    drivers-above|35) if [ -z "$2" ]; then echo "Укажите сумму: ./help.sh drivers-above 10000"; else need_num "$2"; sql "SELECT 'Водитель №' || В.код AS водитель, SUM(П.стоимость) AS выручка FROM ВОДИТЕЛИ В JOIN ПОЕЗДКИ П ON В.код = П.водитель GROUP BY В.код HAVING SUM(П.стоимость) > $2 ORDER BY выручка DESC;"; fi ;;
    rename-company|40) if [ -z "$2" ] || [ -z "$3" ]; then echo "Использование: ./help.sh rename-company код название"; else need_num "$2"; sql "UPDATE ТАКСОПАРКИ SET название = '$(sql_str "$3")' WHERE код = $2; SELECT * FROM ТАКСОПАРКИ WHERE код = $2;"; fi ;;
    client-desc|41) if [ -z "$2" ] || [ -z "$3" ]; then echo "Использование: ./help.sh client-desc код описание"; else need_num "$2"; sql "UPDATE КЛИЕНТЫ SET описание = '$(sql_str "$3")' WHERE код = $2; SELECT * FROM КЛИЕНТЫ WHERE код = $2;"; fi ;;
    delete-driver|42) if [ -z "$2" ]; then echo "Использование: ./help.sh delete-driver код"; else need_num "$2"; sql "DELETE FROM ПОЕЗДКИ WHERE водитель = $2; DELETE FROM ВОДИТЕЛИ WHERE код = $2;" && echo "Водитель удалён"; fi ;;
    add-company|43) if [ -z "$2" ]; then echo "Использование: ./help.sh add-company название"; else sql "INSERT INTO ТАКСОПАРКИ (название) VALUES ('$(sql_str "$2")'); SELECT * FROM ТАКСОПАРКИ ORDER BY код DESC LIMIT 1;"; fi ;;
    add-driver|44) if [ -z "$2" ]; then echo "Использование: ./help.sh add-driver taxi_id"; else sql "INSERT INTO ВОДИТЕЛИ (taxi_id) VALUES ('$(sql_str "$2")'); SELECT * FROM ВОДИТЕЛИ ORDER BY код DESC LIMIT 1;"; fi ;;
    set-ride-company|45) if [ -z "$2" ] || [ -z "$3" ]; then echo "Использование: ./help.sh set-ride-company код_поездки код_таксопарка"; else need_num "$2"; need_num "$3"; sql "UPDATE ПОЕЗДКИ SET таксопарк = $3 WHERE код_поездки = $2; SELECT * FROM v_rides_user WHERE код_поездки = $2;"; fi ;;
    set-tips|46) if [ -z "$2" ] || [ -z "$3" ]; then echo "Использование: ./help.sh set-tips код_поездки сумма"; else need_num "$2"; need_num "$3"; sql "UPDATE ПОЕЗДКИ SET чаевые = $3 WHERE код_поездки = $2; SELECT * FROM v_rides_user WHERE код_поездки = $2;"; fi ;;
    update-before|60) psql -d "$DATABASE" -f helper/60_before_update.sql ;;
    update-do|61) psql -d "$DATABASE" -f helper/61_do_update.sql ;;
    update-after|62) psql -d "$DATABASE" -f helper/62_after_update.sql ;;
    delete-before|63) psql -d "$DATABASE" -f helper/63_before_delete.sql ;;
    delete-do|64) psql -d "$DATABASE" -f helper/64_do_delete.sql ;;
    delete-after|65) psql -d "$DATABASE" -f helper/65_after_delete.sql ;;
    view-user|100) psql -d "$DATABASE" -f queries/views/01_create_rides_view.sql ;;
    view-tech|101) psql -d "$DATABASE" -f queries/views/02_create_rides_tech.sql ;;
    view-check|102) psql -d "$DATABASE" -f queries/views/03_check_views.sql ;;
    sub-deviation|110) psql -d "$DATABASE" -f queries/subqueries/01_price_deviation.sql ;;
    sub-company-rating|111) psql -d "$DATABASE" -f queries/subqueries/02_company_rating.sql ;;
    sub-above-company-avg|112) psql -d "$DATABASE" -f queries/subqueries/03_rides_above_avg.sql ;;
    sub-company-stats|113) psql -d "$DATABASE" -f queries/subqueries/04_company_stats.sql ;;
    sub-top3|114) psql -d "$DATABASE" -f queries/subqueries/05_top_drivers_lateral.sql ;;
    sub-above-driver-avg|115) if [ -z "$2" ]; then echo "Использование: ./help.sh sub-above-driver-avg код_водителя"; echo "Пример: ./help.sh sub-above-driver-avg 1"; else need_num "$2"; sql_file queries/subqueries/06_rides_above_avg_param.sql "$2"; fi ;;
    sub-good-drivers|116) psql -d "$DATABASE" -f queries/subqueries/07_good_drivers_exists.sql ;;
    sub-best-drivers|117) psql -d "$DATABASE" -f queries/subqueries/08_best_drivers_all.sql ;;
    sub-expensive|118) sql "SELECT * FROM v_rides_user ORDER BY стоимость DESC LIMIT 10;" ;;
    sub-all|199)
        echo "============================================="
        echo "ПРЕДСТАВЛЕНИЯ И ПОДЗАПРОСЫ - ВСЕ ЗАДАЧИ"
        echo "============================================="
        psql -d "$DATABASE" -f queries/views/03_check_views.sql || exit 1
        psql -d "$DATABASE" -f queries/subqueries/01_price_deviation.sql || exit 1
        psql -d "$DATABASE" -f queries/subqueries/02_company_rating.sql || exit 1
        psql -d "$DATABASE" -f queries/subqueries/03_rides_above_avg.sql || exit 1
        psql -d "$DATABASE" -f queries/subqueries/04_company_stats.sql || exit 1
        psql -d "$DATABASE" -f queries/subqueries/05_top_drivers_lateral.sql || exit 1
        psql -d "$DATABASE" -v arg1=1 -f queries/subqueries/06_rides_above_avg_param.sql || exit 1
        psql -d "$DATABASE" -f queries/subqueries/07_good_drivers_exists.sql || exit 1
        psql -d "$DATABASE" -f queries/subqueries/08_best_drivers_all.sql || exit 1
        ;;
    func-create|200)
        echo "============================================="
        echo "СОЗДАНИЕ ФУНКЦИЙ"
        echo "============================================="
        psql -d "$DATABASE" -f queries/functions/01_create_functions_task1.sql || exit 1
        psql -d "$DATABASE" -f queries/functions/02_create_functions_task2.sql || exit 1
        psql -d "$DATABASE" -f queries/functions/03_create_functions_task3.sql || exit 1
        echo " Все функции созданы"
        ;;
    func-drivers-above|201)
        if [ -z "$2" ]; then
            echo "Использование: ./help.sh func-drivers-above <порог>"
            echo "Пример: ./help.sh func-drivers-above 10000"
            echo ""
            sql "SELECT * FROM drivers_above_revenue(10000) LIMIT 20;"
        else
            need_num "$2"
            sql "SELECT * FROM drivers_above_revenue($2) LIMIT 20;"
        fi
        ;;
    func-company-season|202)
        echo "============================================="
        echo "ВЫРУЧКА ПО ТАКСОПАРКАМ И СЕЗОНАМ"
        echo "============================================="
        sql "SELECT * FROM revenue_by_company_and_season();"
        ;;
    func-pivot|203)
        echo "============================================="
        echo "СВОДНАЯ ТАБЛИЦА (ВОДИТЕЛИ x СПОСОБЫ ОПЛАТЫ)"
        echo "============================================="
        sql "SELECT * FROM display_pivot_table();"
        ;;
    func-all|204)
        echo "============================================="
        echo "ФУНКЦИИ - ВСЕ ЗАДАЧИ"
        echo "============================================="
        ./help.sh func-create || exit 1
        echo ""
        echo "=== ЗАДАЧА 1 ==="
        ./help.sh func-drivers-above 10000 || exit 1
        echo ""
        echo "=== ЗАДАЧА 2 ==="
        ./help.sh func-company-season || exit 1
        echo ""
        echo "=== ЗАДАЧА 3 ==="
        ./help.sh func-pivot || exit 1
        ;;
    *) echo "ОШИБКА: Неизвестная команда $1" >&2; exit 1 ;;
esac
