#!/bin/bash
# настройки подключения: переменные PG* из окружения или из .env в корне проекта
[ -f "$(dirname "$0")/.env" ] && set -a && . "$(dirname "$0")/.env" && set +a
DATABASE="${PGDATABASE:-taxi}"
# Windows: psql выводит свои русские надписи («(1 строка)») в кодировке ANSI,
# в консоли UTF-8 они нечитаемы — там они на английском, данные остаются русскими
case "$OSTYPE" in msys*|cygwin*) export LC_MESSAGES=C ;; esac
# SQL-файлы проекта в UTF-8. Без этой строки psql в Windows иногда берет кодировку
# консоли (WIN1251), например при выводе в /dev/null, и ломает кириллицу в запросах
export PGCLIENTENCODING="${PGCLIENTENCODING:-UTF8}"

if [ -z "$1" ]; then
    echo "Использование: ./run_sql.sh файл.sql [параметр]"
    echo "Пример: ./run_sql.sh queries/subqueries/06_rides_above_avg_param.sql Иванов"
    exit 1
fi

if [ ! -f "$1" ]; then
    echo "ОШИБКА: Файл $1 не найден"
    exit 1
fi

if [ -z "$2" ]; then
    psql -v ON_ERROR_STOP=1 -c "\pset pager off" -d "$DATABASE" -f "$1"
else
    psql -v ON_ERROR_STOP=1 -c "\pset pager off" -d "$DATABASE" -f "$1" -v arg1="$2"
fi
