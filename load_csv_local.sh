#!/bin/bash

CSV_FILE="data/rides.csv"

if [ ! -f "$CSV_FILE" ]; then
    echo "Ошибка: файл $CSV_FILE не найден"
    exit 1
fi

echo "Загрузка данных из CSV в PostgreSQL (только первые 6 колонок)..."

# Всё делаем в одной psql-сессии
psql -d taxi_lab5 << 'SQL'
-- Создаём временную таблицу
DROP TABLE IF EXISTS temp_rides;
CREATE TEMP TABLE temp_rides (
    ts TIMESTAMP,
    from_loc TEXT,
    to_loc TEXT,
    distance_km NUMERIC,
    duration_min INTEGER,
    price_rub NUMERIC
);

-- Загружаем CSV через STDIN (обрезаем первые 6 колонок)
\copy temp_rides(ts, from_loc, to_loc, distance_km, duration_min, price_rub) FROM PROGRAM 'tail -n +2 data/rides.csv | cut -d"," -f1-6' DELIMITER ',' CSV;

-- Вставляем новые записи
INSERT INTO ПОЕЗДКИ (дата, стоимость, водитель, автомобиль, клиент, расстояние_км, время_мин)
SELECT 
    ts,
    price_rub,
    (row_number() OVER() % 32) + 1,
    (row_number() OVER() % 30) + 1,
    (row_number() OVER() % 250) + 1,
    distance_km,
    duration_min
FROM temp_rides t
WHERE NOT EXISTS (
    SELECT 1 FROM ПОЕЗДКИ p 
    WHERE p.дата = t.ts 
    AND p.расстояние_км = t.distance_km
);

SELECT 'Загрузка завершена. Всего записей: ' || COUNT(*) FROM ПОЕЗДКИ;
SQL

echo "Готово!"
