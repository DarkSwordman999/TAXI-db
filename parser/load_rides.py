#!/usr/bin/env python3
"""Загрузка поездок из data/chicago/rides/**/*.csv.gz в базу TAXI.

Повторный запуск безопасен: уже загруженные поездки (по trip_id) пропускаются,
поэтому после git pull достаточно запустить скрипт снова — добавятся только новые дни.
Таксопарки, водители (taxi_id) и типы клиентов (способы оплаты) пополняются из тех же файлов.

Запуск из корня проекта: python3 parser/load_rides.py
Настройки подключения — app/scripts/db_config.py (.env / переменные PG*).
"""

import gzip
import sys
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
from scripts.db_config import DB_CONFIG  # noqa: E402

RIDES_DIR = ROOT / "data" / "chicago" / "rides"
MILE_KM = 1.609344

# Русские названия способов оплаты; неизвестный новый тип получит описание = тип
CLIENT_TYPES = {
    "Credit Card": "Банковская карта",
    "Cash": "Наличные",
    "Mobile": "Мобильное приложение",
    "Prcard": "Предоплаченная карта",
    "Unknown": "Неизвестно",
    "Dispute": "Оспоренная оплата",
    "No Charge": "Без оплаты",
}

STAGING = """
CREATE TEMP TABLE staging (
    trip_id TEXT, taxi_id TEXT, trip_start_timestamp TIMESTAMP, trip_end_timestamp TIMESTAMP,
    trip_seconds INTEGER, trip_miles NUMERIC, pickup_community_area INTEGER,
    dropoff_community_area INTEGER, fare NUMERIC, tips NUMERIC, tolls NUMERIC,
    extras NUMERIC, trip_total NUMERIC, payment_type TEXT, company TEXT
) ON COMMIT DROP
"""

LOAD = """
-- город пишет один таксопарк по-разному ("Agency  LLC" и "Agency Llc"):
-- лишние пробелы убираются, а названия сравниваются без учёта регистра
UPDATE staging SET company = COALESCE(regexp_replace(trim(company), '\\s+', ' ', 'g'), 'Не указан');

INSERT INTO ТАКСОПАРКИ (название)
SELECT DISTINCT ON (lower(company)) company FROM staging ORDER BY lower(company), company
ON CONFLICT DO NOTHING;

INSERT INTO ВОДИТЕЛИ (taxi_id)
SELECT DISTINCT taxi_id FROM staging
ON CONFLICT (taxi_id) DO NOTHING;

INSERT INTO КЛИЕНТЫ (тип, описание)
SELECT DISTINCT s.тип, COALESCE(m.описание, s.тип)
FROM (SELECT COALESCE(payment_type, 'Unknown') AS тип FROM staging) s
LEFT JOIN client_types m ON m.тип = s.тип
ON CONFLICT (тип) DO NOTHING;

INSERT INTO ПОЕЗДКИ (trip_id, дата, окончание, водитель, клиент, таксопарк, откуда, куда,
                     расстояние_км, время_мин, стоимость, чаевые, сборы)
SELECT s.trip_id, s.trip_start_timestamp, s.trip_end_timestamp, В.код, К.код, Т.код,
       s.pickup_community_area, s.dropoff_community_area,
       ROUND(s.trip_miles * %(mile_km)s, 2),
       GREATEST(1, ROUND(s.trip_seconds / 60.0)),
       s.fare, COALESCE(s.tips, 0), COALESCE(s.tolls, 0) + COALESCE(s.extras, 0)
FROM staging s
JOIN ВОДИТЕЛИ В ON В.taxi_id = s.taxi_id
JOIN КЛИЕНТЫ К ON К.тип = COALESCE(s.payment_type, 'Unknown')
JOIN ТАКСОПАРКИ Т ON lower(Т.название) = lower(s.company)
ON CONFLICT (trip_id) DO NOTHING;
"""


def main():
    files = sorted(RIDES_DIR.glob("*/*.csv.gz"))
    if not files:
        print(f"Нет файлов в {RIDES_DIR}: сначала запустите parser/chicago_fetch.py")
        return 1

    conn = psycopg2.connect(**DB_CONFIG)
    with conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM ПОЕЗДКИ")
        before = cur.fetchone()[0]
        cur.execute(STAGING)
        cur.execute("CREATE TEMP TABLE client_types (тип TEXT, описание TEXT) ON COMMIT DROP")
        cur.executemany("INSERT INTO client_types VALUES (%s, %s)", CLIENT_TYPES.items())
        for path in files:
            with gzip.open(path, "rt", encoding="utf-8") as f:
                cur.copy_expert("COPY staging FROM STDIN WITH (FORMAT csv, HEADER true)", f)
        cur.execute(LOAD, {"mile_km": MILE_KM})
        cur.execute("SELECT COUNT(*), MIN(дата)::date, MAX(дата)::date FROM ПОЕЗДКИ")
        total, first, last = cur.fetchone()
    conn.close()

    print(f"Файлов: {len(files)}; добавлено поездок: {total - before}; "
          f"всего в базе: {total} (с {first} по {last})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
