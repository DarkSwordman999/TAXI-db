#!/bin/bash
# ============================================
# ГЛАВНЫЙ СКРИПТ ДЛЯ ЗАПУСКА SQL-ЗАПРОСОВ TAXI
# ============================================

DATABASE="taxi_lab5"

if [ -z "$1" ]; then
    echo "Использование: ./s task1|task2|task3|task4 <день>"
    echo ""
    echo "Доступные задачи:"
    echo "  ./s task1                    - выручка по сезонам"
    echo "  ./s task2                    - выручка по сезонам и классам авто"
    echo "  ./s task3                    - выручка по дням недели и водителям"
    echo "  ./s task4 <день_недели>      - выручка по водителям за день"
    echo "Пример: ./s task4 1"
    exit 1
fi

case "$1" in
    task1)
        psql -d $DATABASE -f queries/tasks/01_revenue_by_season.sql
        ;;
    task2)
        psql -d $DATABASE -f queries/tasks/02_revenue_by_season_and_class.sql
        ;;
    task3)
        psql -d $DATABASE -f queries/tasks/03_revenue_by_day_and_driver.sql
        ;;
    task4)
        if [ -z "$2" ]; then
            echo "Укажите день недели (1-7): ./s task4 1"
        else
            psql -d $DATABASE -v arg1="$2" -f queries/tasks/04_revenue_by_driver_for_day.sql
        fi
        ;;
    *)
        echo "Неизвестная задача: $1"
        ;;
esac
