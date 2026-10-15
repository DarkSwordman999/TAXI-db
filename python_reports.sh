#!/bin/bash
cd "$(dirname "$0")" || exit 1

show_help() {
    echo "============================================="
    echo "  PYTHON-ОТЧЁТЫ - TAXI"
    echo "============================================="
    echo ""
    echo "ОПИСАНИЕ КОМАНД:"
    echo "  ./python_reports.sh 1 [водитель] [класс]         - отчёт по водителям и классам"
    echo "  ./python_reports.sh 1s [водитель] [класс]        - отчёт со звездочкой * в углу"
    echo "  ./python_reports.sh 2 [класс]                    - сводная таблица"
    echo "  ./python_reports.sh 3                            - график динамики"
    echo "  ./python_reports.sh 4 [водитель]                 - круговая диаграмма"
    echo "  ./python_reports.sh all                          - выполнить всё"
    echo "  ./python_reports.sh save                         - сохранить все графики"
    echo "  ./python_reports.sh save --force                 - сохранить с перезаписью"
    echo ""
    echo "ПРИМЕРЫ:"
    echo "  ./python_reports.sh 1"
    echo "  ./python_reports.sh 1s"
    echo "  ./python_reports.sh 1 Волков"
    echo "  ./python_reports.sh 1s Волков"
    echo "  ./python_reports.sh 2"
    echo "  ./python_reports.sh 3"
    echo "  ./python_reports.sh 4 Волков"
}

case "$1" in
    1)
        if [ -z "$2" ]; then
            python3 taxi_report.py task1
        elif [ -z "$3" ]; then
            python3 taxi_report.py task1 "$2"
        else
            python3 taxi_report.py task1 "$2" "$3"
        fi
        ;;
    1s)
        if [ -z "$2" ]; then
            echo " ✸ Отчёт со звездочкой *"
            python3 taxi_report.py task1s
        elif [ -z "$3" ]; then
            echo " ✸ Отчёт со звездочкой * (водитель: $2)"
            python3 taxi_report.py task1s "$2"
        else
            echo " ✸ Отчёт со звездочкой * (водитель: $2, класс: $3)"
            python3 taxi_report.py task1s "$2" "$3"
        fi
        ;;
    2)
        if [ -z "$2" ]; then
            python3 taxi_report.py task2
        else
            python3 taxi_report.py task2 "$2"
        fi
        ;;
    3)
        python3 taxi_report.py task3
        ;;
    4)
        if [ -z "$2" ]; then
            python3 taxi_report.py task4
        else
            python3 taxi_report.py task4 "$2"
        fi
        ;;
    save)
        if [ "$2" = "--force" ]; then
            python3 taxi_report.py save-all --force
        else
            python3 taxi_report.py save-all
        fi
        ;;
    all)
        echo "============================================="
        echo "  ВЫПОЛНЕНИЕ ВСЕХ ЗАДАЧ"
        echo "============================================="
        echo ""
        echo "--- ЗАДАЧА 1: ОТЧЁТ ---"
        python3 taxi_report.py task1
        echo ""
        echo "--- ЗАДАЧА 1s: ОТЧЁТ СО ЗВЕЗДОЧКОЙ * ---"
        python3 taxi_report.py task1s
        echo ""
        echo "--- ЗАДАЧА 2: СВОДНАЯ ТАБЛИЦА ---"
        python3 taxi_report.py task2
        echo ""
        echo "--- ЗАДАЧА 3: ГРАФИК ---"
        python3 taxi_report.py task3
        echo ""
        echo "--- ЗАДАЧА 4: ДИАГРАММА ---"
        python3 taxi_report.py task4
        ;;
    *)
        show_help
        ;;
esac
