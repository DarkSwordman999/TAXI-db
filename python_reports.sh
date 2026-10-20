#!/bin/bash
cd "$(dirname "$0")" || exit 1
PYTHON=python3
# в Windows python3 бывает заглушкой Microsoft Store, которая не запускается
"$PYTHON" -c "" 2>/dev/null || PYTHON=python

show_help() {
    echo "============================================="
    echo "  PYTHON-ОТЧЁТЫ - TAXI"
    echo "============================================="
    echo ""
    echo "ОПИСАНИЕ КОМАНД:"
    echo "  ./python_reports.sh 1 [код_водителя] [тип_клиента]         - отчёт по водителям и типам клиентов"
    echo "  ./python_reports.sh 1s [код_водителя] [тип_клиента]        - отчёт со звездочкой * в углу"
    echo "  ./python_reports.sh 2 [тип_клиента]                 - сводная таблица"
    echo "  ./python_reports.sh 3 [--force]                  - график динамики"
    echo "  ./python_reports.sh 4 [код_водителя] [--force]    - круговая диаграмма"
    echo "  ./python_reports.sh months [--force]             - выручка и цена километра по месяцам (вместо 3)"
    echo "  ./python_reports.sh payments [код_водителя] [--force] - доли выручки по способам оплаты (вместо 4)"
    echo "  ./python_reports.sh all                          - выполнить всё"
    echo "  ./python_reports.sh save                         - сохранить все графики"
    echo "  ./python_reports.sh save --force                 - сохранить с перезаписью"
    echo ""
    echo "ПРИМЕРЫ:"
    echo "  ./python_reports.sh 1"
    echo "  ./python_reports.sh 1s"
    echo "  ./python_reports.sh 1 1"
    echo "  ./python_reports.sh 1s 1"
    echo "  ./python_reports.sh 2"
    echo "  ./python_reports.sh 3"
    echo "  ./python_reports.sh 4 1"
    echo "  ./python_reports.sh months"
    echo "  ./python_reports.sh payments 1"
}

case "$1" in
    1)
        if [ -z "$2" ]; then
            "$PYTHON" taxi_report.py task1
        elif [ -z "$3" ]; then
            "$PYTHON" taxi_report.py task1 "$2"
        else
            "$PYTHON" taxi_report.py task1 "$2" "$3"
        fi
        ;;
    1s)
        if [ -z "$2" ]; then
            echo " ✸ Отчёт со звездочкой *"
            "$PYTHON" taxi_report.py task1s
        elif [ -z "$3" ]; then
            echo " ✸ Отчёт со звездочкой * (водитель №$2)"
            "$PYTHON" taxi_report.py task1s "$2"
        else
            echo " ✸ Отчёт со звездочкой * (водитель №$2, тип клиента: $3)"
            "$PYTHON" taxi_report.py task1s "$2" "$3"
        fi
        ;;
    2)
        if [ -z "$2" ]; then
            "$PYTHON" taxi_report.py task2
        else
            "$PYTHON" taxi_report.py task2 "$2"
        fi
        ;;
    3)
        # --force перезаписывает уже сохранённый график без вопроса
        "$PYTHON" taxi_report.py task3 "${@:2}"
        ;;
    4)
        "$PYTHON" taxi_report.py task4 "${@:2}"
        ;;
    months)
        "$PYTHON" taxi_report.py months "${@:2}"
        ;;
    payments)
        "$PYTHON" taxi_report.py payments "${@:2}"
        ;;
    save)
        if [ "$2" = "--force" ]; then
            "$PYTHON" taxi_report.py save-all --force
        else
            "$PYTHON" taxi_report.py save-all
        fi
        ;;
    all)
        echo "============================================="
        echo "  ВЫПОЛНЕНИЕ ВСЕХ ЗАДАЧ"
        echo "============================================="
        echo ""
        echo "--- ЗАДАЧА 1: ОТЧЁТ ---"
        "$PYTHON" taxi_report.py task1 || exit 1
        echo ""
        echo "--- ЗАДАЧА 1s: ОТЧЁТ СО ЗВЕЗДОЧКОЙ * ---"
        "$PYTHON" taxi_report.py task1s || exit 1
        echo ""
        echo "--- ЗАДАЧА 2: СВОДНАЯ ТАБЛИЦА ---"
        "$PYTHON" taxi_report.py task2 || exit 1
        echo ""
        echo "--- ЗАДАЧА 3: ГРАФИК ---"
        "$PYTHON" taxi_report.py task3 || exit 1
        echo ""
        echo "--- ЗАДАЧА 4: ДИАГРАММА ---"
        "$PYTHON" taxi_report.py task4 || exit 1
        echo ""
        echo "--- ГРАФИКИ ПО МЕСЯЦАМ И СПОСОБАМ ОПЛАТЫ ---"
        "$PYTHON" taxi_report.py months || exit 1
        "$PYTHON" taxi_report.py payments || exit 1
        ;;
    "")
        show_help
        ;;
    *)
        show_help >&2
        echo "ОШИБКА: неизвестная команда $1" >&2
        exit 1
        ;;
esac
