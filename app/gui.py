#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GUI для базы данных TAXI.
Запуск из корня проекта: ./run_app.sh (или python3 app/gui.py).
Настройки подключения — app/scripts/db_config.py.
"""

import csv
import os
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, simpledialog

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import psycopg2
from psycopg2 import sql as psql

from scripts.db_config import DB_CONFIG


class TaxiApp:
    TABLES = ["ТАКСОПАРКИ", "ВОДИТЕЛИ", "КЛИЕНТЫ", "РАЙОНЫ", "ПОЕЗДКИ", "СЕЗОН"]

    def __init__(self, root):
        self.root = root
        self.root.title("TAXI: поездки такси Чикаго")
        self.root.geometry("1420x860")
        self.root.minsize(1100, 700)

        self.conn = None
        self.last_rows = []
        self.last_cols = []
        self.status_var = tk.StringVar(value="Готово")
        self.filter_field_var = tk.StringVar(value="без фильтра")
        self.filter_value_var = tk.StringVar(value="")
        self.limit_var = tk.StringVar(value="100")
        self.search_var = tk.StringVar(value="")
        self.similarity_var = tk.StringVar(value="0.3")

        self.connect_db()
        self.create_menu()
        self.create_widgets()
        self.load_autocomplete_data()
        self.dashboard()

    # ------------------------- базовые методы -------------------------
    def connect_db(self):
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.conn.autocommit = False
            self.status_var.set("Подключено к БД")
        except Exception as e:
            self.conn = None
            self.status_var.set(f"Ошибка подключения: {e}")
            messagebox.showerror("Ошибка подключения", str(e))

    def reconnect(self):
        try:
            if self.conn:
                self.conn.close()
        except Exception:
            pass
        self.connect_db()
        self.load_autocomplete_data()
        self.db_stats()

    def create_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Экспорт текущего отчёта в CSV", command=self.export_current_csv)
        file_menu.add_command(label="Экспорт всех таблиц в CSV", command=self.export_all_tables_csv)
        file_menu.add_command(label="Бэкап БД", command=self.backup_db)
        file_menu.add_separator()
        file_menu.add_command(label="Запустить SQL-файл", command=self.run_sql_file)
        file_menu.add_command(label="SQL-скрипты проекта", command=self.sql_scripts_manager)
        file_menu.add_separator()
        file_menu.add_command(label="Команды ./help.sh", command=self.h_commands_window)
        file_menu.add_command(label="Команды ./python_reports.sh", command=self.python_commands_window)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        menubar.add_cascade(label="Файл", menu=file_menu)

        db_menu = tk.Menu(menubar, tearoff=0)
        db_menu.add_command(label="Переподключиться", command=self.reconnect)
        db_menu.add_command(label="Структура БД", command=self.show_structure)
        db_menu.add_command(label="Статистика БД", command=self.db_stats)
        db_menu.add_command(label="Создать pg_trgm", command=self.ensure_pg_trgm)
        db_menu.add_separator()
        db_menu.add_command(label="Команды ./help.sh", command=self.h_commands_window)
        db_menu.add_command(label="Команды ./python_reports.sh", command=self.python_commands_window)
        menubar.add_cascade(label="База данных", menu=db_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="О программе", command=self.show_about)
        menubar.add_cascade(label="Справка", menu=help_menu)

        self.root.config(menu=menubar)

    def create_widgets(self):
        main = ttk.Frame(self.root, padding=6)
        main.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(main, width=260)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        left.pack_propagate(False)

        ttk.Label(left, text="TAXI GUI", font=("Arial", 15, "bold")).pack(anchor="w", pady=(0, 8))

        self.add_button_group(left, "Основное", [
            ("Дашборд", self.dashboard),
            ("Статистика БД", self.db_stats),
            ("Последние поездки", self.latest_rides),
            ("Просмотр таблиц", self.show_tables_window),
            ("Структура БД", self.show_structure),
        ])
        self.add_button_group(left, "Рейтинги и отчёты", [
            ("Топ водителей", self.top_drivers),
            ("Типы клиентов", self.top_clients),
            ("Доход по таксопаркам", self.revenue_by_company),
            ("Статистика таксопарков", self.company_stats),
            ("По сезонам", self.season_stats),
        ])
        self.add_button_group(left, "Аналитика", [
            ("Динамика по месяцам", self.chart_monthly_revenue),
            ("Круговая по оплате", self.chart_payment_pie),
            ("Выручка водителей", self.chart_driver_revenue),
            ("По дням недели", self.chart_weekday_revenue),
            ("Распределение стоимости", self.fare_distribution),
            ("Средняя поездка", self.average_ride_report),
            ("Отчёт за период", self.period_report),
            ("Дни недели", self.weekday_report),
            ("Часы суток", self.hour_report),
        ])
        self.add_button_group(left, "Действия", [
            ("Добавить запись", self.add_record_window),
            ("Редактировать запись", self.edit_record_window),
            ("Полное редактирование", self.edit_any_record),
            ("Удалить запись", self.delete_record_window),
            ("UPDATE до/после", self.update_before_after),
            ("DELETE до/после", self.delete_before_after),
        ])
        self.add_button_group(left, "Контроль", [
            ("Дорогие поездки", self.expensive_rides),
            ("Длинные поездки", self.long_rides),
            ("Неактивные водители", self.inactive_drivers),
            ("Таксопарки без поездок", self.inactive_companies),
            ("Проверка связей", self.data_quality_check),
        ])
        self.add_button_group(left, "Полное меню", [
            ("Команды ./help.sh", self.h_commands_window),
            ("Команды ./python_reports.sh", self.python_commands_window),
            ("SQL-скрипты проекта", self.sql_scripts_manager),
        ])
        self.add_button_group(left, "Администрирование", [
            ("Создать views", self.create_views),
            ("Проверить views", self.check_views),
            ("Создать функции", self.create_functions),
            ("Демо функций", self.functions_demo),
            ("Создать pg_trgm", self.ensure_pg_trgm),
            ("Архивация поездок", self.archive_old_rides),
            ("Экспорт текущего CSV", self.export_current_csv),
            ("Экспорт всех таблиц", self.export_all_tables_csv),
            ("Бэкап", self.backup_db),
            ("SQL-файл", self.run_sql_file),
            ("SQL-скрипты проекта", self.sql_scripts_manager),
        ])

        right = ttk.Frame(main)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        filters = ttk.LabelFrame(right, text="Параметры и фильтр", padding=8)
        filters.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(filters, text="Количество:").grid(row=0, column=0, sticky="w", padx=4, pady=3)
        ttk.Spinbox(filters, from_=1, to=5000, textvariable=self.limit_var, width=8).grid(row=0, column=1, sticky="w", padx=4, pady=3)

        ttk.Label(filters, text="Фильтр поездок по полю:").grid(row=0, column=2, sticky="w", padx=4, pady=3)
        self.filter_field_combo = ttk.Combobox(
            filters,
            textvariable=self.filter_field_var,
            values=[
                "без фильтра", "таксопарк", "водитель", "тип клиента",
                "откуда", "куда", "дата",
                "стоимость >=", "стоимость <=", "расстояние >=", "расстояние <=",
                "время >=", "время <=",
            ],
            width=18,
            state="readonly",
        )
        self.filter_field_combo.grid(row=0, column=3, sticky="w", padx=4, pady=3)
        self.filter_field_combo.bind("<<ComboboxSelected>>", lambda e: self.filter_value_var.set(""))

        ttk.Label(filters, text="Значение:").grid(row=0, column=4, sticky="w", padx=4, pady=3)
        self.filter_value_entry = ttk.Entry(filters, textvariable=self.filter_value_var, width=28)
        self.filter_value_entry.grid(row=0, column=5, sticky="w", padx=4, pady=3)
        self.filter_value_entry.bind("<Return>", lambda e: self.latest_rides())

        ttk.Button(filters, text="Применить", command=self.latest_rides).grid(row=0, column=6, sticky="w", padx=4, pady=3)
        ttk.Button(filters, text="Сбросить", command=self.clear_filters).grid(row=0, column=7, sticky="w", padx=4, pady=3)

        hint = "Примеры: таксопарк = Flash; водитель = 12; откуда = Loop; дата = 2026-03-15; стоимость >= 50"
        ttk.Label(filters, text=hint, foreground="#666").grid(row=1, column=2, columnspan=6, sticky="w", padx=4, pady=1)

        ttk.Label(filters, text="Триграммный поиск:").grid(row=2, column=0, sticky="w", padx=4, pady=3)
        search_entry = ttk.Entry(filters, textvariable=self.search_var, width=32)
        search_entry.grid(row=2, column=1, columnspan=2, sticky="w", padx=4, pady=3)
        search_entry.bind("<Return>", lambda e: self.quick_search())

        ttk.Label(filters, text="Порог:").grid(row=2, column=3, sticky="e", padx=4, pady=3)
        ttk.Spinbox(filters, from_=0.05, to=1.0, increment=0.05, textvariable=self.similarity_var, width=6).grid(row=2, column=4, sticky="w", padx=4, pady=3)
        ttk.Button(filters, text="Искать похоже", command=self.quick_search).grid(row=2, column=5, sticky="w", padx=4, pady=3)
        ttk.Button(filters, text="Создать pg_trgm", command=self.ensure_pg_trgm).grid(row=2, column=6, sticky="w", padx=4, pady=3)

        self.result = scrolledtext.ScrolledText(right, wrap=tk.NONE, font=("Menlo", 11), state=tk.DISABLED)
        self.result.pack(fill=tk.BOTH, expand=True)

        status = ttk.Label(right, textvariable=self.status_var, anchor="w")
        status.pack(fill=tk.X, pady=(5, 0))

    def add_button_group(self, parent, title, buttons):
        frame = ttk.LabelFrame(parent, text=title, padding=6)
        frame.pack(fill=tk.X, pady=4)
        for text, command in buttons:
            ttk.Button(frame, text=text, command=command).pack(fill=tk.X, pady=2)

    def set_status(self, text):
        self.status_var.set(text)
        self.root.update_idletasks()

    def get_limit(self):
        try:
            return max(1, min(5000, int(self.limit_var.get())))
        except Exception:
            self.limit_var.set("100")
            return 100

    def display(self, text):
        self.result.config(state=tk.NORMAL)
        self.result.delete("1.0", tk.END)
        self.result.insert(tk.END, text)
        self.result.config(state=tk.DISABLED)

    def format_table(self, rows, cols, title=""):
        self.last_rows = rows or []
        self.last_cols = cols or []
        if not rows:
            return (title + "\n\n" if title else "") + "Нет данных.\n"

        str_rows = [["" if v is None else str(v) for v in row] for row in rows]
        widths = [len(str(c)) for c in cols]
        for row in str_rows[:1000]:
            for i, val in enumerate(row):
                widths[i] = max(widths[i], len(val))
        widths = [min(w, 34) for w in widths]

        out = []
        if title:
            out.append(title)
            out.append("=" * len(title))
        top = "┌" + "┬".join("─" * (w + 2) for w in widths) + "┐"
        sep = "├" + "┼".join("─" * (w + 2) for w in widths) + "┤"
        bot = "└" + "┴".join("─" * (w + 2) for w in widths) + "┘"
        out.append(top)
        out.append("│" + "│".join(f" {str(cols[i])[:widths[i]].ljust(widths[i])} " for i in range(len(cols))) + "│")
        out.append(sep)
        for row in str_rows[:1000]:
            out.append("│" + "│".join(f" {row[i][:widths[i]].ljust(widths[i])} " for i in range(len(cols))) + "│")
        out.append(bot)
        out.append(f"\nВсего строк: {len(rows)}")
        if len(rows) > 1000:
            out.append("Показаны первые 1000 строк.")
        return "\n".join(out) + "\n"

    def execute(self, query, params=None, title="", fetch=True):
        if not self.conn:
            return "Нет подключения к БД.\n"
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params or [])
                if fetch and cur.description:
                    rows = cur.fetchall()
                    cols = [d[0] for d in cur.description]
                    self.conn.commit()
                    return self.format_table(rows, cols, title)
                self.conn.commit()
                self.last_rows = []
                self.last_cols = []
                return (title + "\n" if title else "") + "Выполнено успешно.\n"
        except Exception as e:
            self.conn.rollback()
            return f"Ошибка SQL: {e}\n"

    def execute_and_display(self, query, params=None, title="", status="Готово", fetch=True):
        self.set_status("Выполняю запрос...")
        result = self.execute(query, params=params, title=title, fetch=fetch)
        self.display(result)
        self.set_status(status)


    def get_similarity_threshold(self):
        """Возвращает безопасный порог схожести для pg_trgm."""
        try:
            value = float(str(self.similarity_var.get()).replace(",", "."))
            value = max(0.05, min(1.0, value))
            self.similarity_var.set(str(value))
            return value
        except Exception:
            self.similarity_var.set("0.3")
            return 0.3

    def ensure_pg_trgm(self, silent=False):
        """Создаёт расширение pg_trgm для триграммного поиска."""
        if not self.conn:
            if not silent:
                messagebox.showerror("Ошибка", "Нет подключения к БД")
            return False
        try:
            with self.conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
            self.conn.commit()
            if not silent:
                messagebox.showinfo("pg_trgm", "Расширение pg_trgm подключено.")
                self.set_status("pg_trgm подключено")
            return True
        except Exception as e:
            self.conn.rollback()
            if not silent:
                messagebox.showerror("pg_trgm", f"Не удалось подключить pg_trgm:\n{e}")
            return False

    # ------------------------- данные для подсказок -------------------------
    def load_autocomplete_data(self):
        self.autocomplete = {
            "таксопарк": [],
            "тип клиента": [],
            "район": [],
            "дата": [],
        }
        if not self.conn:
            return
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT название FROM ТАКСОПАРКИ ORDER BY название")
                self.autocomplete["таксопарк"] = [r[0] for r in cur.fetchall()]
                cur.execute("SELECT описание FROM КЛИЕНТЫ ORDER BY описание")
                self.autocomplete["тип клиента"] = [r[0] for r in cur.fetchall()]
                cur.execute("SELECT название FROM РАЙОНЫ ORDER BY название")
                self.autocomplete["район"] = [r[0] for r in cur.fetchall()]
            self.conn.commit()
        except Exception:
            self.conn.rollback()

    def on_filter_typing(self, event=None):
        """Оставлено для совместимости со старыми привязками. В новой версии подсказки не создают отдельное поле."""
        return

    def clear_filters(self):
        self.filter_field_var.set("без фильтра")
        self.filter_value_var.set("")
        self.search_var.set("")
        self.latest_rides()

    def build_ride_filter(self):
        field = self.filter_field_var.get().strip()
        value = self.filter_value_var.get().strip()
        if field == "без фильтра" or not value:
            return "", []

        like_value = f"%{value}%"
        text_mapping = {
            "таксопарк": ("t.название ILIKE %s", [like_value]),
            # водитель задаётся кодом (12) или частью taxi_id
            "водитель": ("(v.код::text = %s OR v.taxi_id ILIKE %s)", [value.lstrip("№ "), like_value]),
            "тип клиента": ("(k.тип ILIKE %s OR k.описание ILIKE %s)", [like_value, like_value]),
            "откуда": ("ro.название ILIKE %s", [like_value]),
            "куда": ("rk.название ILIKE %s", [like_value]),
        }
        if field in text_mapping:
            cond, params = text_mapping[field]
            return " AND " + cond, params

        if field == "дата":
            # Для даты можно вводить точную дату 2026-05-09 или часть даты/времени.
            if len(value) == 10 and value[4] == "-" and value[7] == "-":
                return " AND p.дата::date = %s", [value]
            return " AND CAST(p.дата AS TEXT) ILIKE %s", [like_value]

        numeric_mapping = {
            "стоимость >=": ("p.стоимость >= %s", float),
            "стоимость <=": ("p.стоимость <= %s", float),
            "расстояние >=": ("p.расстояние_км >= %s", float),
            "расстояние <=": ("p.расстояние_км <= %s", float),
            "время >=": ("p.время_мин >= %s", int),
            "время <=": ("p.время_мин <= %s", int),
        }
        if field in numeric_mapping:
            cond, caster = numeric_mapping[field]
            try:
                return " AND " + cond, [caster(value.replace(",", "."))]
            except Exception:
                messagebox.showerror("Ошибка фильтра", f"Для фильтра '{field}' нужно ввести число.")
                return " AND 1=0", []

        return "", []

    # ------------------------- просмотр и отчёты -------------------------
    def db_stats(self):
        query = """
            SELECT 'ТАКСОПАРКИ' AS таблица, COUNT(*) AS записей FROM ТАКСОПАРКИ
            UNION ALL SELECT 'ВОДИТЕЛИ', COUNT(*) FROM ВОДИТЕЛИ
            UNION ALL SELECT 'КЛИЕНТЫ', COUNT(*) FROM КЛИЕНТЫ
            UNION ALL SELECT 'РАЙОНЫ', COUNT(*) FROM РАЙОНЫ
            UNION ALL SELECT 'ПОЕЗДКИ', COUNT(*) FROM ПОЕЗДКИ
            UNION ALL SELECT 'СЕЗОН', COUNT(*) FROM СЕЗОН
            ORDER BY таблица
        """
        self.execute_and_display(query, title="Сводная статистика по таблицам", status="Статистика БД")

    def show_structure(self):
        query = """
            SELECT table_name AS таблица, column_name AS столбец, data_type AS тип
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name IN ('ТАКСОПАРКИ','ВОДИТЕЛИ','КЛИЕНТЫ','РАЙОНЫ','ПОЕЗДКИ','СЕЗОН')
            ORDER BY table_name, ordinal_position
        """
        self.execute_and_display(query, title="Структура БД", status="Структура БД")

    def show_tables_window(self):
        win = tk.Toplevel(self.root)
        win.title("Просмотр таблиц")
        win.geometry("360x360")
        win.transient(self.root)
        ttk.Label(win, text="Выберите таблицу:", font=("Arial", 12, "bold")).pack(pady=10)
        for table in self.TABLES:
            ttk.Button(win, text=table, command=lambda t=table: self.view_table(t)).pack(fill=tk.X, padx=20, pady=4)

    def view_table(self, table):
        if table not in self.TABLES:
            messagebox.showerror("Ошибка", "Неизвестная таблица")
            return
        if table == "ПОЕЗДКИ":
            query = f"""
    SELECT p.код_поездки, p.дата,
                       'Водитель №' || v.код AS водитель,
                       t.название AS таксопарк,
                       k.описание AS оплата,
                       ro.название AS откуда, rk.название AS куда,
                       p.расстояние_км, p.время_мин, p.стоимость, p.чаевые
                FROM ПОЕЗДКИ p
                JOIN ВОДИТЕЛИ v ON v.код = p.водитель
                JOIN КЛИЕНТЫ k ON k.код = p.клиент
                JOIN ТАКСОПАРКИ t ON t.код = p.таксопарк
                LEFT JOIN РАЙОНЫ ro ON ro.код = p.откуда
                LEFT JOIN РАЙОНЫ rk ON rk.код = p.куда
                ORDER BY p.дата DESC
                LIMIT {self.get_limit()}
            """
            title = "Таблица ПОЕЗДКИ с расшифровкой"
            self.execute_and_display(query, title=title, status=title)
        else:
            query = psql.SQL("SELECT * FROM {} ORDER BY 1 LIMIT %s").format(psql.Identifier(table))
            self.execute_and_display(query, params=[self.get_limit()], title=f"Таблица {table}", status=f"Таблица {table}")

    def latest_rides(self):
        limit = self.get_limit()
        cond, params = self.build_ride_filter()
        query = f"""
            SELECT p.код_поездки, p.дата,
                   'Водитель №' || v.код AS водитель,
                   t.название AS таксопарк,
                   k.описание AS оплата,
                   ro.название AS откуда, rk.название AS куда,
                   p.расстояние_км, p.время_мин, p.стоимость, p.чаевые
            FROM ПОЕЗДКИ p
            JOIN ВОДИТЕЛИ v ON v.код = p.водитель
            JOIN КЛИЕНТЫ k ON k.код = p.клиент
            JOIN ТАКСОПАРКИ t ON t.код = p.таксопарк
            LEFT JOIN РАЙОНЫ ro ON ro.код = p.откуда
            LEFT JOIN РАЙОНЫ rk ON rk.код = p.куда
            WHERE 1=1 {cond}
            ORDER BY p.дата DESC
            LIMIT %s
        """
        self.execute_and_display(query, params=params + [limit], title="Последние поездки", status="Последние поездки")

    def top_drivers(self):
        query = """
            SELECT v.код, 'Водитель №' || v.код AS водитель, v.taxi_id,
                   COUNT(p.код_поездки) AS поездок,
                   ROUND(COALESCE(SUM(p.стоимость),0), 2) AS выручка,
                   ROUND(COALESCE(AVG(p.стоимость),0), 2) AS средний_чек,
                   ROUND(COALESCE(SUM(p.чаевые),0), 2) AS чаевые
            FROM ВОДИТЕЛИ v
            LEFT JOIN ПОЕЗДКИ p ON p.водитель = v.код
            GROUP BY v.код
            ORDER BY выручка DESC, поездок DESC
            LIMIT %s
        """
        self.execute_and_display(query, [self.get_limit()], title="Топ водителей", status="Топ водителей")

    def top_clients(self):
        query = """
            SELECT k.код, k.тип, k.описание,
                   COUNT(p.код_поездки) AS поездок,
                   ROUND(COALESCE(SUM(p.стоимость),0), 2) AS сумма,
                   ROUND(COALESCE(AVG(p.стоимость),0), 2) AS средний_чек,
                   ROUND(COALESCE(AVG(p.чаевые),0), 2) AS средние_чаевые
            FROM КЛИЕНТЫ k
            LEFT JOIN ПОЕЗДКИ p ON p.клиент = k.код
            GROUP BY k.код
            ORDER BY сумма DESC, поездок DESC
            LIMIT %s
        """
        self.execute_and_display(query, [self.get_limit()], title="Типы клиентов (способы оплаты)", status="Типы клиентов")

    def revenue_by_company(self):
        query = """
            SELECT t.название AS таксопарк,
                   COUNT(p.код_поездки) AS поездок,
                   ROUND(SUM(p.стоимость), 2) AS выручка,
                   ROUND(AVG(p.стоимость), 2) AS средний_чек,
                   ROUND(AVG(p.расстояние_км), 2) AS среднее_расстояние,
                   ROUND(AVG(p.время_мин), 2) AS среднее_время
            FROM ПОЕЗДКИ p
            JOIN ТАКСОПАРКИ t ON t.код = p.таксопарк
            GROUP BY t.название
            ORDER BY выручка DESC
        """
        self.execute_and_display(query, title="Доход по таксопаркам", status="Доход по таксопаркам")

    def company_stats(self):
        query = """
            SELECT t.код, t.название,
                   COUNT(DISTINCT p.водитель) AS водителей,
                   COUNT(p.код_поездки) AS поездок,
                   ROUND(COALESCE(SUM(p.стоимость),0), 2) AS выручка,
                   ROUND(COALESCE(AVG(p.расстояние_км),0), 2) AS средний_км
            FROM ТАКСОПАРКИ t
            LEFT JOIN ПОЕЗДКИ p ON p.таксопарк = t.код
            GROUP BY t.код, t.название
            ORDER BY выручка DESC, поездок DESC
            LIMIT %s
        """
        self.execute_and_display(query, [self.get_limit()], title="Статистика таксопарков", status="Статистика таксопарков")

    def season_stats(self):
        query = """
            SELECT s.сезон,
                   COUNT(p.код_поездки) AS поездок,
                   ROUND(SUM(p.стоимость), 2) AS выручка,
                   ROUND(AVG(p.стоимость), 2) AS средний_чек,
                   ROUND(AVG(p.расстояние_км), 2) AS средний_км
            FROM ПОЕЗДКИ p
            JOIN СЕЗОН s ON s.месяц = EXTRACT(MONTH FROM p.дата)::int
            GROUP BY s.сезон, s.порядок
            ORDER BY s.порядок
        """
        self.execute_and_display(query, title="Статистика по сезонам", status="Сезоны")

    def fare_distribution(self):
        query = """
            SELECT
                CASE
                    WHEN стоимость < 10 THEN 'до $10'
                    WHEN стоимость < 25 THEN '$10-24.99'
                    WHEN стоимость < 50 THEN '$25-49.99'
                    ELSE '$50+'
                END AS диапазон,
                COUNT(*) AS поездок,
                ROUND(AVG(стоимость), 2) AS средняя_стоимость
            FROM ПОЕЗДКИ
            GROUP BY диапазон
            ORDER BY MIN(стоимость)
        """
        self.execute_and_display(query, title="Распределение стоимости поездок", status="Распределение стоимости")

    def average_ride_report(self):
        query = """
            SELECT COUNT(*) AS поездок,
                   ROUND(AVG(расстояние_км), 2) AS среднее_расстояние_км,
                   ROUND(AVG(время_мин), 2) AS среднее_время_мин,
                   ROUND(AVG(стоимость), 2) AS средняя_стоимость,
                   ROUND(SUM(стоимость), 2) AS общая_выручка
            FROM ПОЕЗДКИ
        """
        self.execute_and_display(query, title="Средние показатели поездок", status="Средняя поездка")

    def quick_search(self):
        """Триграммный поиск по основным текстовым полям базы TAXI."""
        text = self.search_var.get().strip()
        if not text:
            messagebox.showinfo("Поиск", "Введите текст для триграммного поиска")
            return

        if not self.ensure_pg_trgm(silent=True):
            messagebox.showerror(
                "Триграммный поиск",
                "Для триграммного поиска нужно расширение pg_trgm. "
                "Нажмите кнопку 'Создать pg_trgm' или выполните CREATE EXTENSION IF NOT EXISTS pg_trgm."
            )
            return

        threshold = self.get_similarity_threshold()
        like = f"%{text}%"
        term = text.lower()

        query = """
            WITH q AS (
                SELECT %s::text AS term, %s::text AS like_term, %s::float AS threshold
            )
            SELECT * FROM (
                SELECT
                    'таксопарк' AS тип,
                    t.код::text AS код,
                    t.название AS найдено,
                    ROUND(similarity(LOWER(t.название), q.term)::numeric, 3) AS схожесть
                FROM ТАКСОПАРКИ t CROSS JOIN q
                WHERE similarity(LOWER(t.название), q.term) >= q.threshold
                   OR t.название ILIKE q.like_term

                UNION ALL

                SELECT
                    'район' AS тип,
                    r.код::text AS код,
                    r.название AS найдено,
                    ROUND(similarity(LOWER(r.название), q.term)::numeric, 3) AS схожесть
                FROM РАЙОНЫ r CROSS JOIN q
                WHERE similarity(LOWER(r.название), q.term) >= q.threshold
                   OR r.название ILIKE q.like_term

                UNION ALL

                SELECT
                    'тип клиента' AS тип,
                    k.код::text AS код,
                    k.описание || ' (' || k.тип || ')' AS найдено,
                    ROUND(GREATEST(similarity(LOWER(k.описание), q.term),
                                   similarity(LOWER(k.тип), q.term))::numeric, 3) AS схожесть
                FROM КЛИЕНТЫ k CROSS JOIN q
                WHERE GREATEST(similarity(LOWER(k.описание), q.term),
                               similarity(LOWER(k.тип), q.term)) >= q.threshold
                   OR k.описание ILIKE q.like_term
                   OR k.тип ILIKE q.like_term

                UNION ALL

                SELECT
                    'водитель' AS тип,
                    v.код::text AS код,
                    'Водитель №' || v.код || ' (' || v.taxi_id || ')' AS найдено,
                    ROUND(similarity(LOWER(v.taxi_id), q.term)::numeric, 3) AS схожесть
                FROM ВОДИТЕЛИ v CROSS JOIN q
                WHERE v.taxi_id ILIKE q.like_term
                   OR v.код::text = q.term
            ) found
            ORDER BY схожесть DESC, тип, найдено
            LIMIT %s
        """
        params = [term, like, threshold, self.get_limit()]
        self.execute_and_display(
            query,
            params,
            title=f"Триграммный поиск: {text} | порог {threshold}",
            status="Триграммный поиск"
        )

    # ------------------------- графики -------------------------
    def chart_monthly_revenue(self):
        if not self.conn:
            messagebox.showerror("Ошибка", "Нет подключения к БД")
            return
        query = """
            SELECT DATE_TRUNC('month', дата)::date AS месяц,
                   COUNT(*) AS поездок,
                   SUM(стоимость) AS выручка
            FROM ПОЕЗДКИ
            GROUP BY DATE_TRUNC('month', дата)
            ORDER BY месяц
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Ошибка", str(e))
            return
        if not rows:
            messagebox.showinfo("Нет данных", "Нет данных для графика")
            return
        months = [r[0] for r in rows]
        revenue = [float(r[2]) for r in rows]
        self.open_line_chart(months, revenue, "Динамика выручки по месяцам", "Месяц", "Выручка, $")

    def chart_payment_pie(self):
        if not self.conn:
            messagebox.showerror("Ошибка", "Нет подключения к БД")
            return
        query = """
            SELECT k.описание, COUNT(*) AS поездок
            FROM ПОЕЗДКИ p
            JOIN КЛИЕНТЫ k ON k.код = p.клиент
            GROUP BY k.описание
            ORDER BY поездок DESC
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Ошибка", str(e))
            return
        if not rows:
            messagebox.showinfo("Нет данных", "Нет данных для диаграммы")
            return
        labels = [r[0] for r in rows]
        sizes = [int(r[1]) for r in rows]
        self.open_pie_chart(labels, sizes, "Доля поездок по способам оплаты")

    def open_line_chart(self, x, y, title, xlabel, ylabel):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("850x540")
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(x, y, marker="o", linewidth=2)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)
        fig.autofmt_xdate()
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def open_pie_chart(self, labels, sizes, title):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("700x600")
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.pie(sizes, labels=labels, autopct="%1.1f%%")
        ax.set_title(title)
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # ------------------------- CRUD -------------------------
    def ask_fields(self, title, fields):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("430x" + str(90 + len(fields) * 38))
        win.transient(self.root)
        win.grab_set()
        values = {}
        entries = {}
        for i, (key, label, default) in enumerate(fields):
            ttk.Label(win, text=label).grid(row=i, column=0, sticky="w", padx=10, pady=6)
            var = tk.StringVar(value=str(default or ""))
            entry = ttk.Entry(win, textvariable=var, width=34)
            entry.grid(row=i, column=1, sticky="w", padx=10, pady=6)
            values[key] = var
            entries[key] = entry
        result = {"ok": False}

        def ok():
            result["ok"] = True
            win.destroy()

        def cancel():
            win.destroy()

        btns = ttk.Frame(win)
        btns.grid(row=len(fields), column=0, columnspan=2, pady=12)
        ttk.Button(btns, text="OK", command=ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btns, text="Отмена", command=cancel).pack(side=tk.LEFT, padx=5)
        if entries:
            next(iter(entries.values())).focus_set()
        self.root.wait_window(win)
        if not result["ok"]:
            return None
        return {k: v.get().strip() for k, v in values.items()}

    def add_record_window(self):
        table = simpledialog.askstring("Добавление", "Что добавить? company / driver / client / ride")
        if not table:
            return
        table = table.lower().strip()
        if table in ["company", "таксопарк"]:
            self.add_company()
        elif table in ["driver", "водитель"]:
            self.add_driver()
        elif table in ["client", "клиент"]:
            self.add_client()
        elif table in ["ride", "поездка"]:
            self.add_ride()
        else:
            messagebox.showerror("Ошибка", "Введите: company, driver, client или ride")

    def add_company(self):
        data = self.ask_fields("Добавить таксопарк", [("name", "Название", "Новый таксопарк")])
        if not data:
            return
        self.execute_and_display("INSERT INTO ТАКСОПАРКИ (название) VALUES (%s)", [data["name"]],
                                 title="Добавление таксопарка", status="Таксопарк добавлен", fetch=False)
        self.load_autocomplete_data()

    def add_driver(self):
        data = self.ask_fields("Добавить водителя", [("taxi_id", "taxi_id (до 16 символов)", "manual00000001")])
        if not data:
            return
        self.execute_and_display("INSERT INTO ВОДИТЕЛИ (taxi_id) VALUES (%s)", [data["taxi_id"]],
                                 title="Добавление водителя", status="Водитель добавлен", fetch=False)

    def add_client(self):
        data = self.ask_fields("Добавить тип клиента", [
            ("type", "Тип (как в данных города)", "Voucher"),
            ("desc", "Описание", "Ваучер"),
        ])
        if not data:
            return
        self.execute_and_display("INSERT INTO КЛИЕНТЫ (тип, описание) VALUES (%s, %s)", [data["type"], data["desc"]],
                                 title="Добавление типа клиента", status="Тип клиента добавлен", fetch=False)
        self.load_autocomplete_data()

    def add_ride(self):
        data = self.ask_fields("Добавить поездку", [
            ("driver", "Код водителя", "1"),
            ("client", "Код типа клиента", "1"),
            ("company", "Код таксопарка", "1"),
            ("from", "Код района посадки (1-77, можно пусто)", "32"),
            ("to", "Код района высадки (1-77, можно пусто)", "8"),
            ("km", "Расстояние км", "5"),
            ("min", "Время мин", "15"),
            ("cost", "Стоимость $", "15"),
            ("tips", "Чаевые $", "0"),
        ])
        if not data:
            return
        # введённые вручную поездки получают trip_id с префиксом manual
        query = """
            INSERT INTO ПОЕЗДКИ (trip_id, дата, водитель, клиент, таксопарк, откуда, куда,
                                 расстояние_км, время_мин, стоимость, чаевые)
            VALUES ('manual' || LPAD((SELECT COUNT(*) + 1 FROM ПОЕЗДКИ)::text, 10, '0'), NOW(),
                    %s::int, %s::int, %s::int, NULLIF(%s,'')::int, NULLIF(%s,'')::int,
                    %s::numeric, %s::int, %s::numeric, %s::numeric)
        """
        params = [data["driver"], data["client"], data["company"], data["from"], data["to"],
                  data["km"], data["min"], data["cost"], data["tips"]]
        self.execute_and_display(query, params, title="Добавление поездки", status="Поездка добавлена", fetch=False)

    def edit_record_window(self):
        action = simpledialog.askstring("Редактирование", "Что изменить? company_name / client_description / ride_tips / ride_company")
        if not action:
            return
        action = action.lower().strip()
        if action == "company_name":
            self.update_company_name()
        elif action == "client_description":
            self.update_client_description()
        elif action == "ride_tips":
            self.update_ride_tips()
        elif action == "ride_company":
            self.update_ride_company()
        else:
            messagebox.showerror("Ошибка", "Варианты: company_name, client_description, ride_tips, ride_company")

    def update_company_name(self):
        data = self.ask_fields("Переименовать таксопарк", [("id", "Код таксопарка", "1"), ("name", "Новое название", "")])
        if data:
            self.execute_and_display("UPDATE ТАКСОПАРКИ SET название=%s WHERE код=%s::int", [data["name"], data["id"]],
                                     title="Переименование таксопарка", status="Таксопарк переименован", fetch=False)
            self.load_autocomplete_data()

    def update_client_description(self):
        data = self.ask_fields("Изменить описание типа клиента", [("id", "Код типа клиента", "1"), ("desc", "Новое описание", "")])
        if data:
            self.execute_and_display("UPDATE КЛИЕНТЫ SET описание=%s WHERE код=%s::int", [data["desc"], data["id"]],
                                     title="Изменение описания типа клиента", status="Описание изменено", fetch=False)
            self.load_autocomplete_data()

    def update_ride_tips(self):
        data = self.ask_fields("Изменить чаевые поездки", [("id", "Код поездки", "1"), ("tips", "Чаевые $", "2.00")])
        if data:
            self.execute_and_display("UPDATE ПОЕЗДКИ SET чаевые=%s::numeric WHERE код_поездки=%s::int", [data["tips"], data["id"]],
                                     title="Изменение чаевых", status="Чаевые изменены", fetch=False)

    def update_ride_company(self):
        data = self.ask_fields("Сменить таксопарк поездки", [("id", "Код поездки", "1"), ("company", "Код таксопарка", "1")])
        if data:
            self.execute_and_display("UPDATE ПОЕЗДКИ SET таксопарк=%s::int WHERE код_поездки=%s::int", [data["company"], data["id"]],
                                     title="Смена таксопарка поездки", status="Таксопарк поездки изменён", fetch=False)

    def delete_record_window(self):
        table = simpledialog.askstring("Удаление", "Что удалить? company / driver / client / ride")
        if not table:
            return
        table = table.lower().strip()
        code = simpledialog.askinteger("Код", "Введите код записи")
        if not code:
            return
        if not messagebox.askyesno("Подтверждение", f"Удалить {table} с кодом {code} вместе с его поездками?"):
            return
        if table in ["ride", "поездка"]:
            self.execute_and_display("DELETE FROM ПОЕЗДКИ WHERE код_поездки=%s", [code], title="Удаление поездки", status="Удалено", fetch=False)
        elif table in ["client", "клиент"]:
            self.execute_and_display("DELETE FROM ПОЕЗДКИ WHERE клиент=%s; DELETE FROM КЛИЕНТЫ WHERE код=%s", [code, code], title="Удаление типа клиента", status="Удалено", fetch=False)
        elif table in ["driver", "водитель"]:
            self.execute_and_display("DELETE FROM ПОЕЗДКИ WHERE водитель=%s; DELETE FROM ВОДИТЕЛИ WHERE код=%s", [code, code], title="Удаление водителя", status="Удалено", fetch=False)
        elif table in ["company", "таксопарк"]:
            self.execute_and_display("DELETE FROM ПОЕЗДКИ WHERE таксопарк=%s; DELETE FROM ТАКСОПАРКИ WHERE код=%s", [code, code], title="Удаление таксопарка", status="Удалено", fetch=False)
        else:
            messagebox.showerror("Ошибка", "Варианты: company, driver, client, ride")

    def update_before_after(self):
        data = self.ask_fields("UPDATE до/после", [("id", "Код поездки", "1"), ("tips", "Новые чаевые $", "3.00")])
        if not data:
            return
        ride_id = data["id"]
        before = self.execute("SELECT * FROM v_rides_user WHERE код_поездки=%s::int", [ride_id], title="ДО UPDATE")
        update = self.execute("UPDATE ПОЕЗДКИ SET чаевые=%s::numeric WHERE код_поездки=%s::int", [data["tips"], ride_id], title="UPDATE", fetch=False)
        after = self.execute("SELECT * FROM v_rides_user WHERE код_поездки=%s::int", [ride_id], title="ПОСЛЕ UPDATE")
        self.display(before + "\n" + update + "\n" + after)
        self.set_status("UPDATE до/после")

    def delete_before_after(self):
        code = simpledialog.askinteger("DELETE до/после", "Код поездки для удаления")
        if not code:
            return
        if not messagebox.askyesno("Подтверждение", f"Удалить поездку код {code}?"):
            return
        before = self.execute("SELECT * FROM ПОЕЗДКИ WHERE код_поездки=%s", [code], title="ДО DELETE")
        deletion = self.execute("DELETE FROM ПОЕЗДКИ WHERE код_поездки=%s", [code], title="DELETE", fetch=False)
        after = self.execute("SELECT * FROM ПОЕЗДКИ WHERE код_поездки=%s", [code], title="ПОСЛЕ DELETE")
        self.display(before + "\n" + deletion + "\n" + after)
        self.set_status("DELETE до/после")



    # ------------------------- расширенные отчёты и полный функционал -------------------------
    def fetch_rows(self, query, params=None):
        """Возвращает rows, cols для внутренних расчётов."""
        if not self.conn:
            return [], []
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params or [])
                if cur.description:
                    rows = cur.fetchall()
                    cols = [d[0] for d in cur.description]
                else:
                    rows, cols = [], []
            self.conn.commit()
            return rows, cols
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Ошибка SQL", str(e))
            return [], []

    def dashboard(self):
        """Главная сводка: сколько данных, выручка, средний чек, лучшие объекты."""
        queries = [
            ("Всего поездок", "SELECT COUNT(*) FROM ПОЕЗДКИ"),
            ("Общая выручка", "SELECT ROUND(COALESCE(SUM(стоимость),0), 2) FROM ПОЕЗДКИ"),
            ("Средний чек", "SELECT ROUND(COALESCE(AVG(стоимость),0), 2) FROM ПОЕЗДКИ"),
            ("Средняя дистанция", "SELECT ROUND(COALESCE(AVG(расстояние_км),0), 2) FROM ПОЕЗДКИ"),
            ("Период данных", "SELECT MIN(дата)::date || ' — ' || MAX(дата)::date FROM ПОЕЗДКИ"),
            ("Водителей (такси)", "SELECT COUNT(*) FROM ВОДИТЕЛИ"),
            ("Таксопарков", "SELECT COUNT(*) FROM ТАКСОПАРКИ"),
            ("Типов клиентов", "SELECT COUNT(*) FROM КЛИЕНТЫ"),
        ]
        lines = ["Дашборд TAXI — реальные поездки такси Чикаго, суммы в $", "=" * 56, ""]
        for label, query in queries:
            rows, _ = self.fetch_rows(query)
            value = rows[0][0] if rows else "—"
            lines.append(f"{label}: {value}")

        blocks = [
            ("\nТоп-3 таксопарка по выручке", """
                SELECT t.название AS таксопарк, COUNT(*) AS поездок, ROUND(SUM(p.стоимость),2) AS выручка
                FROM ПОЕЗДКИ p JOIN ТАКСОПАРКИ t ON t.код = p.таксопарк
                GROUP BY t.название
                ORDER BY выручка DESC
                LIMIT 3
            """),
            ("\nТоп-5 водителей по выручке", """
                SELECT 'Водитель №' || v.код AS водитель,
                       COUNT(p.код_поездки) AS поездок,
                       ROUND(COALESCE(SUM(p.стоимость),0),2) AS выручка
                FROM ВОДИТЕЛИ v JOIN ПОЕЗДКИ p ON p.водитель = v.код
                GROUP BY v.код
                ORDER BY выручка DESC
                LIMIT 5
            """),
            ("\nПоследние 5 поездок", """
                SELECT p.код_поездки, p.дата, t.название AS таксопарк,
                       'Водитель №' || p.водитель AS водитель, p.стоимость
                FROM ПОЕЗДКИ p
                JOIN ТАКСОПАРКИ t ON t.код = p.таксопарк
                ORDER BY p.дата DESC
                LIMIT 5
            """),
        ]
        text = "\n".join(lines) + "\n"
        for title, query in blocks:
            rows, cols = self.fetch_rows(query)
            text += "\n" + self.format_table(rows, cols, title)
        self.display(text)
        self.set_status("Дашборд")

    def period_report(self):
        data = self.ask_fields("Отчёт за период", [
            ("date_from", "Дата начала YYYY-MM-DD", "2026-01-01"),
            ("date_to", "Дата конца YYYY-MM-DD", "2026-12-31"),
        ])
        if not data:
            return
        query = """
            SELECT DATE(p.дата) AS дата,
                   COUNT(*) AS поездок,
                   ROUND(SUM(p.стоимость),2) AS выручка,
                   ROUND(AVG(p.стоимость),2) AS средний_чек,
                   ROUND(SUM(p.расстояние_км),2) AS км_всего,
                   ROUND(AVG(p.расстояние_км),2) AS средняя_дистанция
            FROM ПОЕЗДКИ p
            WHERE DATE(p.дата) BETWEEN %s::date AND %s::date
            GROUP BY DATE(p.дата)
            ORDER BY дата
        """
        self.execute_and_display(query, [data["date_from"], data["date_to"]],
                                 title="Отчёт по датам за период", status="Отчёт за период")

    def weekday_report(self):
        query = """
            SELECT CASE EXTRACT(ISODOW FROM p.дата)
                    WHEN 1 THEN 'Понедельник'
                    WHEN 2 THEN 'Вторник'
                    WHEN 3 THEN 'Среда'
                    WHEN 4 THEN 'Четверг'
                    WHEN 5 THEN 'Пятница'
                    WHEN 6 THEN 'Суббота'
                    WHEN 7 THEN 'Воскресенье'
                   END AS день_недели,
                   COUNT(*) AS поездок,
                   ROUND(SUM(p.стоимость),2) AS выручка,
                   ROUND(AVG(p.стоимость),2) AS средний_чек
            FROM ПОЕЗДКИ p
            GROUP BY EXTRACT(ISODOW FROM p.дата)
            ORDER BY EXTRACT(ISODOW FROM p.дата)
        """
        self.execute_and_display(query, title="Аналитика по дням недели", status="Дни недели")

    def hour_report(self):
        query = """
            SELECT EXTRACT(HOUR FROM p.дата)::int AS час,
                   COUNT(*) AS поездок,
                   ROUND(SUM(p.стоимость),2) AS выручка,
                   ROUND(AVG(p.стоимость),2) AS средний_чек
            FROM ПОЕЗДКИ p
            GROUP BY EXTRACT(HOUR FROM p.дата)
            ORDER BY час
        """
        self.execute_and_display(query, title="Аналитика по часам суток", status="Часы суток")

    def expensive_rides(self):
        query = """
            SELECT * FROM v_rides_user
            ORDER BY стоимость DESC
            LIMIT %s
        """
        self.execute_and_display(query, [self.get_limit()], title="Самые дорогие поездки", status="Дорогие поездки")

    def long_rides(self):
        query = """
            SELECT * FROM v_rides_user
            ORDER BY расстояние_км DESC
            LIMIT %s
        """
        self.execute_and_display(query, [self.get_limit()], title="Самые длинные поездки", status="Длинные поездки")

    def inactive_drivers(self):
        query = """
            SELECT v.код, 'Водитель №' || v.код AS водитель, v.taxi_id
            FROM ВОДИТЕЛИ v
            LEFT JOIN ПОЕЗДКИ p ON p.водитель = v.код
            WHERE p.код_поездки IS NULL
            ORDER BY v.код
        """
        self.execute_and_display(query, title="Водители без поездок", status="Неактивные водители")

    def inactive_companies(self):
        query = """
            SELECT t.код, t.название
            FROM ТАКСОПАРКИ t
            LEFT JOIN ПОЕЗДКИ p ON p.таксопарк = t.код
            WHERE p.код_поездки IS NULL
            ORDER BY t.код
        """
        self.execute_and_display(query, title="Таксопарки без поездок", status="Таксопарки без поездок")

    def data_quality_check(self):
        query = """
            SELECT 'Поездки без района посадки (за городом)' AS проверка, COUNT(*) AS найдено FROM ПОЕЗДКИ WHERE откуда IS NULL
            UNION ALL SELECT 'Поездки без района высадки (за городом)', COUNT(*) FROM ПОЕЗДКИ WHERE куда IS NULL
            UNION ALL SELECT 'Окончание раньше начала', COUNT(*) FROM ПОЕЗДКИ WHERE окончание < дата
            UNION ALL SELECT 'Чаевые больше стоимости', COUNT(*) FROM ПОЕЗДКИ WHERE чаевые > стоимость
            UNION ALL SELECT 'Скорость выше 120 км/ч', COUNT(*) FROM ПОЕЗДКИ WHERE расстояние_км / (время_мин / 60.0) > 120
            UNION ALL SELECT 'Водители без поездок', COUNT(*) FROM ВОДИТЕЛИ v WHERE NOT EXISTS (SELECT 1 FROM ПОЕЗДКИ p WHERE p.водитель = v.код)
            UNION ALL SELECT 'Районы без поездок', COUNT(*) FROM РАЙОНЫ r WHERE NOT EXISTS (SELECT 1 FROM ПОЕЗДКИ p WHERE p.откуда = r.код OR p.куда = r.код)
        """
        self.execute_and_display(query, title="Проверка качества данных", status="Проверка связей")

    def chart_driver_revenue(self):
        query = """
            SELECT 'Водитель №' || v.код AS водитель,
                   ROUND(SUM(p.стоимость),2) AS выручка
            FROM ВОДИТЕЛИ v
            JOIN ПОЕЗДКИ p ON p.водитель = v.код
            GROUP BY v.код
            ORDER BY выручка DESC
            LIMIT 10
        """
        rows, _ = self.fetch_rows(query)
        if not rows:
            messagebox.showinfo("График", "Нет данных")
            return
        labels = [r[0] for r in rows]
        values = [float(r[1] or 0) for r in rows]
        self.open_bar_chart(labels, values, "Топ-10 водителей по выручке", "Водитель", "Выручка, $")

    def chart_weekday_revenue(self):
        query = """
            SELECT CASE EXTRACT(ISODOW FROM дата)
                    WHEN 1 THEN 'Пн' WHEN 2 THEN 'Вт' WHEN 3 THEN 'Ср' WHEN 4 THEN 'Чт'
                    WHEN 5 THEN 'Пт' WHEN 6 THEN 'Сб' WHEN 7 THEN 'Вс'
                   END AS день,
                   ROUND(SUM(стоимость),2) AS выручка,
                   EXTRACT(ISODOW FROM дата) AS n
            FROM ПОЕЗДКИ
            GROUP BY EXTRACT(ISODOW FROM дата)
            ORDER BY n
        """
        rows, _ = self.fetch_rows(query)
        if not rows:
            messagebox.showinfo("График", "Нет данных")
            return
        labels = [r[0] for r in rows]
        values = [float(r[1] or 0) for r in rows]
        self.open_bar_chart(labels, values, "Выручка по дням недели", "День недели", "Выручка, $")

    def open_bar_chart(self, labels, values, title, xlabel, ylabel):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("900x560")
        fig, ax = plt.subplots(figsize=(9, 5.2))
        ax.bar(labels, values)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True, axis="y", alpha=0.3)
        plt.xticks(rotation=35, ha="right")
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.set_status(title)

    def edit_any_record(self):
        table = simpledialog.askstring("Полное редактирование", "Таблица: ТАКСОПАРКИ / ВОДИТЕЛИ / КЛИЕНТЫ / РАЙОНЫ / ПОЕЗДКИ")
        if not table:
            return
        table = table.strip().upper()
        if table not in self.TABLES:
            messagebox.showerror("Ошибка", "Такой таблицы нет в списке GUI")
            return
        pk = {"ПОЕЗДКИ": "код_поездки", "СЕЗОН": "месяц"}.get(table, "код")
        code = simpledialog.askinteger("Код записи", f"Введите {pk}")
        if not code:
            return
        rows, cols = self.fetch_rows(psql.SQL("SELECT * FROM {} WHERE {} = %s").format(psql.Identifier(table), psql.Identifier(pk)), [code])
        if not rows:
            messagebox.showinfo("Редактирование", "Запись не найдена")
            return
        current = dict(zip(cols, rows[0]))
        editable = [c for c in cols if c != pk]
        fields = [(c, c, "" if current[c] is None else str(current[c])) for c in editable]
        data = self.ask_fields(f"Редактирование {table}", fields)
        if not data:
            return
        assignments = [psql.SQL("{} = %s").format(psql.Identifier(c)) for c in editable]
        query = psql.SQL("UPDATE {} SET {} WHERE {} = %s").format(
            psql.Identifier(table), psql.SQL(", ").join(assignments), psql.Identifier(pk)
        )
        params = [data[c] if data[c] != "" else None for c in editable] + [code]
        self.execute_and_display(query, params, title=f"Запись {table} обновлена", status="Полное редактирование", fetch=False)
        self.view_table(table)
        self.load_autocomplete_data()

    def create_views(self):
        query = """
            CREATE OR REPLACE VIEW taxi_full_rides AS
            SELECT p.код_поездки, p.дата,
                   'Водитель №' || v.код AS водитель,
                   t.название AS таксопарк,
                   k.описание AS оплата,
                   ro.название AS откуда, rk.название AS куда,
                   p.расстояние_км, p.время_мин, p.стоимость, p.чаевые
            FROM ПОЕЗДКИ p
            JOIN ВОДИТЕЛИ v ON v.код = p.водитель
            JOIN КЛИЕНТЫ k ON k.код = p.клиент
            JOIN ТАКСОПАРКИ t ON t.код = p.таксопарк
            LEFT JOIN РАЙОНЫ ro ON ro.код = p.откуда
            LEFT JOIN РАЙОНЫ rk ON rk.код = p.куда;

            CREATE OR REPLACE VIEW taxi_driver_report AS
            SELECT v.код, 'Водитель №' || v.код AS водитель, v.taxi_id,
                   COUNT(p.код_поездки) AS поездок,
                   ROUND(COALESCE(SUM(p.стоимость),0),2) AS выручка,
                   ROUND(COALESCE(AVG(p.стоимость),0),2) AS средний_чек
            FROM ВОДИТЕЛИ v
            LEFT JOIN ПОЕЗДКИ p ON p.водитель = v.код
            GROUP BY v.код;

            CREATE OR REPLACE VIEW taxi_client_report AS
            SELECT k.код, k.тип, k.описание,
                   COUNT(p.код_поездки) AS поездок,
                   ROUND(COALESCE(SUM(p.стоимость),0),2) AS сумма,
                   ROUND(COALESCE(AVG(p.чаевые),0),2) AS средние_чаевые
            FROM КЛИЕНТЫ k
            LEFT JOIN ПОЕЗДКИ p ON p.клиент = k.код
            GROUP BY k.код;
        """
        self.execute_and_display(query, title="Представления созданы", status="Views созданы", fetch=False)

    def check_views(self):
        query = """
            SELECT 'taxi_full_rides' AS view_name, COUNT(*) AS строк FROM taxi_full_rides
            UNION ALL SELECT 'taxi_driver_report', COUNT(*) FROM taxi_driver_report
            UNION ALL SELECT 'taxi_client_report', COUNT(*) FROM taxi_client_report
        """
        self.execute_and_display(query, title="Проверка представлений", status="Views проверены")

    def create_functions(self):
        query = """
            CREATE OR REPLACE FUNCTION taxi_driver_revenue(driver_id integer)
            RETURNS numeric AS $$
                SELECT ROUND(COALESCE(SUM(стоимость),0),2)
                FROM ПОЕЗДКИ
                WHERE водитель = driver_id;
            $$ LANGUAGE SQL;

            CREATE OR REPLACE FUNCTION taxi_client_spent(client_id integer)
            RETURNS numeric AS $$
                SELECT ROUND(COALESCE(SUM(стоимость),0),2)
                FROM ПОЕЗДКИ
                WHERE клиент = client_id;
            $$ LANGUAGE SQL;

            -- ожидаемая стоимость по реальным поездкам таксопарка: средняя цена километра и минуты
            CREATE OR REPLACE FUNCTION taxi_estimate_price(company text, km numeric, minutes integer)
            RETURNS numeric AS $$
                SELECT ROUND(AVG(p.стоимость / p.расстояние_км) * km * 0.5
                           + AVG(p.стоимость / p.время_мин) * minutes * 0.5, 2)
                FROM ПОЕЗДКИ p
                JOIN ТАКСОПАРКИ t ON t.код = p.таксопарк
                WHERE t.название ILIKE '%%' || company || '%%'  -- %% из-за подстановки параметров psycopg2
                  AND p.расстояние_км >= 1;
            $$ LANGUAGE SQL;
        """
        self.execute_and_display(query, title="SQL-функции созданы", status="Функции созданы", fetch=False)

    def functions_demo(self):
        data = self.ask_fields("Демо функций", [
            ("driver", "Код водителя", "1"),
            ("client", "Код типа клиента", "1"),
            ("company", "Таксопарк (часть названия)", "Flash"),
            ("km", "Километры", "10"),
            ("minutes", "Минуты", "25"),
        ])
        if not data:
            return
        query = """
            SELECT taxi_driver_revenue(%s::int) AS выручка_водителя,
                   taxi_client_spent(%s::int) AS сумма_типа_клиента,
                   taxi_estimate_price(%s, %s::numeric, %s::int) AS оценка_стоимости
        """
        self.execute_and_display(query, [data["driver"], data["client"], data["company"], data["km"], data["minutes"]],
                                 title="Демонстрация SQL-функций", status="Демо функций")

    def archive_old_rides(self):
        years = simpledialog.askinteger("Архивация", "Архивировать поездки старше N лет", initialvalue=3, minvalue=1, maxvalue=100)
        if not years:
            return
        if not messagebox.askyesno("Подтверждение", f"Перенести в архив поездки старше {years} лет?"):
            return
        query = """
            CREATE TABLE IF NOT EXISTS ПОЕЗДКИ_АРХИВ (LIKE ПОЕЗДКИ INCLUDING ALL);

            INSERT INTO ПОЕЗДКИ_АРХИВ
            SELECT * FROM ПОЕЗДКИ
            WHERE дата < CURRENT_DATE - make_interval(years => %s::int)
            ON CONFLICT (код_поездки) DO NOTHING;

            DELETE FROM ПОЕЗДКИ
            WHERE дата < CURRENT_DATE - make_interval(years => %s::int);
        """
        self.execute_and_display(query, [years, years], title="Архивация старых поездок", status="Архивация выполнена", fetch=False)

    # ------------------------- экспорт, бэкап, SQL -------------------------
    def export_current_csv(self):
        if not self.last_cols:
            messagebox.showinfo("Экспорт", "Сначала выполните отчёт или откройте таблицу")
            return
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not filename:
            return
        try:
            with open(filename, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(self.last_cols)
                writer.writerows(self.last_rows)
            messagebox.showinfo("Экспорт", f"Сохранено: {filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def export_all_tables_csv(self):
        directory = filedialog.askdirectory(title="Куда сохранить CSV-файлы")
        if not directory:
            return
        if not self.conn:
            messagebox.showerror("Ошибка", "Нет подключения к БД")
            return
        saved = 0
        try:
            for table in self.TABLES:
                with self.conn.cursor() as cur:
                    cur.execute(psql.SQL("SELECT * FROM {}").format(psql.Identifier(table)))
                    rows = cur.fetchall()
                    cols = [d[0] for d in cur.description]
                out_path = Path(directory) / f"{table}.csv"
                with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerow(cols)
                    writer.writerows(rows)
                saved += 1
            self.conn.commit()
            messagebox.showinfo("Экспорт", f"Экспортировано таблиц: {saved}")
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Ошибка", str(e))

    def backup_db(self):
        filename = filedialog.asksaveasfilename(defaultextension=".dump", filetypes=[("PostgreSQL dump", "*.dump"), ("All files", "*.*")])
        if not filename:
            return
        env = os.environ.copy()
        if DB_CONFIG.get("password"):
            env["PGPASSWORD"] = str(DB_CONFIG.get("password"))
        cmd = [
            "pg_dump",
            "-h", str(DB_CONFIG.get("host", "localhost")),
            "-p", str(DB_CONFIG.get("port", 5432)),
            "-U", str(DB_CONFIG.get("user", "postgres")),
            "-Fc",
            "-f", filename,
            str(DB_CONFIG.get("dbname", "taxi_db")),
        ]
        try:
            subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)
            messagebox.showinfo("Бэкап", f"Бэкап создан: {filename}")
        except Exception as e:
            messagebox.showerror("Ошибка бэкапа", str(e))


    # ------------------------------------------------------------------
    # Работа с SQL-файлами проекта
    # ------------------------------------------------------------------
    def project_root(self):
        """Корень проекта TAXI: файл GUI лежит в папке app, корень на уровень выше."""
        return Path(__file__).resolve().parents[1]

    def project_sql_directories(self):
        """Папки проекта, где обычно лежат SQL-скрипты."""
        return [
            "schema",
            "data",
            "helper",
            "queries",
            "setup",
        ]

    def find_project_sql_files(self):
        """Находит все .sql файлы в основных папках проекта."""
        root = self.project_root()
        files = []
        for folder in self.project_sql_directories():
            base = root / folder
            if base.exists():
                files.extend(sorted(base.rglob("*.sql")))
        return sorted(set(files), key=lambda p: str(p.relative_to(root)).lower())

    def read_sql_text(self, path):
        """Читает SQL-файл с учётом возможной кодировки."""
        path = Path(path)
        for enc in ("utf-8", "utf-8-sig", "cp1251"):
            try:
                return path.read_text(encoding=enc)
            except UnicodeDecodeError:
                continue
        return path.read_text(encoding="utf-8", errors="replace")

    def prepare_sql_with_params(self, sql_text, params_text=None):
        """
        Простая подстановка параметров для SQL-файлов проекта.
        Поддерживает $1, $2, :param1, :param2.
        """
        if params_text is None:
            needs_params = any(marker in sql_text for marker in ("$1", ":param1", ":1"))
            if needs_params:
                params_text = simpledialog.askstring(
                    "Параметры SQL-файла",
                    "Введите параметры через пробел. Например: Flash 12\nМожно оставить пустым:",
                    parent=self.root,
                )
            else:
                params_text = ""
        params = [] if not params_text else params_text.split()
        prepared = sql_text
        for idx, value in enumerate(params, start=1):
            safe = value.replace("'", "''")
            quoted = f"'{safe}'"
            prepared = prepared.replace(f"$${idx}", quoted)
            prepared = prepared.replace(f"${idx}", quoted)
            prepared = prepared.replace(f":param{idx}", quoted)
            prepared = prepared.replace(f":{idx}", quoted)
        return prepared

    def run_project_sql_file(self, path, use_psql=False):
        """Выполняет выбранный SQL-файл проекта и выводит результат в главное окно."""
        path = Path(path)
        if not path.exists():
            messagebox.showerror("SQL-файл", f"Файл не найден:\n{path}")
            return

        if use_psql:
            self.run_project_sql_file_psql(path)
            return

        try:
            sql_text = self.read_sql_text(path)
            sql_text = self.prepare_sql_with_params(sql_text)
            title = f"SQL-файл проекта: {path.relative_to(self.project_root())}"
            result = self.execute(sql_text, title=title, fetch=True)
            self.display(result)
            self.set_status(f"Выполнен SQL-файл: {path.name}")
        except Exception as e:
            messagebox.showerror("Ошибка SQL-файла", str(e))

    def run_project_sql_file_psql(self, path):
        """
        Запуск SQL через psql. Это полезно для файлов, где есть psql-команды.
        Результат выводится в главное окно приложения.
        """
        path = Path(path)
        env = os.environ.copy()
        if DB_CONFIG.get("password"):
            env["PGPASSWORD"] = str(DB_CONFIG.get("password"))
        cmd = [
            "psql",
            "-h", str(DB_CONFIG.get("host", "localhost")),
            "-p", str(DB_CONFIG.get("port", 5432)),
            "-U", str(DB_CONFIG.get("user", "")),
            "-d", str(DB_CONFIG.get("dbname", "")),
            "-f", str(path),
        ]
        try:
            proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
            title = f"psql: {path.relative_to(self.project_root())}"
            out = [title, "=" * len(title), ""]
            if proc.stdout:
                out.append(proc.stdout)
            if proc.stderr:
                out.append("\nСообщения/ошибки psql:\n" + proc.stderr)
            out.append(f"\nКод завершения: {proc.returncode}")
            self.display("\n".join(out))
            self.set_status(f"psql выполнен: {path.name}")
        except FileNotFoundError:
            messagebox.showerror("psql", "Команда psql не найдена. Проверьте установку PostgreSQL и PATH.")
        except Exception as e:
            messagebox.showerror("Ошибка psql", str(e))

    def run_sql_directory(self):
        """Запускает все SQL-файлы из выбранной папки проекта по порядку."""
        root = self.project_root()
        directory = filedialog.askdirectory(initialdir=str(root), title="Выберите папку с SQL-файлами")
        if not directory:
            return
        folder = Path(directory)
        files = sorted(folder.rglob("*.sql"))
        if not files:
            messagebox.showinfo("SQL-папка", "В выбранной папке нет .sql файлов.")
            return
        ok = messagebox.askyesno(
            "Запуск папки SQL",
            f"Будет выполнено {len(files)} SQL-файлов из папки:\n{folder}\n\n"
            "Внимание: среди них могут быть INSERT, UPDATE, DELETE или DROP. Продолжить?",
        )
        if not ok:
            return

        reports = []
        for file in files:
            try:
                sql_text = self.read_sql_text(file)
                sql_text = self.prepare_sql_with_params(sql_text, params_text="")
                result = self.execute(sql_text, title=str(file.relative_to(root)), fetch=True)
                reports.append(result)
            except Exception as e:
                reports.append(f"{file.relative_to(root)}\nОшибка: {e}\n")
        self.display("\n\n".join(reports))
        self.set_status(f"Выполнена папка SQL: {folder.name}")

    def sql_scripts_manager(self):
        """Окно навигации по SQL-скриптам проекта."""
        root = self.project_root()
        win = tk.Toplevel(self.root)
        win.title("SQL-скрипты проекта TAXI")
        win.geometry("1200x720")
        win.transient(self.root)

        top = ttk.Frame(win, padding=6)
        top.pack(fill=tk.X)
        ttk.Label(top, text="Поиск:").pack(side=tk.LEFT, padx=(0, 4))
        search_var = tk.StringVar()
        search_entry = ttk.Entry(top, textvariable=search_var, width=42)
        search_entry.pack(side=tk.LEFT, padx=4)

        body = ttk.PanedWindow(win, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        left = ttk.Frame(body)
        right = ttk.Frame(body)
        body.add(left, weight=1)
        body.add(right, weight=2)

        listbox = tk.Listbox(left, font=("Menlo", 10), exportselection=False)
        list_scroll = ttk.Scrollbar(left, orient=tk.VERTICAL, command=listbox.yview)
        listbox.configure(yscrollcommand=list_scroll.set)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        preview = scrolledtext.ScrolledText(right, wrap=tk.NONE, font=("Menlo", 11))
        preview.pack(fill=tk.BOTH, expand=True)

        all_files = self.find_project_sql_files()
        visible_files = []

        def rel(path):
            try:
                return str(path.relative_to(root))
            except Exception:
                return str(path)

        def refresh_list(*_):
            query = search_var.get().strip().lower()
            listbox.delete(0, tk.END)
            visible_files.clear()
            for file in all_files:
                name = rel(file)
                if not query or query in name.lower():
                    visible_files.append(file)
                    listbox.insert(tk.END, name)
            if visible_files:
                listbox.selection_set(0)
                show_preview()
            else:
                preview.delete("1.0", tk.END)
                preview.insert(tk.END, "SQL-файлы не найдены.")

        def selected_file():
            sel = listbox.curselection()
            if not sel:
                return None
            return visible_files[sel[0]]

        def show_preview(*_):
            file = selected_file()
            preview.config(state=tk.NORMAL)
            preview.delete("1.0", tk.END)
            if not file:
                preview.insert(tk.END, "Выберите SQL-файл слева.")
                return
            try:
                text = self.read_sql_text(file)
                header = f"-- {rel(file)}\n-- Размер: {file.stat().st_size} байт\n\n"
                preview.insert(tk.END, header + text)
            except Exception as e:
                preview.insert(tk.END, f"Ошибка чтения файла: {e}")

        def run_selected_python():
            file = selected_file()
            if file:
                self.run_project_sql_file(file, use_psql=False)

        def run_selected_psql():
            file = selected_file()
            if file:
                self.run_project_sql_file(file, use_psql=True)

        def copy_path():
            file = selected_file()
            if file:
                self.root.clipboard_clear()
                self.root.clipboard_append(str(file))
                self.set_status("Путь к SQL-файлу скопирован")

        actions = ttk.Frame(win, padding=6)
        actions.pack(fill=tk.X)
        ttk.Button(actions, text="Выполнить выбранный SQL", command=run_selected_python).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Выполнить через psql", command=run_selected_psql).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Выполнить папку SQL", command=self.run_sql_directory).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Скопировать путь", command=copy_path).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Обновить список", command=refresh_list).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Закрыть", command=win.destroy).pack(side=tk.RIGHT, padx=4)

        search_var.trace_add("write", refresh_list)
        listbox.bind("<<ListboxSelect>>", show_preview)
        search_entry.bind("<Return>", lambda e: refresh_list())
        refresh_list()

    def run_sql_file(self):
        filename = filedialog.askopenfilename(filetypes=[("SQL files", "*.sql"), ("All files", "*.*")])
        if not filename:
            return
        try:
            text = Path(filename).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = Path(filename).read_text(encoding="cp1251")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            return
        result = self.execute(text, title=f"SQL-файл: {Path(filename).name}", fetch=True)
        self.display(result)
        self.set_status("SQL-файл выполнен")


    # ------------------------- полное покрытие ./help.sh и ./python_reports.sh -------------------------
    def run_shell_tool(self, tool_name, args=None, title=None, timeout=180):
        """Запускает ./help.sh или ./python_reports.sh из корня проекта и выводит результат в окно GUI."""
        args = [str(a) for a in (args or []) if str(a) != ""]
        root = self.project_root()
        tool_path = root / tool_name
        if not tool_path.exists():
            messagebox.showerror("Файл не найден", f"Не найден файл {tool_path}")
            return
        cmd = [str(tool_path)] + args
        self.set_status("Выполняю: " + " ".join([tool_name] + args))
        env = os.environ.copy()
        env.setdefault("PYTHONIOENCODING", "utf-8")
        try:
            completed = subprocess.run(
                cmd,
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
            )
            output = []
            header = title or ("./" + " ".join([tool_name] + args))
            output.append(header)
            output.append("=" * len(header))
            output.append("Команда: " + " ".join(["./" + tool_name] + args))
            output.append(f"Код завершения: {completed.returncode}")
            if completed.stdout:
                output.append("\nSTDOUT:\n" + completed.stdout)
            if completed.stderr:
                output.append("\nSTDERR:\n" + completed.stderr)
            self.last_rows = []
            self.last_cols = []
            self.display("\n".join(output))
            self.set_status("Готово: " + " ".join([tool_name] + args))
        except subprocess.TimeoutExpired:
            self.display(f"Команда выполнялась слишком долго и была остановлена:\n./{tool_name} {' '.join(args)}\n")
            self.set_status("Команда остановлена по таймауту")
        except Exception as e:
            messagebox.showerror("Ошибка запуска", str(e))
            self.set_status("Ошибка запуска команды")

    def run_h(self, *args, title=None):
        self.run_shell_tool("help.sh", list(args), title=title or "./help.sh " + " ".join(map(str, args)))

    def run_python_report(self, *args, title=None):
        self.run_shell_tool("python_reports.sh", list(args), title=title or "./python_reports.sh " + " ".join(map(str, args)), timeout=240)

    def run_h_with_fields(self, command, title, fields):
        data = self.ask_fields(title, fields)
        if data is None:
            return
        args = [command] + [data[key] for key, _, _ in fields]
        self.run_h(*args, title=title)

    def run_h_confirm_delete_driver(self):
        data = self.ask_fields("./help.sh 42 — удалить водителя", [("code", "Код водителя", "32")])
        if not data:
            return
        if not messagebox.askyesno("Подтверждение", f"Удалить водителя с кодом {data['code']} через ./help.sh 42?"):
            return
        self.run_h("42", data["code"], title="./help.sh 42 — удалить водителя")

    def run_python_with_optional_fields(self, command, title, fields):
        data = self.ask_fields(title, fields)
        if data is None:
            return
        values = [data[key] for key, _, _ in fields]
        args = [command] + [v for v in values if v]
        self.run_python_report(*args, title=title)

    def make_scrollable_window(self, title, width=760, height=720):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry(f"{width}x{height}")
        win.transient(self.root)
        outer = ttk.Frame(win, padding=8)
        outer.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(outer, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        body = ttk.Frame(canvas)
        body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=body, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        return win, body

    def add_command_section(self, parent, title, items):
        section = ttk.LabelFrame(parent, text=title, padding=8)
        section.pack(fill=tk.X, pady=6)
        for i, item in enumerate(items):
            label, desc, action = item
            row = ttk.Frame(section)
            row.pack(fill=tk.X, pady=2)
            ttk.Button(row, text=label, command=action, width=22).pack(side=tk.LEFT, padx=(0, 8))
            ttk.Label(row, text=desc, wraplength=470, justify=tk.LEFT).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def h_commands_window(self):
        win, body = self.make_scrollable_window("Команды ./help.sh — полное меню TAXI")
        ttk.Label(
            body,
            text="Здесь собраны команды из ./help.sh. Простые команды запускаются сразу, параметрические открывают окно ввода.",
            wraplength=680,
        ).pack(anchor="w", pady=(0, 8))

        self.add_command_section(body, "Данные", [
            ("fetch", "Скачать недостающие дни из открытых данных Чикаго", lambda: self.run_shell_tool("help.sh", ["fetch"], title="./help.sh fetch — сбор данных", timeout=1800)),
            ("load", "Загрузить скачанные поездки в базу (только новые)", lambda: self.run_shell_tool("help.sh", ["load"], title="./help.sh load — загрузка в базу", timeout=600)),
        ])

        self.add_command_section(body, "Основные задачи", [
            ("task1", "Выручка по сезонам", lambda: self.run_h("task1", title="./help.sh task1 — выручка по сезонам")),
            ("task2", "Выручка по сезонам и таксопаркам", lambda: self.run_h("task2", title="./help.sh task2 — сезоны и таксопарки")),
            ("task3", "Выручка по дням недели и водителям", lambda: self.run_h("task3", title="./help.sh task3 — дни недели и водители")),
            ("task4", "Выручка по водителям за выбранный день", lambda: self.run_h_with_fields("task4", "./help.sh task4 — день", [("day", "День недели: 1 — пн ... 7 — вс", "1")]))
        ])

        self.add_command_section(body, "Просмотр данных", [
            ("01", "Все таксопарки", lambda: self.run_h("01", title="./help.sh 01 — таксопарки")),
            ("02", "Водители (первые 50)", lambda: self.run_h("02", title="./help.sh 02 — водители")),
            ("03", "Типы клиентов", lambda: self.run_h("03", title="./help.sh 03 — типы клиентов")),
            ("04", "Количество поездок", lambda: self.run_h("04", title="./help.sh 04 — количество поездок")),
            ("05", "Последние поездки", lambda: self.run_h("05", title="./help.sh 05 — последние поездки")),
            ("06", "Типы клиентов с числом поездок", lambda: self.run_h("06", title="./help.sh 06 — типы клиентов и поездки")),
            ("16", "Структура таблиц", lambda: self.run_h("16", title="./help.sh 16 — структура таблиц")),
        ])

        self.add_command_section(body, "JOIN", [
            ("07", "INNER JOIN", lambda: self.run_h("07", title="./help.sh 07 — INNER JOIN")),
            ("08", "LEFT JOIN", lambda: self.run_h("08", title="./help.sh 08 — LEFT JOIN")),
            ("09", "RIGHT JOIN", lambda: self.run_h("09", title="./help.sh 09 — RIGHT JOIN")),
            ("10", "FULL JOIN", lambda: self.run_h("10", title="./help.sh 10 — FULL JOIN")),
            ("11", "CROSS JOIN", lambda: self.run_h("11", title="./help.sh 11 — CROSS JOIN")),
            ("12", "SELF JOIN", lambda: self.run_h("12", title="./help.sh 12 — SELF JOIN")),
        ])

        self.add_command_section(body, "Показать до/после", [
            ("60", "ДО UPDATE", lambda: self.run_h("60", title="./help.sh 60 — до UPDATE")),
            ("61", "Выполнить UPDATE", lambda: self.run_h("61", title="./help.sh 61 — UPDATE")),
            ("62", "ПОСЛЕ UPDATE", lambda: self.run_h("62", title="./help.sh 62 — после UPDATE")),
            ("63", "ДО DELETE", lambda: self.run_h("63", title="./help.sh 63 — до DELETE")),
            ("64", "Выполнить DELETE", lambda: self.run_h("64", title="./help.sh 64 — DELETE")),
            ("65", "ПОСЛЕ DELETE", lambda: self.run_h("65", title="./help.sh 65 — после DELETE")),
        ])

        self.add_command_section(body, "Аналитика", [
            ("17", "Топ-10 районов по выручке", lambda: self.run_h("17", title="./help.sh 17 — топ районов")),
            ("18", "Топ-10 водителей по выручке", lambda: self.run_h("18", title="./help.sh 18 — топ водителей")),
            ("19", "Выручка по месяцам", lambda: self.run_h("19", title="./help.sh 19 — выручка по месяцам")),
            ("20", "Средний чек", lambda: self.run_h("20", title="./help.sh 20 — средний чек")),
            ("21", "Поездки по часам", lambda: self.run_h("21", title="./help.sh 21 — поездки по часам")),
            ("22", "Статистика по таксопаркам", lambda: self.run_h("22", title="./help.sh 22 — статистика по таксопаркам")),
            ("23", "Загруженность водителей", lambda: self.run_h("23", title="./help.sh 23 — загруженность водителей")),
            ("24", "Средние чаевые по типам клиентов", lambda: self.run_h("24", title="./help.sh 24 — чаевые по типам клиентов")),
            ("25", "Выручка по дням недели", lambda: self.run_h("25", title="./help.sh 25 — дни недели")),
            ("26", "Выручка по типам клиентов", lambda: self.run_h("26", title="./help.sh 26 — типы клиентов")),
            ("27", "Средний пробег по таксопаркам", lambda: self.run_h("27", title="./help.sh 27 — средний пробег")),
            ("28", "Распределение поездок по часам", lambda: self.run_h("28", title="./help.sh 28 — распределение по часам")),
            ("29", "Средний чек по часам", lambda: self.run_h("29", title="./help.sh 29 — средний чек по часам")),
            ("30", "Топ-10 водителей по чаевым", lambda: self.run_h("30", title="./help.sh 30 — топ по чаевым")),
        ])

        self.add_command_section(body, "Запросы с параметрами", [
            ("31", "Таксопарки по части названия", lambda: self.run_h_with_fields("31", "./help.sh 31 — таксопарки", [("text", "Часть названия", "Cab")])) ,
            ("32", "Информация о водителе", lambda: self.run_h_with_fields("32", "./help.sh 32 — водитель", [("code", "Код водителя", "1")])) ,
            ("33", "Последние поездки водителя", lambda: self.run_h_with_fields("33", "./help.sh 33 — поездки водителя", [("code", "Код водителя", "1")])) ,
            ("34", "Поездки дороже суммы", lambda: self.run_h_with_fields("34", "./help.sh 34 — поездки дороже суммы", [("amount", "Сумма $", "100")])) ,
            ("35", "Водители с выручкой выше суммы", lambda: self.run_h_with_fields("35", "./help.sh 35 — выручка выше суммы", [("amount", "Сумма $", "10000")])) ,
            ("40", "Переименовать таксопарк", lambda: self.run_h_with_fields("40", "./help.sh 40 — переименовать таксопарк", [("code", "Код таксопарка", "1"), ("name", "Новое название", "")])) ,
            ("41", "Изменить описание типа клиента", lambda: self.run_h_with_fields("41", "./help.sh 41 — описание типа клиента", [("code", "Код типа клиента", "1"), ("desc", "Новое описание", "")])) ,
            ("42", "Удалить водителя", self.run_h_confirm_delete_driver),
            ("43", "Добавить таксопарк", lambda: self.run_h_with_fields("43", "./help.sh 43 — добавить таксопарк", [("name", "Название", "Новый таксопарк")])) ,
            ("44", "Добавить водителя", lambda: self.run_h_with_fields("44", "./help.sh 44 — добавить водителя", [("taxi_id", "taxi_id (до 16 символов)", "manual00000001")])) ,
            ("45", "Сменить таксопарк поездки", lambda: self.run_h_with_fields("45", "./help.sh 45 — таксопарк поездки", [("ride", "Код поездки", "1"), ("company", "Код таксопарка", "1")])) ,
            ("46", "Изменить чаевые поездки", lambda: self.run_h_with_fields("46", "./help.sh 46 — чаевые поездки", [("ride", "Код поездки", "1"), ("tips", "Чаевые $", "2.00")])) ,
        ])

        self.add_command_section(body, "Представления и подзапросы", [
            ("100", "Создать пользовательское представление", lambda: self.run_h("100", title="./help.sh 100 — view")),
            ("101", "Создать технологическое представление", lambda: self.run_h("101", title="./help.sh 101 — tech view")),
            ("102", "Проверить представления", lambda: self.run_h("102", title="./help.sh 102 — check views")),
            ("110", "Отклонение стоимости поездки", lambda: self.run_h("110", title="./help.sh 110 — подзапрос 1.1")),
            ("111", "Рейтинг таксопарков", lambda: self.run_h("111", title="./help.sh 111 — рейтинг таксопарков")),
            ("112", "Поездки дороже среднего по таксопарку", lambda: self.run_h("112", title="./help.sh 112 — выше среднего")),
            ("113", "Статистика по таксопаркам", lambda: self.run_h("113", title="./help.sh 113 — статистика таксопарков")),
            ("114", "Топ-3 водителя в каждом таксопарке", lambda: self.run_h("114", title="./help.sh 114 — топ-3")),
            ("115", "Поездки дороже среднего по водителю", lambda: self.run_h_with_fields("115", "./help.sh 115 — водитель", [("code", "Код водителя", "1")])) ,
            ("116", "Водители без поездок дешевле $10", lambda: self.run_h("116", title="./help.sh 116 — без дешёвых")),
            ("117", "Лучшие водители", lambda: self.run_h("117", title="./help.sh 117 — лучшие водители")),
            ("118", "Самые дорогие поездки", lambda: self.run_h("118", title="./help.sh 118 — самые дорогие поездки")),
            ("199", "Выполнить все запросы с подзапросами", lambda: self.run_h("199", title="./help.sh 199 — все подзапросы")),
        ])

        self.add_command_section(body, "Функции", [
            ("200", "Создать все функции", lambda: self.run_h("200", title="./help.sh 200 — создать функции")),
            ("201", "Водители с выручкой выше порога", lambda: self.run_h_with_fields("201", "./help.sh 201 — порог", [("amount", "Порог $", "10000")])) ,
            ("202", "Выручка по таксопаркам и сезонам", lambda: self.run_h("202", title="./help.sh 202 — таксопарки и сезоны")),
            ("203", "Сводная таблица водители × способы оплаты", lambda: self.run_h("203", title="./help.sh 203 — сводная")),
            ("204", "Выполнить всё по функциям", lambda: self.run_h("204", title="./help.sh 204 — все функции")),
        ])

    def python_commands_window(self):
        win, body = self.make_scrollable_window("Команды ./python_reports.sh — отчёты TAXI", width=720, height=560)
        ttk.Label(
            body,
            text="Эти кнопки запускают тот же файл ./python_reports.sh, но из графического интерфейса. Графики сохраняются в docs/ проекта.",
            wraplength=640,
        ).pack(anchor="w", pady=(0, 8))

        self.add_command_section(body, "Отчёты", [
            ("python_reports.sh 1", "Отчёт по водителям и типам клиентов; оба параметра необязательны", lambda: self.run_python_with_optional_fields("1", "./python_reports.sh 1", [("driver", "Код водителя, можно пусто", ""), ("cls", "Тип клиента, можно пусто", "")])) ,
            ("python_reports.sh 1s", "Отчёт со звёздочкой * в углу", lambda: self.run_python_with_optional_fields("1s", "./python_reports.sh 1s", [("driver", "Код водителя, можно пусто", ""), ("cls", "Тип клиента, можно пусто", "")])) ,
            ("python_reports.sh 2", "Сводная таблица; тип клиента необязателен", lambda: self.run_python_with_optional_fields("2", "./python_reports.sh 2", [("cls", "Тип клиента, можно пусто", "")])) ,
            ("python_reports.sh 3", "График динамики", lambda: self.run_python_report("3", title="./python_reports.sh 3 — график динамики")),
            ("python_reports.sh 4", "Круговая диаграмма; водитель необязателен", lambda: self.run_python_with_optional_fields("4", "./python_reports.sh 4", [("driver", "Код водителя, можно пусто", "")])) ,
        ])

        self.add_command_section(body, "Пакетный запуск и сохранение", [
            ("python_reports.sh all", "Выполнить всё", lambda: self.run_python_report("all", title="./python_reports.sh all")),
            ("python_reports.sh save", "Сохранить все графики", lambda: self.run_python_report("save", title="./python_reports.sh save")),
            ("python_reports.sh save --force", "Сохранить все графики с перезаписью", lambda: self.run_python_report("save", "--force", title="./python_reports.sh save --force")),
        ])

        self.add_command_section(body, "Дополнительно", [
            ("Открыть docs", "Показать папку docs в Finder", self.open_docs_folder),
            ("Показать меню python_reports.sh", "Запустить ./python_reports.sh без параметров", lambda: self.run_python_report(title="./python_reports.sh — меню")),
        ])

    def open_docs_folder(self):
        docs = self.project_root() / "docs"
        docs.mkdir(exist_ok=True)
        try:
            subprocess.run(["open", str(docs)], check=False)
            self.set_status(f"Открыта папка {docs}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def show_about(self):
        messagebox.showinfo(
            "О программе",
            "TAXI: поездки такси Чикаго\n"
            "Реальные открытые данные города (Chicago Data Portal, Taxi Trips).\n"
            "Таблицы: таксопарки, водители, типы клиентов, районы, поездки, сезон.\n\n"
            "Реализовано: просмотр, фильтры, поиск, рейтинги, аналитика, графики, CRUD,\n"
            "UPDATE/DELETE до-после, экспорт, бэкап и запуск SQL-файлов."
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = TaxiApp(root)
    root.mainloop()
