#!/bin/bash
# Автотест проекта: пересобирает ТЕСТОВУЮ базу и прогоняет все команды
# ./help.sh, все SQL-файлы и ./python_reports.sh. Падает при первой ошибке.
#
# Запуск из любой папки: tests/run_all.sh
# База берётся из PGDATABASE, по умолчанию taxi_test; рабочую базу taxi
# скрипт не трогает — пересборка удаляет все данные.
# SKIP_REBUILD=1 — не пересобирать базу (для повторных прогонов на своей машине).
# Его же запускает GitHub Actions (.github/workflows/tests.yml).

cd "$(dirname "$0")/.." || exit 1
export PGDATABASE="${PGDATABASE:-taxi_test}"

# help.sh и rebuild.sh читают .env, и его значения важнее окружения:
# проверяем, какая база получится на самом деле
EFFECTIVE_DB=$(bash -c '[ -f .env ] && set -a && . ./.env; echo "${PGDATABASE:-taxi}"')
if [ "$EFFECTIVE_DB" = "taxi" ]; then
    echo "ОТКАЗ: тест пересоздаёт базу, а скрипты проекта будут работать с рабочей базой taxi." >&2
    echo "Задайте другую базу: PGDATABASE=taxi_test (и уберите PGDATABASE из .env)." >&2
    exit 1
fi
export PGDATABASE="$EFFECTIVE_DB"

PYTHON=python3
"$PYTHON" -c "" 2>/dev/null || PYTHON=python
export PYTHONIOENCODING=utf-8
export PGCLIENTENCODING=UTF8

# графики пишутся во временную папку, а не в docs/
TMP_DIR=$(mktemp -d)
export TAXI_DOCS_DIR="$TMP_DIR/docs"
trap 'rm -rf "$TMP_DIR"' EXIT

LOG="$TMP_DIR/step.log"
PASSED=0

# step "описание" команда...: команда должна завершиться с кодом 0 и без ERROR в выводе
step() {
    local title="$1"
    shift
    if "$@" </dev/null >"$LOG" 2>&1 && ! grep -qE '^(psql:.*)?(ERROR|ОШИБКА):|Traceback' "$LOG"; then
        PASSED=$((PASSED + 1))
        echo "  ok  $title"
    else
        echo "FAIL  $title" >&2
        echo "----- вывод: $* -----" >&2
        cat "$LOG" >&2
        exit 1
    fi
}

# step_fails "описание" команда...: команда обязана завершиться с ошибкой
step_fails() {
    local title="$1"
    shift
    if "$@" </dev/null >"$LOG" 2>&1; then
        echo "FAIL  $title: ожидалась ошибка, а команда прошла" >&2
        cat "$LOG" >&2
        exit 1
    fi
    PASSED=$((PASSED + 1))
    echo "  ok  $title"
}

# step_output "описание" "ожидаемый текст" команда...
step_output() {
    local title="$1" expected="$2"
    shift 2
    step "$title" "$@"
    if ! grep -qF -- "$expected" "$LOG"; then
        echo "FAIL  $title: в выводе нет «$expected»" >&2
        cat "$LOG" >&2
        exit 1
    fi
}

# одно значение из базы
value() {
    printf '%s\n' "$1" | psql -X -q -t -A -v ON_ERROR_STOP=1
}

echo "=== База $PGDATABASE ==="
if [ -z "$(printf '%s\n' "SELECT 1 FROM pg_database WHERE datname = '$PGDATABASE'" | psql -X -t -A -d postgres)" ]; then
    createdb "$PGDATABASE" || exit 1
fi

echo "=== Синтаксис скриптов ==="
for f in *.sh setup/*.sh tests/*.sh; do
    step "bash -n $f" bash -n "$f"
done
step "python: компиляция всех модулей" "$PYTHON" -m compileall -q taxi_report.py parser app

echo "=== Пересборка базы ==="
if [ "${SKIP_REBUILD:-}" = "1" ]; then
    echo "      пропущена (SKIP_REBUILD=1)"
else
    step "./help.sh rebuild" ./help.sh rebuild
fi
RIDES=$(value "SELECT COUNT(*) FROM ПОЕЗДКИ")
FILES=$(find data/chicago/rides -name '*.csv.gz' | wc -l)
if [ "$RIDES" -lt 1000 ]; then
    echo "FAIL  после пересборки в базе всего $RIDES поездок" >&2
    exit 1
fi
echo "      поездок: $RIDES, файлов с днями: $FILES"
step_output "./help.sh load: повторная загрузка ничего не добавляет" "Новых дней нет" ./help.sh load
if [ "$(value "SELECT COUNT(*) FROM ПОЕЗДКИ")" != "$RIDES" ]; then
    echo "FAIL  повторная загрузка изменила число поездок" >&2
    exit 1
fi

echo "=== help.sh: каждый файл helper/ вызывается командой ==="
# иначе запрос живёт в двух местах (файл и help.sh) и копии расходятся
for f in helper/*.sql; do
    if ! grep -qF "$f" help.sh; then
        echo "FAIL  $f не вызывается ни одной командой help.sh" >&2
        exit 1
    fi
done
echo "  ok  все файлы helper/ используются"

echo "=== help.sh: команды только для чтения ==="
step "./help.sh без параметров (меню)" bash -c './help.sh; [ $? -eq 1 ]'
for cmd in task1 task2 task3 \
           companies drivers clients count latest clients-rides tables columns \
           join-inner join-left join-right join-full join-cross join-self \
           top-areas top-drivers by-month avg-check by-hour company-stats driver-load \
           tips-by-client by-weekday revenue-by-client distance-by-company hour-share \
           check-by-hour top-tips \
           view-user view-tech view-check \
           sub-deviation sub-company-rating sub-above-company-avg sub-company-stats sub-top3 \
           sub-good-drivers sub-best-drivers sub-expensive sub-all \
           func-create func-drivers-above func-company-season func-pivot func-all \
           update-before delete-before; do
    step "./help.sh $cmd" ./help.sh "$cmd"
done
DRIVER=$(value "SELECT MIN(водитель) FROM ПОЕЗДКИ")
for day in 1 7; do
    step "./help.sh task4 $day" ./help.sh task4 "$day"
done
step_output "./help.sh find-company Flash" "Flash" ./help.sh find-company Flash
step "./help.sh find-company с кавычкой" ./help.sh find-company "O'Hare"
step_output "./help.sh find-area Park" "Park" ./help.sh find-area Park
step "./help.sh find-area с кавычкой" ./help.sh find-area "O'Hare"
step_output "./help.sh rename-demo" "Парк O'Brien" ./help.sh rename-demo 1 "Парк O'Brien"
step "./help.sh rename-demo без названия" ./help.sh rename-demo 1
step "./help.sh delete-demo $DRIVER" ./help.sh delete-demo "$DRIVER"
step "./help.sh driver $DRIVER" ./help.sh driver "$DRIVER"
step "./help.sh driver-rides $DRIVER" ./help.sh driver-rides "$DRIVER"
step "./help.sh rides-above 100" ./help.sh rides-above 100
step "./help.sh drivers-above 10000" ./help.sh drivers-above 10000
step "./help.sh sub-above-driver-avg $DRIVER" ./help.sh sub-above-driver-avg "$DRIVER"
step "./help.sh func-drivers-above 5000" ./help.sh func-drivers-above 5000
step "./help.sh 01 (номер вместо имени)" ./help.sh 01
step "./help.sh 203 (номер вместо имени)" ./help.sh 203

echo "=== help.sh: ошибки должны давать ненулевой код ==="
BAD_SQL="$TMP_DIR/bad.sql"
echo "SELECT * FROM нет_такой_таблицы;" >"$BAD_SQL"
step_fails "SQL-файл с ошибкой" ./help.sh "$BAD_SQL"
step_fails "SQL-файл с ошибкой через h1" ./help.sh h1 "$BAD_SQL"
step_fails "неизвестная команда" ./help.sh no-such-command
step_fails "task4 с днём 8" ./help.sh task4 8
step_fails "нечисловой код водителя" ./help.sh driver "1; DROP TABLE ПОЕЗДКИ"
step_fails "python_reports.sh: неизвестная команда" ./python_reports.sh no-such-command

echo "=== Все SQL-файлы только для чтения ==="
# параметр arg1 для файлов, которые его ждут
param_for() {
    case "$1" in
        helper/15_demo_with_param.sql) echo "Flash" ;;
        helper/24_search_area.sql) echo "Park" ;;
        queries/subqueries/06_rides_above_avg_param.sql) echo "$DRIVER" ;;
        queries/tasks/04_revenue_by_driver_for_day.sql) echo "3" ;;
    esac
}
# файлы, меняющие данные, идут отдельно и в конце
is_modifying() {
    case "$1" in
        helper/22_*|helper/23_*|helper/61_*|helper/62_*|helper/64_*|helper/65_*) return 0 ;;
        queries/delete/*|queries/insert/*|queries/update/*) return 0 ;;
    esac
    return 1
}
for f in helper/*.sql queries/*/*.sql; do
    is_modifying "$f" && continue
    step "$f" ./help.sh "$f" "$(param_for "$f")"
done
step "./help.sh h1 (run_sql.sh) с параметром" ./help.sh h1 helper/15_demo_with_param.sql Flash

echo "=== python_reports.sh ==="
step "./python_reports.sh без параметров (справка)" ./python_reports.sh
step "./python_reports.sh 1" ./python_reports.sh 1
step "./python_reports.sh 1 $DRIVER" ./python_reports.sh 1 "$DRIVER"
step "./python_reports.sh 1s" ./python_reports.sh 1s
step "./python_reports.sh 1s $DRIVER Cash" ./python_reports.sh 1s "$DRIVER" Cash
step "./python_reports.sh 2" ./python_reports.sh 2
step "./python_reports.sh 2 Credit" ./python_reports.sh 2 Credit
step "./python_reports.sh 3 --force" ./python_reports.sh 3 --force
step "./python_reports.sh 4 --force" ./python_reports.sh 4 --force
step "./python_reports.sh 4 $DRIVER --force" ./python_reports.sh 4 "$DRIVER" --force
step "./python_reports.sh months --force" ./python_reports.sh months --force
step "./python_reports.sh payments --force" ./python_reports.sh payments --force
step "./python_reports.sh payments $DRIVER --force" ./python_reports.sh payments "$DRIVER" --force
step "./python_reports.sh save --force" ./python_reports.sh save --force
step "./python_reports.sh all" ./python_reports.sh all
for png in task3_chart.png task4_chart.png "task4_chart_$DRIVER.png"            months_chart.png payments_chart.png "payments_chart_$DRIVER.png"; do
    if [ ! -s "$TAXI_DOCS_DIR/$png" ]; then
        echo "FAIL  график $png не создан" >&2
        exit 1
    fi
done
echo "  ok  графики созданы"

echo "=== Команды и файлы, меняющие данные ==="
for cmd in update-do update-after delete-do delete-after; do
    step "./help.sh $cmd" ./help.sh "$cmd"
done
for f in helper/*.sql queries/*/*.sql; do
    is_modifying "$f" || continue
    step "$f" ./help.sh "$f" "$(param_for "$f")"
done
RIDE=$(value "SELECT MIN(код_поездки) FROM ПОЕЗДКИ")
COMPANY=$(value "SELECT MIN(код) FROM ТАКСОПАРКИ")
CLIENT=$(value "SELECT MIN(код) FROM КЛИЕНТЫ")
step_output "./help.sh add-company" "Тестовый парк" ./help.sh add-company "Тестовый парк"
step "./help.sh add-driver" ./help.sh add-driver "test-driver-$$"
step_output "./help.sh rename-company" "Парк O'Brien" ./help.sh rename-company "$COMPANY" "Парк O'Brien"
step_output "./help.sh client-desc" "Тестовое описание" ./help.sh client-desc "$CLIENT" "Тестовое описание"
step "./help.sh set-ride-company" ./help.sh set-ride-company "$RIDE" "$COMPANY"
step_output "./help.sh set-tips" "1.50" ./help.sh set-tips "$RIDE" 1.50
DRIVER_TO_DELETE=$(value "SELECT MAX(водитель) FROM ПОЕЗДКИ")
step_output "./help.sh delete-driver $DRIVER_TO_DELETE" "Водитель удалён" ./help.sh delete-driver "$DRIVER_TO_DELETE"
if [ "$(value "SELECT COUNT(*) FROM ВОДИТЕЛИ WHERE код = $DRIVER_TO_DELETE")" != "0" ]; then
    echo "FAIL  водитель $DRIVER_TO_DELETE не удалён" >&2
    exit 1
fi

echo ""
echo "=== Все проверки пройдены: $PASSED ==="
