"""Просмотр данных: дашборд, таблицы, поездки с фильтром, триграммный поиск."""

import tkinter as tk
from tkinter import ttk, messagebox

from psycopg2 import sql as psql

from . import sql

PG_TRGM_MISSING = (
    "Расширение pg_trgm не подключено, триграммный поиск недоступен.\n"
    "Выполните ./help.sh rebuild или попросите владельца базы выполнить:\n"
    "CREATE EXTENSION pg_trgm;"
)

FILTER_FIELDS = [
    "без фильтра", "таксопарк", "водитель", "тип клиента",
    "откуда", "куда", "дата",
    "стоимость >=", "стоимость <=", "расстояние >=", "расстояние <=",
    "время >=", "время <=",
]

NUMERIC_FILTERS = {
    "стоимость >=": ("p.стоимость >= %s", float),
    "стоимость <=": ("p.стоимость <= %s", float),
    "расстояние >=": ("p.расстояние_км >= %s", float),
    "расстояние <=": ("p.расстояние_км <= %s", float),
    "время >=": ("p.время_мин >= %s", int),
    "время <=": ("p.время_мин <= %s", int),
}


class BrowseMixin:

    def dashboard(self):
        """Главная сводка: сколько данных, выручка, средний чек, лучшие объекты."""
        lines = ["Дашборд TAXI — реальные поездки такси Чикаго, суммы в $", "=" * 56, ""]
        for label, query in sql.DASHBOARD_VALUES:
            rows, _ = self.fetch_rows(query, show_error=False)
            lines.append(f"{label}: {rows[0][0] if rows else '—'}")
        text = "\n".join(lines) + "\n"
        for title, query in sql.DASHBOARD_TABLES:
            rows, cols = self.fetch_rows(query, show_error=False)
            text += "\n\n" + self.format_table(rows, cols, title)
        self.display(text)
        self.set_status("Дашборд")

    def db_stats(self):
        self.execute_and_display(sql.DB_STATS, title="Сводная статистика по таблицам", status="Статистика БД")

    def show_structure(self):
        self.execute_and_display(sql.STRUCTURE, title="Структура БД", status="Структура БД")

    def show_tables_window(self):
        win = tk.Toplevel(self.root)
        win.title("Просмотр таблиц")
        win.geometry("360x360")
        win.transient(self.root)
        ttk.Label(win, text="Выберите таблицу:", font=("Arial", 12, "bold")).pack(pady=10)
        for table in sql.TABLES:
            ttk.Button(win, text=table, command=lambda t=table: self.view_table(t)).pack(fill=tk.X, padx=20, pady=4)

    def view_table(self, table):
        if table not in sql.TABLES:
            messagebox.showerror("Ошибка", "Неизвестная таблица")
            return
        if table == "ПОЕЗДКИ":
            title = "Таблица ПОЕЗДКИ с расшифровкой"
            self.execute_and_display(sql.RIDES_FILTERED.format(cond=""), [self.get_limit()], title=title, status=title)
        else:
            query = psql.SQL("SELECT * FROM {} ORDER BY 1 LIMIT %s").format(psql.Identifier(table))
            self.execute_and_display(query, [self.get_limit()], title=f"Таблица {table}", status=f"Таблица {table}")

    # ------------------------- поездки с фильтром -------------------------
    def latest_rides(self):
        cond, params = self.build_ride_filter()
        self.execute_and_display(sql.RIDES_FILTERED.format(cond=cond), params + [self.get_limit()],
                                 title="Последние поездки", status="Последние поездки")

    def clear_filters(self):
        self.filter_field_var.set("без фильтра")
        self.filter_value_var.set("")
        self.search_var.set("")
        self.latest_rides()

    def build_ride_filter(self):
        """Условие для sql.RIDES_FILTERED: (' AND ...', [параметры])."""
        field = self.filter_field_var.get().strip()
        value = self.filter_value_var.get().strip()
        if field == "без фильтра" or not value:
            return "", []

        like_value = f"%{value}%"
        text_filters = {
            "таксопарк": ("t.название ILIKE %s", [like_value]),
            # водитель задаётся кодом (12) или частью taxi_id
            "водитель": ("(v.код::text = %s OR v.taxi_id ILIKE %s)", [value.lstrip("№ "), like_value]),
            "тип клиента": ("(k.тип ILIKE %s OR k.описание ILIKE %s)", [like_value, like_value]),
            "откуда": ("ro.название ILIKE %s", [like_value]),
            "куда": ("rk.название ILIKE %s", [like_value]),
        }
        if field in text_filters:
            cond, params = text_filters[field]
            return " AND " + cond, params

        if field == "дата":
            # точная дата 2026-05-09 или часть даты/времени
            if len(value) == 10 and value[4] == "-" and value[7] == "-":
                return " AND p.дата::date = %s", [value]
            return " AND CAST(p.дата AS TEXT) ILIKE %s", [like_value]

        if field in NUMERIC_FILTERS:
            cond, caster = NUMERIC_FILTERS[field]
            try:
                return " AND " + cond, [caster(value.replace(",", "."))]
            except ValueError:
                messagebox.showerror("Ошибка фильтра", f"Для фильтра '{field}' нужно ввести число.")
                return " AND 1=0", []

        return "", []

    def load_autocomplete_data(self):
        """Списки названий для подсказок (таксопарки, типы клиентов, районы)."""
        self.autocomplete = {key: [] for key in sql.AUTOCOMPLETE}
        for key, query in sql.AUTOCOMPLETE.items():
            rows, _ = self.fetch_rows(query, show_error=False)
            self.autocomplete[key] = [r[0] for r in rows]

    # ------------------------- триграммный поиск -------------------------
    def get_similarity_threshold(self):
        """Порог схожести pg_trgm в пределах 0.05–1.0."""
        try:
            value = float(str(self.similarity_var.get()).replace(",", "."))
            value = max(0.05, min(1.0, value))
            self.similarity_var.set(str(value))
            return value
        except ValueError:
            self.similarity_var.set("0.3")
            return 0.3

    def ensure_pg_trgm(self, silent=False):
        """Проверяет, что расширение pg_trgm подключено (его создаёт ./help.sh rebuild)."""
        if not self.conn:
            if not silent:
                messagebox.showerror("Ошибка", "Нет подключения к БД")
            return False
        rows, _ = self.fetch_rows(sql.PG_TRGM_EXISTS, show_error=not silent)
        found = bool(rows)
        if not silent:
            if found:
                messagebox.showinfo("pg_trgm", "Расширение pg_trgm подключено.")
                self.set_status("pg_trgm подключено")
            else:
                messagebox.showwarning("pg_trgm", PG_TRGM_MISSING)
        return found

    def quick_search(self):
        """Триграммный поиск по таксопаркам, районам, типам клиентов и водителям."""
        text = self.search_var.get().strip()
        if not text:
            messagebox.showinfo("Поиск", "Введите текст для триграммного поиска")
            return
        if not self.ensure_pg_trgm(silent=True):
            messagebox.showerror("Триграммный поиск", PG_TRGM_MISSING)
            return
        threshold = self.get_similarity_threshold()
        params = [text.lower(), f"%{text}%", threshold, self.get_limit()]
        self.execute_and_display(sql.TRIGRAM_SEARCH, params,
                                 title=f"Триграммный поиск: {text} | порог {threshold}",
                                 status="Триграммный поиск")
