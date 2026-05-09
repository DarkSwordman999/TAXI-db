#!/bin/bash

# Параметры подключения к Render PostgreSQL
DB_HOST="dpg-d7vjcc67r5hc73at1hbg-a.frankfurt-postgres.render.com"
DB_PORT="5432"
DB_NAME="taxi_lab5"
DB_USER="taxis_user"
DB_PASSWORD="i05JtXBqRwzNfmCqN7rLGTzREAoNTQCQ"

CSV_FILE="data/rides.csv"

# Проверяем существует ли CSV файл
if [ ! -f "$CSV_FILE" ]; then
    echo "Ошибка: CSV файл $CSV_FILE не найден"
    exit 1
fi

echo "=========================================="
echo "Загрузка данных из CSV в PostgreSQL"
echo "Источник: $CSV_FILE"
echo "База: $DB_NAME на $DB_HOST"
echo "=========================================="

# Считаем строки в CSV (без заголовка)
TOTAL_LINES=$(tail -n +2 "$CSV_FILE" | wc -l | tr -d ' ')
echo "Найдено строк в CSV: $TOTAL_LINES"

# Создаём временную таблицу с такой же структурой
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << 'SQL'
    CREATE TEMP TABLE temp_rides (
        run_id TEXT,
        timestamp TIMESTAMP,
        from_loc TEXT,
        to_loc TEXT,
        distance_km NUMERIC,
        duration_min INTEGER,
        price_rub NUMERIC
    ) ON COMMIT DROP;
SQL

# Загружаем CSV во временную таблицу
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\copy temp_rides(run_id, timestamp, from_loc, to_loc, distance_km, duration_min, price_rub) FROM '$CSV_FILE' DELIMITER ',' CSV HEADER;"

# Вставляем данные в основную таблицу ПОЕЗДКИ (пропуская дубликаты по run_id + направление)
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << 'SQL'
    INSERT INTO ПОЕЗДКИ (дата, стоимость, водитель, автомобиль, клиент, расстояние_км, время_мин)
    SELECT 
        t.timestamp,
        t.price_rub,
        (row_number() over() % 32) + 1 as водитель,
        (row_number() over() % 30) + 1 as автомобиль,
        (row_number() over() % 250) + 1 as клиент,
        t.distance_km,
        t.duration_min
    FROM temp_rides t
    WHERE NOT EXISTS (
        SELECT 1 FROM ПОЕЗДКИ p 
        WHERE p.дата = t.timestamp 
        AND p.расстояние_км = t.distance_km
    );
SQL

# Проверяем результат
echo ""
echo "=========================================="
echo "ПРОВЕРКА РЕЗУЛЬТАТА"
echo "=========================================="

CURRENT_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM ПОЕЗДКИ;" | tr -d ' ')
echo "Всего записей в таблице ПОЕЗДКИ: $CURRENT_COUNT"

echo ""
echo "Последние 5 добавленных записей:"
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT код_поездки, дата, стоимость, расстояние_км FROM ПОЕЗДКИ ORDER BY код_поездки DESC LIMIT 5;"

echo ""
echo "Загрузка завершена!"
