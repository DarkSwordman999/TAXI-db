#!/bin/bash
DATABASE="taxi_lab5"

if [ -z "$1" ]; then
    echo "============================================="
    echo "  БАЗА ДАННЫХ TAXI"
    echo "============================================="
    echo ""
    echo "================== ЛАБА 5 ОСНОВНЫЕ ЗАДАЧИ =================="
    echo "  ./h task1 - выручка по сезонам"
    echo "  ./h task2 - выручка по сезонам и классам авто"
    echo "  ./h task3 - выручка по дням недели и водителям"
    echo "  ./h task4 день - выручка по водителям за день"
    echo ""
    echo "================== ЛАБА 5 ПРОСМОТР ДАННЫХ =================="
    echo "  ./h 01 - все автомобили"
    echo "  ./h 02 - все водители"
    echo "  ./h 03 - все клиенты первые 10"
    echo "  ./h 04 - количество поездок"
    echo "  ./h 05 - примеры поездок"
    echo "  ./h 06 - все клиенты полный список"
    echo "  ./h 16 - структура таблиц"
    echo ""
    echo "================== ЛАБА 5 ДЕМОНСТРАЦИЯ JOIN =================="
    echo "  ./h 07 - INNER JOIN"
    echo "  ./h 08 - LEFT JOIN"
    echo "  ./h 09 - RIGHT JOIN"
    echo "  ./h 10 - FULL JOIN"
    echo "  ./h 11 - CROSS JOIN"
    echo "  ./h 12 - SELF JOIN"
    echo ""
    echo "================== ЛАБА 5 ПОКАЗАТЬ ДО/ПОСЛЕ =================="
    echo "  ./h 60 - ДО UPDATE"
    echo "  ./h 61 - ПОСЛЕ UPDATE"
    echo "  ./h 62 - ДО DELETE"
    echo "  ./h 63 - ПОСЛЕ DELETE"
    echo ""
    echo "================== ЛАБА 5 АНАЛИТИКА =================="
    echo "  ./h 17 - топ-10 авто по выручке"
    echo "  ./h 18 - топ-10 водителей по выручке"
    echo "  ./h 19 - выручка по месяцам"
    echo "  ./h 20 - средний чек"
    echo "  ./h 21 - поездки по часам"
    echo "  ./h 22 - статистика по классам"
    echo "  ./h 23 - загруженность водителей"
    echo "  ./h 24 - средняя стоимость по классам"
    echo "  ./h 25 - выручка по дням недели"
    echo "  ./h 26 - топ-5 клиентов"
    echo "  ./h 27 - средний пробег по классам"
    echo "  ./h 28 - распределение поездок по часам"
    echo "  ./h 29 - средний чек по часам"
    echo "  ./h 30 - выручка по водителям с рейтингом"
    echo ""
    echo "================== ЛАБА 5 ЗАПРОСЫ С ПАРАМЕТРАМИ =================="
    echo "  ./h 31 класс - авто по классу"
    echo "  ./h 32 код - информация о водителе"
    echo "  ./h 33 код - история поездок авто"
    echo "  ./h 34 сумма - поездки дороже суммы"
    echo "  ./h 35 сумма - водители с выручкой выше суммы"
    echo "  ./h 40 код номер - обновить госномер авто"
    echo "  ./h 41 код телефон - обновить телефон водителя"
    echo "  ./h 42 код - удалить водителя"
    echo "  ./h 43 марка модель класс - добавить авто"
    echo "  ./h 44 фамилия имя телефон - добавить водителя"
    echo "  ./h 45 код класс - изменить класс авто"
    echo "  ./h 46 код рейтинг - изменить рейтинг водителя"
    echo ""
    echo "================== ЛАБА 6 ПРЕДСТАВЛЕНИЯ =================="
    echo "  ./h 100 - создать пользовательское представление"
    echo "  ./h 101 - создать технологическое представление"
    echo "  ./h 102 - проверить представления"
    echo ""
    echo "================== ЛАБА 6 ПОДЗАПРОСЫ =================="
    echo "  ./h 110 - задача 1.1 отклонение стоимости поездки"
    echo "  ./h 111 - задача 1.2 рейтинг автомобилей"
    echo "  ./h 112 - задача 2.1 поездки дороже среднего по классу"
    echo "  ./h 113 - задача 2.2 статистика по классам"
    echo "  ./h 114 - задача 3.1 топ-3 водителя в каждом классе"
    echo "  ./h 115 фамилия - задача 4.1 поездки дороже среднего по водителю"
    echo "  ./h 116 - задача 4.2 водители без дешёвых поездок"
    echo "  ./h 117 - задача 4.3 лучшие водители"
    echo "  ./h 118 - добавить дорогие поездки (для теста 4.3)"
    echo "  ./h 199 - выполнить все задачи лабораторной 6"
    echo ""
    echo "================== ЛАБА 7 ФУНКЦИИ =================="
    echo "  ./h 200 - создать все функции"
    echo "  ./h 201 порог - водители с выручкой выше порога"
    echo "  ./h 202 - выручка по классам и сезонам"
    echo "  ./h 203 - сводная таблица (водители x классы)"
    echo "  ./h 204 - выполнить всё"
    echo ""
    echo "================== ЗАПУСК SQL ФАЙЛОВ =================="
    echo "  ./h файл.sql [параметр] - выполнить SQL-файл"
    echo "  ./h h1 файл.sql [параметр] - выполнить SQL-файл через h1"
    exit 1
fi

if [[ "$1" == *.sql ]]; then
    if [ -f "$1" ]; then
        if [ -z "$2" ]; then
            psql -d "$DATABASE" -f "$1"
        else
            psql -d "$DATABASE" -f "$1" -v arg1="$2"
        fi
    else
        echo "ОШИБКА: Файл $1 не найден"
        exit 1
    fi
    exit 0
fi

if [ "$1" = "h1" ]; then
    shift
    ./h1 "$@"
    exit 0
fi

case "$1" in
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
            psql -d "$DATABASE" -v arg1="$2" -f queries/tasks/04_revenue_by_driver_for_day.sql
        fi
        ;;
    01) psql -d "$DATABASE" -c "SELECT * FROM АВТОМОБИЛИ ORDER BY код;" ;;
    02) psql -d "$DATABASE" -c "SELECT код, фамилия, имя, телефон, стаж_лет, рейтинг FROM ВОДИТЕЛИ ORDER BY код;" ;;
    03) psql -d "$DATABASE" -c "SELECT код, фамилия, имя, телефон FROM КЛИЕНТЫ ORDER BY код LIMIT 10;" ;;
    04) psql -d "$DATABASE" -c "SELECT COUNT(*) FROM ПОЕЗДКИ;" ;;
    05) psql -d "$DATABASE" -c "SELECT код_поездки, стоимость, дата FROM ПОЕЗДКИ ORDER BY дата DESC LIMIT 10;" ;;
    06) psql -d "$DATABASE" -c "SELECT код, фамилия, имя, телефон FROM КЛИЕНТЫ ORDER BY код;" ;;
    07) psql -d "$DATABASE" -c "SELECT П.код_поездки, А.марка, А.модель, В.фамилия, П.стоимость FROM ПОЕЗДКИ П INNER JOIN АВТОМОБИЛИ А ON П.автомобиль = А.код INNER JOIN ВОДИТЕЛИ В ON П.водитель = В.код LIMIT 10;" ;;
    08) psql -d "$DATABASE" -c "SELECT А.марка, А.модель, COUNT(П.код_поездки) as поездок FROM АВТОМОБИЛИ А LEFT JOIN ПОЕЗДКИ П ON А.код = П.автомобиль GROUP BY А.марка, А.модель ORDER BY поездок DESC LIMIT 10;" ;;
    09) psql -d "$DATABASE" -c "SELECT К.фамилия, COUNT(П.код_поездки) as поездок FROM ПОЕЗДКИ П RIGHT JOIN КЛИЕНТЫ К ON П.клиент = К.код GROUP BY К.фамилия ORDER BY поездок DESC LIMIT 10;" ;;
    10) psql -d "$DATABASE" -c "SELECT А.марка, К.фамилия FROM АВТОМОБИЛИ А FULL JOIN КЛИЕНТЫ К ON А.код = К.код LIMIT 10;" ;;
    11) psql -d "$DATABASE" -c "SELECT А.марка, В.фамилия FROM АВТОМОБИЛИ А CROSS JOIN ВОДИТЕЛИ В LIMIT 10;" ;;
    12) psql -d "$DATABASE" -c "SELECT В1.фамилия, В1.стаж_лет, В2.фамилия, В2.стаж_лет FROM ВОДИТЕЛИ В1, ВОДИТЕЛИ В2 WHERE В1.стаж_лет > В2.стаж_лет AND В1.код != В2.код LIMIT 10;" ;;
    16) psql -d "$DATABASE" -c "\d" ;;
    17) psql -d "$DATABASE" -c "SELECT А.марка, А.модель, SUM(П.стоимость) as выручка FROM ПОЕЗДКИ П JOIN АВТОМОБИЛИ А ON П.автомобиль = А.код GROUP BY А.марка, А.модель ORDER BY выручка DESC LIMIT 10;" ;;
    18) psql -d "$DATABASE" -c "SELECT В.фамилия, В.имя, SUM(П.стоимость) as выручка FROM ПОЕЗДКИ П JOIN ВОДИТЕЛИ В ON П.водитель = В.код GROUP BY В.фамилия, В.имя ORDER BY выручка DESC LIMIT 10;" ;;
    19) psql -d "$DATABASE" -c "SELECT EXTRACT(MONTH FROM дата) as месяц, SUM(стоимость) as выручка FROM ПОЕЗДКИ GROUP BY месяц ORDER BY месяц;" ;;
    20) psql -d "$DATABASE" -c "SELECT AVG(стоимость) as средний, MIN(стоимость) as мин, MAX(стоимость) as макс FROM ПОЕЗДКИ;" ;;
    21) psql -d "$DATABASE" -c "SELECT EXTRACT(HOUR FROM дата) as час, COUNT(*) as поездок, SUM(стоимость) as выручка FROM ПОЕЗДКИ GROUP BY час ORDER BY час;" ;;
    22) psql -d "$DATABASE" -c "SELECT А.класс, COUNT(*) as поездок, AVG(П.стоимость) as сред_чек FROM ПОЕЗДКИ П JOIN АВТОМОБИЛИ А ON П.автомобиль = А.код GROUP BY А.класс;" ;;
    23) psql -d "$DATABASE" -c "SELECT В.фамилия, COUNT(П.код_поездки) as поездок FROM ВОДИТЕЛИ В JOIN ПОЕЗДКИ П ON В.код = П.водитель GROUP BY В.фамилия ORDER BY поездок DESC LIMIT 10;" ;;
    24) psql -d "$DATABASE" -c "SELECT класс, AVG(цена_за_км) as цена_км FROM ТАРИФЫ GROUP BY класс;" ;;
    25) psql -d "$DATABASE" -c "SELECT EXTRACT(DOW FROM дата) as день, SUM(стоимость) as выручка FROM ПОЕЗДКИ GROUP BY день ORDER BY день;" ;;
    26) psql -d "$DATABASE" -c "SELECT К.фамилия, SUM(П.стоимость) as сумма FROM КЛИЕНТЫ К JOIN ПОЕЗДКИ П ON К.код = П.клиент GROUP BY К.фамилия ORDER BY сумма DESC LIMIT 5;" ;;
    27) psql -d "$DATABASE" -c "SELECT А.класс, AVG(П.расстояние_км) as пробег FROM ПОЕЗДКИ П JOIN АВТОМОБИЛИ А ON П.автомобиль = А.код GROUP BY А.класс;" ;;
    28) psql -d "$DATABASE" -c "SELECT EXTRACT(HOUR FROM дата) as час, COUNT(*) as поездок, ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as процент FROM ПОЕЗДКИ GROUP BY час ORDER BY час;" ;;
    29) psql -d "$DATABASE" -c "SELECT EXTRACT(HOUR FROM дата) as час, AVG(стоимость) as средний_чек FROM ПОЕЗДКИ GROUP BY час ORDER BY час;" ;;
    30) psql -d "$DATABASE" -c "SELECT В.фамилия, В.рейтинг, SUM(П.стоимость) as выручка FROM ПОЕЗДКИ П JOIN ВОДИТЕЛИ В ON П.водитель = В.код GROUP BY В.фамилия, В.рейтинг ORDER BY выручка DESC LIMIT 10;" ;;
    31) if [ -z "$2" ]; then echo "Укажите класс: ./h 31 бизнес"; else psql -d "$DATABASE" -c "SELECT * FROM АВТОМОБИЛИ WHERE класс = '$2';"; fi ;;
    32) if [ -z "$2" ]; then echo "Укажите код: ./h 32 1"; else psql -d "$DATABASE" -c "SELECT * FROM ВОДИТЕЛИ WHERE код = $2;"; fi ;;
    33) if [ -z "$2" ]; then echo "Укажите код: ./h 33 1"; else psql -d "$DATABASE" -c "SELECT * FROM ПОЕЗДКИ WHERE автомобиль = $2 ORDER BY дата DESC LIMIT 10;"; fi ;;
    34) if [ -z "$2" ]; then echo "Укажите сумму: ./h 34 500"; else psql -d "$DATABASE" -c "SELECT * FROM ПОЕЗДКИ WHERE стоимость > $2 ORDER BY стоимость DESC LIMIT 10;"; fi ;;
    35) if [ -z "$2" ]; then echo "Укажите сумму: ./h 35 10000"; else psql -d "$DATABASE" -c "SELECT В.фамилия, SUM(П.стоимость) as выручка FROM ВОДИТЕЛИ В JOIN ПОЕЗДКИ П ON В.код = П.водитель GROUP BY В.фамилия HAVING SUM(П.стоимость) > $2 ORDER BY выручка DESC;"; fi ;;
    40) if [ -z "$2" ] || [ -z "$3" ]; then echo "Использование: ./h 40 код номер"; else psql -d "$DATABASE" -c "UPDATE АВТОМОБИЛИ SET гос_номер = '$3' WHERE код = $2; SELECT * FROM АВТОМОБИЛИ WHERE код = $2;"; fi ;;
    41) if [ -z "$2" ] || [ -z "$3" ]; then echo "Использование: ./h 41 код телефон"; else psql -d "$DATABASE" -c "UPDATE ВОДИТЕЛИ SET телефон = '$3' WHERE код = $2; SELECT * FROM ВОДИТЕЛИ WHERE код = $2;"; fi ;;
    42) if [ -z "$2" ]; then echo "Использование: ./h 42 код"; else psql -d "$DATABASE" -c "DELETE FROM ПОЕЗДКИ WHERE водитель = $2; DELETE FROM ВОДИТЕЛИ WHERE код = $2;"; echo "Водитель удалён"; fi ;;
    43) if [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ]; then echo "Использование: ./h 43 марка модель класс"; else psql -d "$DATABASE" -c "INSERT INTO АВТОМОБИЛИ (марка, модель, класс) VALUES ('$2', '$3', '$4'); SELECT * FROM АВТОМОБИЛИ ORDER BY код DESC LIMIT 1;"; fi ;;
    44) if [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ]; then echo "Использование: ./h 44 фамилия имя телефон"; else NEXT_CODE=$(psql -d "$DATABASE" -t -c "SELECT COALESCE(MAX(код), 0) + 1 FROM ВОДИТЕЛИ;" | tr -d ' '); psql -d "$DATABASE" -c "INSERT INTO ВОДИТЕЛИ (код, фамилия, имя, телефон) VALUES ($NEXT_CODE, '$2', '$3', '$4'); SELECT * FROM ВОДИТЕЛИ WHERE код = $NEXT_CODE;"; fi ;;
    45) if [ -z "$2" ] || [ -z "$3" ]; then echo "Использование: ./h 45 код класс"; else psql -d "$DATABASE" -c "UPDATE АВТОМОБИЛИ SET класс = '$3' WHERE код = $2; SELECT * FROM АВТОМОБИЛИ WHERE код = $2;"; fi ;;
    46) if [ -z "$2" ] || [ -z "$3" ]; then echo "Использование: ./h 46 код рейтинг"; else psql -d "$DATABASE" -c "UPDATE ВОДИТЕЛИ SET рейтинг = $3 WHERE код = $2; SELECT * FROM ВОДИТЕЛИ WHERE код = $2;"; fi ;;
    60) psql -d "$DATABASE" -f helper/60_before_update.sql ;;
    61) psql -d "$DATABASE" -f helper/61_do_update.sql ;;
    62) psql -d "$DATABASE" -f helper/63_before_delete.sql ;;
    63) psql -d "$DATABASE" -f helper/65_after_delete.sql ;;
    100) psql -d "$DATABASE" -f queries/views/01_create_rides_view.sql ;;
    101) psql -d "$DATABASE" -f queries/views/02_create_rides_tech.sql ;;
    102) psql -d "$DATABASE" -f queries/views/03_check_views.sql ;;
    110) psql -d "$DATABASE" -f queries/subqueries/01_price_deviation.sql ;;
    111) psql -d "$DATABASE" -f queries/subqueries/02_car_rating.sql ;;
    112) psql -d "$DATABASE" -f queries/subqueries/03_rides_above_avg.sql ;;
    113) psql -d "$DATABASE" -f queries/subqueries/04_class_stats.sql ;;
    114) psql -d "$DATABASE" -f queries/subqueries/05_top_drivers_lateral.sql ;;
    115) if [ -z "$2" ]; then echo "Использование: ./h 115 фамилия"; echo "Пример: ./h 115 Иванов"; else psql -d "$DATABASE" -v arg1="$2" -f queries/subqueries/06_rides_above_avg_param.sql; fi ;;
    116) psql -d "$DATABASE" -f queries/subqueries/07_good_drivers_exists.sql ;;
    117) psql -d "$DATABASE" -f queries/subqueries/08_best_drivers_all.sql ;;
    118) echo "=== ДОБАВЛЕНИЕ ДОРОГИХ ПОЕЗДОК ==="; psql -d "$DATABASE" -f control/inserts/add_expensive_rides.sql ;;
    199)
        echo "============================================="
        echo "ЛАБОРАТОРНАЯ РАБОТА 6 - ВСЕ ЗАДАЧИ"
        echo "============================================="
        psql -d "$DATABASE" -f queries/views/03_check_views.sql
        psql -d "$DATABASE" -f queries/subqueries/01_price_deviation.sql
        psql -d "$DATABASE" -f queries/subqueries/02_car_rating.sql
        psql -d "$DATABASE" -f queries/subqueries/03_rides_above_avg.sql
        psql -d "$DATABASE" -f queries/subqueries/04_class_stats.sql
        psql -d "$DATABASE" -f queries/subqueries/05_top_drivers_lateral.sql
        psql -d "$DATABASE" -v arg1='Иванов' -f queries/subqueries/06_rides_above_avg_param.sql
        psql -d "$DATABASE" -f queries/subqueries/07_good_drivers_exists.sql
        psql -d "$DATABASE" -f queries/subqueries/08_best_drivers_all.sql
        ;;
    200)
        echo "============================================="
        echo "ЛАБА 7 - СОЗДАНИЕ ФУНКЦИЙ"
        echo "============================================="
        psql -d "$DATABASE" -f queries/lab7/01_create_functions_task1.sql
        psql -d "$DATABASE" -f queries/lab7/02_create_functions_task2.sql
        psql -d "$DATABASE" -f queries/lab7/03_create_functions_task3_fixed.sql
        echo " Все функции созданы"
        ;;
    201)
        if [ -z "$2" ]; then
            echo "Использование: ./h 201 <порог>"
            echo "Пример: ./h 201 10000"
            echo ""
            psql -d "$DATABASE" -c "SELECT * FROM drivers_above_revenue(10000);"
        else
            psql -d "$DATABASE" -c "SELECT * FROM drivers_above_revenue($2);"
        fi
        ;;
    202)
        echo "============================================="
        echo "ВЫРУЧКА ПО КЛАССАМ И СЕЗОНАМ"
        echo "============================================="
        psql -d "$DATABASE" -c "SELECT * FROM revenue_by_class_and_season();"
        ;;
    203)
        echo "============================================="
        echo "СВОДНАЯ ТАБЛИЦА (ВОДИТЕЛИ x КЛАССЫ)"
        echo "============================================="
        psql -d "$DATABASE" -c "SELECT * FROM display_pivot_table();"
        ;;
    204)
        echo "============================================="
        echo "ЛАБА 7 - ВСЕ ЗАДАЧИ"
        echo "============================================="
        ./h 200
        echo ""
        echo "=== ЗАДАЧА 1 ==="
        ./h 201 10000
        echo ""
        echo "=== ЗАДАЧА 2 ==="
        ./h 202
        echo ""
        echo "=== ЗАДАЧА 3 ==="
        ./h 203
        ;;
    *) echo "ОШИБКА: Неизвестная команда $1" ;;
esac
