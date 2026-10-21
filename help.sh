#!/bin/bash
cd "$(dirname "$0")" || exit 1
# настройки подключения: переменные PG* из окружения или из .env в корне проекта
[ -f .env ] && set -a && . .env && set +a
DATABASE="${PGDATABASE:-taxi}"
# Windows: psql выводит свои русские надписи («(1 строка)») в кодировке ANSI,
# в консоли UTF-8 они нечитаемы — там они на английском, данные остаются русскими
case "$OSTYPE" in msys*|cygwin*) export LC_MESSAGES=C ;; esac
# SQL-файлы проекта в UTF-8. Без этой строки psql в Windows иногда берет кодировку
# консоли (WIN1251), например при выводе в /dev/null, и ломает кириллицу в запросах
export PGCLIENTENCODING="${PGCLIENTENCODING:-UTF8}"
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

# SQL-файл с необязательными параметрами: в файле они видны как :arg1, :arg2…
# (строкой — :'arg1', psql сам экранирует кавычки). Параметры задаются командой \set
# через stdin, а не psql -v: в Windows аргументы командной строки доходят до psql
# в кодировке ANSI, и кириллица в них ломается
sql_file() {
    if [ -z "$2" ]; then
        psql -d "$DATABASE" -f "$1"
        return
    fi
    local file="$1" n=1 value
    shift
    {
        for value in "$@"; do
            # в \set внутри '...' обратная косая черта — спецсимвол, кавычка удваивается
            value="${value//\\/\\\\}"
            value="${value//\'/\'\'}"
            printf '\\set arg%d '"'"'%s'"'"'\n' "$n" "$value"
            n=$((n + 1))
        done
        cat "$file"
    } | psql -d "$DATABASE"
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
    echo "  ./help.sh rename-demo код [название]              переименовать таксопарк и откатить (база не меняется)"
    echo "  ./help.sh delete-demo код                         удалить водителя и откатить (база не меняется)"
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
    echo "  ./help.sh find-area текст                         районы по части названия"
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
    echo "  ./help.sh файл.sql [параметры]                    выполнить SQL-файл (параметры в нём — :arg1, :arg2...)"
    echo "  ./help.sh h1 файл.sql [параметр]                  выполнить SQL-файл через run_sql.sh"
    exit 1
fi

if [[ "$1" == *.sql ]]; then
    if [ -f "$1" ]; then
        sql_file "$@"
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
    companies|01) psql -d "$DATABASE" -f helper/companies.sql ;;
    drivers|02) psql -d "$DATABASE" -f helper/drivers.sql ;;
    clients|03) psql -d "$DATABASE" -f helper/clients.sql ;;
    count|04) psql -d "$DATABASE" -f helper/count.sql ;;
    latest|05) psql -d "$DATABASE" -f helper/latest.sql ;;
    clients-rides|06) psql -d "$DATABASE" -f helper/clients-rides.sql ;;
    join-inner|07) psql -d "$DATABASE" -f helper/join-inner.sql ;;
    join-left|08) psql -d "$DATABASE" -f helper/join-left.sql ;;
    join-right|09) psql -d "$DATABASE" -f helper/join-right.sql ;;
    join-full|10) psql -d "$DATABASE" -f helper/join-full.sql ;;
    join-cross|11) psql -d "$DATABASE" -f helper/join-cross.sql ;;
    join-self|12) psql -d "$DATABASE" -f helper/join-self.sql ;;
    tables|16) psql -d "$DATABASE" -f helper/tables.sql ;;
    columns) psql -d "$DATABASE" -f helper/columns.sql ;;
    top-areas|17) psql -d "$DATABASE" -f helper/top-areas.sql ;;
    top-drivers|18) psql -d "$DATABASE" -f helper/top-drivers.sql ;;
    by-month|19) psql -d "$DATABASE" -f helper/by-month.sql ;;
    avg-check|20) psql -d "$DATABASE" -f helper/avg-check.sql ;;
    by-hour|21) psql -d "$DATABASE" -f helper/by-hour.sql ;;
    company-stats|22) psql -d "$DATABASE" -f helper/company-stats.sql ;;
    driver-load|23) psql -d "$DATABASE" -f helper/driver-load.sql ;;
    tips-by-client|24) psql -d "$DATABASE" -f helper/tips-by-client.sql ;;
    by-weekday|25) psql -d "$DATABASE" -f helper/by-weekday.sql ;;
    revenue-by-client|26) psql -d "$DATABASE" -f helper/revenue-by-client.sql ;;
    distance-by-company|27) psql -d "$DATABASE" -f helper/distance-by-company.sql ;;
    hour-share|28) psql -d "$DATABASE" -f helper/hour-share.sql ;;
    check-by-hour|29) psql -d "$DATABASE" -f helper/check-by-hour.sql ;;
    top-tips|30) psql -d "$DATABASE" -f helper/top-tips.sql ;;
    find-company|31) if [ -z "$2" ]; then echo "Укажите часть названия: ./help.sh find-company Cab"; else sql_file helper/find-company.sql "$2"; fi ;;
    find-area) if [ -z "$2" ]; then echo "Укажите часть названия: ./help.sh find-area Park"; else sql_file helper/find-area.sql "$2"; fi ;;
    driver|32) if [ -z "$2" ]; then echo "Укажите код: ./help.sh driver 1"; else need_num "$2"; sql_file helper/driver.sql "$2"; fi ;;
    driver-rides|33) if [ -z "$2" ]; then echo "Укажите код: ./help.sh driver-rides 1"; else need_num "$2"; sql_file helper/driver-rides.sql "$2"; fi ;;
    rides-above|34) if [ -z "$2" ]; then echo "Укажите сумму: ./help.sh rides-above 100"; else need_num "$2"; sql_file helper/rides-above.sql "$2"; fi ;;
    drivers-above|35) if [ -z "$2" ]; then echo "Укажите сумму: ./help.sh drivers-above 10000"; else need_num "$2"; sql_file helper/drivers-above.sql "$2"; fi ;;
    rename-company|40) if [ -z "$2" ] || [ -z "$3" ]; then echo "Использование: ./help.sh rename-company код название"; else need_num "$2"; sql_file helper/rename-company.sql "$2" "$3"; fi ;;
    client-desc|41) if [ -z "$2" ] || [ -z "$3" ]; then echo "Использование: ./help.sh client-desc код описание"; else need_num "$2"; sql_file helper/client-desc.sql "$2" "$3"; fi ;;
    delete-driver|42) if [ -z "$2" ]; then echo "Использование: ./help.sh delete-driver код"; else need_num "$2"; sql_file helper/delete-driver.sql "$2" && echo "Водитель удалён"; fi ;;
    add-company|43) if [ -z "$2" ]; then echo "Использование: ./help.sh add-company название"; else sql_file helper/add-company.sql "$2"; fi ;;
    add-driver|44) if [ -z "$2" ]; then echo "Использование: ./help.sh add-driver taxi_id"; else sql_file helper/add-driver.sql "$2"; fi ;;
    set-ride-company|45) if [ -z "$2" ] || [ -z "$3" ]; then echo "Использование: ./help.sh set-ride-company код_поездки код_таксопарка"; else need_num "$2"; need_num "$3"; sql_file helper/set-ride-company.sql "$2" "$3"; fi ;;
    set-tips|46) if [ -z "$2" ] || [ -z "$3" ]; then echo "Использование: ./help.sh set-tips код_поездки сумма"; else need_num "$2"; need_num "$3"; sql_file helper/set-tips.sql "$2" "$3"; fi ;;
    update-before|60) psql -d "$DATABASE" -f helper/update-before.sql ;;
    update-do|61) psql -d "$DATABASE" -f helper/update-do.sql ;;
    update-after|62) psql -d "$DATABASE" -f helper/update-after.sql ;;
    delete-before|63) psql -d "$DATABASE" -f helper/delete-before.sql ;;
    delete-do|64) psql -d "$DATABASE" -f helper/delete-do.sql ;;
    delete-after|65) psql -d "$DATABASE" -f helper/delete-after.sql ;;
    rename-demo) if [ -z "$2" ]; then echo "Использование: ./help.sh rename-demo код [название]"; else need_num "$2"; sql_file helper/rename-demo.sql "$2" ${3:+"$3"}; fi ;;
    delete-demo) if [ -z "$2" ]; then echo "Использование: ./help.sh delete-demo код"; else need_num "$2"; sql_file helper/delete-demo.sql "$2"; fi ;;
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
    sub-expensive|118) psql -d "$DATABASE" -f helper/sub-expensive.sql ;;
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
            psql -d "$DATABASE" -f helper/func-drivers-above.sql
        else
            need_num "$2"
            sql_file helper/func-drivers-above.sql "$2"
        fi
        ;;
    func-company-season|202)
        echo "============================================="
        echo "ВЫРУЧКА ПО ТАКСОПАРКАМ И СЕЗОНАМ"
        echo "============================================="
        psql -d "$DATABASE" -f helper/func-company-season.sql
        ;;
    func-pivot|203)
        echo "============================================="
        echo "СВОДНАЯ ТАБЛИЦА (ВОДИТЕЛИ x СПОСОБЫ ОПЛАТЫ)"
        echo "============================================="
        psql -d "$DATABASE" -f helper/func-pivot.sql
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
