"""Модульные тесты сборщика parser/chicago_fetch.py и загрузчика parser/load_rides.py.

Не нужны ни сеть, ни база: обращения к API подменяются.
Запуск из корня проекта: python -m unittest discover -s tests/unit -v
"""

import csv
import gzip
import io
import re
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "parser"))

import chicago_fetch  # noqa: E402

# поездка в том виде, в каком её отдаёт API города
RAW_ROW = {
    "trip_id": "a" * 40,
    "taxi_id": "b" * 128,
    "trip_start_timestamp": "2026-01-31T23:45:00.000",
    "trip_end_timestamp": "2026-02-01T00:00:00.000",
    "trip_seconds": "900",
    "trip_miles": "3.2",
    "pickup_community_area": "8",
    "dropoff_community_area": "32",
    "fare": "12.25",
    "tips": "2",
    "tolls": "0",
    "extras": "1",
    "trip_total": "15.25",
    "payment_type": "Credit Card",
    "company": "Flash Cab",
}


class CompactTest(unittest.TestCase):
    def test_hashes_are_cut_to_16_chars(self):
        row = chicago_fetch.compact(RAW_ROW)
        self.assertEqual(row["trip_id"], "a" * 16)
        self.assertEqual(row["taxi_id"], "b" * 16)

    def test_zero_milliseconds_are_dropped(self):
        row = chicago_fetch.compact(RAW_ROW)
        self.assertEqual(row["trip_start_timestamp"], "2026-01-31T23:45:00")
        self.assertEqual(row["trip_end_timestamp"], "2026-02-01T00:00:00")

    def test_missing_end_time_is_kept_empty(self):
        row = chicago_fetch.compact({**RAW_ROW, "trip_end_timestamp": None})
        self.assertIsNone(row["trip_end_timestamp"])

    def test_original_row_is_not_changed(self):
        original = dict(RAW_ROW)
        chicago_fetch.compact(RAW_ROW)
        self.assertEqual(RAW_ROW, original)


class DayFileTest(unittest.TestCase):
    def test_path_has_year_folder_and_date(self):
        path = chicago_fetch.day_file(date(2026, 1, 5))
        self.assertEqual(path.relative_to(chicago_fetch.RIDES_DIR).as_posix(), "2026/2026-01-05.csv.gz")


class FetchDayTest(unittest.TestCase):
    def test_request_covers_exactly_one_day(self):
        with mock.patch.object(chicago_fetch, "query", return_value=[]) as query:
            chicago_fetch.fetch_day(date(2026, 12, 31), 500)
        params = query.call_args.args[0]
        self.assertIn("trip_start_timestamp >= '2026-12-31T00:00:00'", params["$where"])
        self.assertIn("trip_start_timestamp < '2027-01-01T00:00:00'", params["$where"])
        self.assertIn(chicago_fetch.QUALITY, params["$where"])
        self.assertEqual(params["$select"].split(","), chicago_fetch.FIELDS)
        # порядок по trip_id делает выборку равномерной и повторяемой
        self.assertEqual(params["$order"], "trip_id")
        self.assertEqual(params["$limit"], 500)


class QueryTest(unittest.TestCase):
    def test_retries_after_network_error(self):
        answers = [OSError("сеть недоступна"), io.BytesIO(b'[{"last": "2026-10-01T00:00:00.000"}]')]
        with mock.patch("urllib.request.urlopen", side_effect=answers) as urlopen, \
                mock.patch("time.sleep") as sleep, mock.patch("sys.stderr", io.StringIO()):
            rows = chicago_fetch.query({"$select": "x"})
        self.assertEqual(rows, [{"last": "2026-10-01T00:00:00.000"}])
        self.assertEqual(urlopen.call_count, 2)
        sleep.assert_called_once_with(5)

    def test_gives_up_after_last_attempt(self):
        with mock.patch("urllib.request.urlopen", side_effect=OSError("нет сети")) as urlopen, \
                mock.patch("time.sleep"), mock.patch("sys.stderr", io.StringIO()):
            with self.assertRaises(OSError):
                chicago_fetch.query({"$select": "x"}, retries=3)
        self.assertEqual(urlopen.call_count, 3)

    def test_latest_available_day_parses_timestamp(self):
        with mock.patch.object(chicago_fetch, "query", return_value=[{"last": "2026-10-05T23:59:00.000"}]):
            self.assertEqual(chicago_fetch.latest_available_day(), date(2026, 10, 5))


class SaveDayTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        patcher = mock.patch.object(chicago_fetch, "RIDES_DIR", Path(tmp.name))
        patcher.start()
        self.addCleanup(patcher.stop)

    def read_rows(self, day):
        with gzip.open(chicago_fetch.day_file(day), "rt", encoding="utf-8", newline="") as f:
            return list(csv.reader(f))

    def test_file_has_header_and_compacted_rows(self):
        day = date(2026, 1, 31)
        chicago_fetch.save_day(day, [{**RAW_ROW, "лишнее_поле": "x"}])
        header, row = self.read_rows(day)
        self.assertEqual(header, chicago_fetch.FIELDS)
        self.assertEqual(row[0], "a" * 16)
        self.assertEqual(row[2], "2026-01-31T23:45:00")
        self.assertEqual(row[-1], "Flash Cab")

    def test_same_data_gives_identical_file(self):
        # иначе git видел бы изменения при каждом повторном сборе
        day = date(2026, 1, 31)
        chicago_fetch.save_day(day, [RAW_ROW])
        first = chicago_fetch.day_file(day).read_bytes()
        # время сохранения другое: без mtime=0 gzip записал бы его в файл
        with mock.patch("time.time", return_value=2_000_000_000):
            chicago_fetch.save_day(day, [RAW_ROW])
        self.assertEqual(chicago_fetch.day_file(day).read_bytes(), first)


class MainTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        for patcher in (
            mock.patch.object(chicago_fetch, "RIDES_DIR", Path(tmp.name)),
            # последний день в наборе 10.10, значит, полный — 09.10
            mock.patch.object(chicago_fetch, "latest_available_day", return_value=date(2026, 10, 10)),
            mock.patch("sys.stdout", io.StringIO()),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_main(self, *args, rows=(RAW_ROW,)):
        with mock.patch.object(sys, "argv", ["chicago_fetch.py", *args]), \
                mock.patch.object(chicago_fetch, "fetch_day", return_value=list(rows)) as fetch_day:
            chicago_fetch.main()
        return [call.args[0] for call in fetch_day.call_args_list]

    def test_last_incomplete_day_is_not_fetched(self):
        days = self.run_main("--days", "3")
        self.assertEqual(days, [date(2026, 10, 7), date(2026, 10, 8), date(2026, 10, 9)])

    def test_existing_days_are_skipped(self):
        self.run_main("--from", "2026-10-01", "--to", "2026-10-02")
        days = self.run_main("--from", "2026-10-01", "--to", "2026-10-03")
        self.assertEqual(days, [date(2026, 10, 3)])

    def test_date_to_is_limited_by_last_complete_day(self):
        days = self.run_main("--from", "2026-10-08", "--to", "2026-12-31")
        self.assertEqual(days, [date(2026, 10, 8), date(2026, 10, 9)])

    def test_empty_day_is_not_saved(self):
        self.run_main("--from", "2026-10-09", "--to", "2026-10-09", rows=())
        self.assertFalse(chicago_fetch.day_file(date(2026, 10, 9)).exists())


class LoadRidesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import load_rides
        except ImportError as e:  # без psycopg2 загрузчик не импортируется
            raise unittest.SkipTest(f"нет зависимостей загрузчика: {e}")
        cls.load_rides = load_rides

    def test_staging_columns_match_fetched_fields(self):
        # COPY берёт колонки CSV по порядку: порядок должен совпадать с FIELDS сборщика
        body = self.load_rides.STAGING.split("(", 1)[1].rsplit(")", 1)[0]
        columns = re.findall(r"(\w+) [A-Z]+", body)
        self.assertEqual(columns, chicago_fetch.FIELDS)

    def test_file_day_is_date_from_name(self):
        self.assertEqual(self.load_rides.file_day(Path("rides/2026/2026-01-31.csv.gz")), "2026-01-31")

    def test_every_payment_type_has_russian_description(self):
        for kind, text in self.load_rides.CLIENT_TYPES.items():
            self.assertTrue(text and text != kind, kind)


if __name__ == "__main__":
    unittest.main()
