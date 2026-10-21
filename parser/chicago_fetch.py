#!/usr/bin/env python3
"""Сборщик реальных поездок такси Чикаго (открытые данные города).

Источник: Chicago Data Portal, набор "Taxi Trips" (ajtu-isnz).
Каждый день сохраняется отдельным файлом data/chicago/rides/ГГГГ/ГГГГ-ММ-ДД.csv.gz:
выборка из --per-day поездок, упорядоченных по trip_id. trip_id — хэш,
поэтому такая выборка равномерная и при повторном запуске та же самая.

Город выкладывает поездки раз в месяц, целым месяцем (в октябре в наборе есть
поездки по 30 сентября), поэтому сборщик проверяет набор каждый день, а день
сохраняется, только когда в наборе уже есть более поздние поездки (день полный).

Запуск:
    python3 parser/chicago_fetch.py                 # докачать недостающие дни за 45 дней
    python3 parser/chicago_fetch.py --days 365      # заполнить историю за год
    python3 parser/chicago_fetch.py --from 2026-01-01 --to 2026-01-31

Только стандартная библиотека: так скрипт работает в GitHub Actions без установки пакетов.
"""

import argparse
import csv
import gzip
import io
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

API = "https://data.cityofchicago.org/resource/ajtu-isnz.json"
ROOT = Path(__file__).resolve().parents[1]
RIDES_DIR = ROOT / "data" / "chicago" / "rides"

FIELDS = [
    "trip_id", "taxi_id", "trip_start_timestamp", "trip_end_timestamp",
    "trip_seconds", "trip_miles", "pickup_community_area", "dropoff_community_area",
    "fare", "tips", "tolls", "extras", "trip_total", "payment_type", "company",
]

# Отсев явного брака в исходных данных: нулевые и невозможные поездки
QUALITY = (
    "taxi_id IS NOT NULL AND trip_seconds > 0 AND trip_seconds <= 21600 "
    "AND trip_miles > 0 AND trip_miles <= 200 AND fare > 0 AND fare <= 1000"
)


def query(params, retries=4):
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=120) as resp:
                return json.load(resp)
        except Exception as e:  # сеть или временный отказ сервера — повторяем
            if attempt == retries - 1:
                raise
            wait = 5 * (attempt + 1)
            print(f"  повтор через {wait} с: {e}", file=sys.stderr)
            time.sleep(wait)


def latest_available_day():
    rows = query({"$select": "max(trip_start_timestamp) AS last"})
    return datetime.fromisoformat(rows[0]["last"]).date()


def day_file(day):
    return RIDES_DIR / f"{day:%Y}" / f"{day:%Y-%m-%d}.csv.gz"


def fetch_day(day, per_day):
    where = (f"trip_start_timestamp >= '{day:%Y-%m-%d}T00:00:00' "
             f"AND trip_start_timestamp < '{day + timedelta(days=1):%Y-%m-%d}T00:00:00' "
             f"AND {QUALITY}")
    return query({"$select": ",".join(FIELDS), "$where": where,
                  "$order": "trip_id", "$limit": per_day})


def compact(row):
    """Укорачивает поля без потери смысла, чтобы файлы занимали меньше места в git.

    trip_id и taxi_id в исходных данных — случайные хэши (40 и 128 символов);
    первых 16 символов (64 бита) достаточно, чтобы различать сотни тысяч поездок
    и тысячи машин. У времени отбрасываются нулевые миллисекунды.
    """
    row = dict(row)
    for key in ("trip_id", "taxi_id"):
        row[key] = row[key][:16]
    for key in ("trip_start_timestamp", "trip_end_timestamp"):
        if row.get(key):
            row[key] = row[key].removesuffix(".000")
    return row


def save_day(day, rows):
    path = day_file(day)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [compact(r) for r in rows]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n", extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    # mtime=0: одинаковые данные дают байт-в-байт одинаковый файл, git не видит лишних изменений
    with open(path, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz:
        gz.write(buf.getvalue().encode("utf-8"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--days", type=int, default=45, help="сколько последних дней проверить (по умолчанию 45)")
    ap.add_argument("--from", dest="date_from", type=date.fromisoformat, help="начальная дата ГГГГ-ММ-ДД")
    ap.add_argument("--to", dest="date_to", type=date.fromisoformat, help="конечная дата ГГГГ-ММ-ДД")
    ap.add_argument("--per-day", type=int, default=2000, help="поездок в выборке за день (по умолчанию 2000)")
    args = ap.parse_args()

    last_complete = latest_available_day() - timedelta(days=1)
    date_to = min(args.date_to or last_complete, last_complete)
    date_from = args.date_from or (date_to - timedelta(days=args.days - 1))
    print(f"Последний полный день в наборе: {last_complete}; период: {date_from} — {date_to}")

    saved = skipped = empty = 0
    day = date_from
    while day <= date_to:
        if day_file(day).exists():
            skipped += 1
        else:
            rows = fetch_day(day, args.per_day)
            if rows:
                save_day(day, rows)
                saved += 1
                print(f"  {day}: {len(rows)} поездок")
            else:
                empty += 1
                print(f"  {day}: данных нет")
        day += timedelta(days=1)

    print(f"Сохранено дней: {saved}, уже было: {skipped}, без данных: {empty}")


if __name__ == "__main__":
    main()
