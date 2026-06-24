#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GUI для базы данных TAXI.
Положить файл в: ~/Desktop/DATA_BASE/TAXI/app/gui.py
Запускать из папки app: python3 gui.py
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

try:
    from scripts.db_config import DB_CONFIG
except Exception:
    DB_CONFIG = {
        "host": "localhost",
        "port": 5432,
        "user": "uliavladimirovna",
        "password": "",
        "dbname": "taxi_lab5",
    }


class TaxiApp:
    TABLES = ["АВТОМОБИЛИ", "ВОДИТЕЛИ", "КЛИЕНТЫ", "ТАРИФЫ", "ПОЕЗДКИ", "СЕЗОН"]

    def __init__(self, root):
        self.root = root
        self.root.title("TAXI: система управления поездками")
        self.root.geometry("1420x860")
        self.root.minsize(1100, 700)

        self.conn = None
        self.last_rows = []
        self.last_cols = []
        self.status_var = tk.StringVar(value="Готово")
        self.filter_field_var = tk.StringVar(value="класс")
        self.filter_value_var = tk.StringVar(value="")
        self.limit_var = tk.StringVar(value="100")
        self.search_var = tk.StringVar(value="")

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
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        menubar.add_cascade(label="Файл", menu=file_menu)

        db_menu = tk.Menu(menubar, tearoff=0)
        db_menu.add_command(label="Переподключиться", command=self.reconnect)
        db_menu.add_command(label="Структура БД", command=self.show_structure)
        db_menu.add_command(label="Статистика БД", command=self.db_stats)
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
            ("Топ клиентов", self.top_clients),
            ("Доход по классам", self.revenue_by_class),
            ("Статистика автомобилей", self.car_stats),
            ("По сезонам", self.season_stats),
        ])
        self.add_button_group(left, "Аналитика", [
            ("Динамика по месяцам", self.chart_monthly_revenue),
            ("Круговая по классам", self.chart_class_pie),
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
            ("Поездка с расчётом", self.add_ride_calculated),
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
            ("Неиспользуемые авто", self.inactive_cars),
            ("Проверка связей", self.data_quality_check),
        ])
        self.add_button_group(left, "Администрирование", [
            ("Создать views", self.create_views),
            ("Проверить views", self.check_views),
            ("Создать функции", self.create_functions),
            ("Демо функций", self.functions_demo),
            ("Архивация поездок", self.archive_old_rides),
            ("Экспорт текущего CSV", self.export_current_csv),
            ("Экспорт всех таблиц", self.export_all_tables_csv),
            ("Бэкап", self.backup_db),
            ("SQL-файл", self.run_sql_file),
        ])

        right = ttk.Frame(main)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        filters = ttk.LabelFrame(right, text="Параметры и фильтр", padding=8)
        filters.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(filters, text="Количество:").grid(row=0, column=0, sticky="w", padx=4, pady=3)
        ttk.Spinbox(filters, from_=1, to=5000, textvariable=self.limit_var, width=8).grid(row=0, column=1, sticky="w", padx=4, pady=3)

        ttk.Label(filters, text="Фильтр:").grid(row=0, column=2, sticky="w", padx=4, pady=3)
        self.filter_field_combo = ttk.Combobox(
            filters,
            textvariable=self.filter_field_var,
            values=["класс", "марка", "модель", "гос_номер", "водитель", "клиент", "телефон", "дата"],
            width=16,
            state="readonly",
        )
        self.filter_field_combo.grid(row=0, column=3, sticky="w", padx=4, pady=3)
        self.filter_field_combo.bind("<<ComboboxSelected>>", lambda e: self.filter_value_var.set(""))

        self.filter_value_combo = ttk.Combobox(filters, textvariable=self.filter_value_var, width=28)
        self.filter_value_combo.grid(row=0, column=4, sticky="w", padx=4, pady=3)
        self.filter_value_combo.bind("<KeyRelease>", self.on_filter_typing)

        ttk.Button(filters, text="Применить к поездкам", command=self.latest_rides).grid(row=0, column=5, sticky="w", padx=4, pady=3)
        ttk.Button(filters, text="Очистить", command=self.clear_filters).grid(row=0, column=6, sticky="w", padx=4, pady=3)

        ttk.Label(filters, text="Быстрый поиск:").grid(row=1, column=0, sticky="w", padx=4, pady=3)
        search_entry = ttk.Entry(filters, textvariable=self.search_var, width=32)
        search_entry.grid(row=1, column=1, columnspan=2, sticky="w", padx=4, pady=3)
        search_entry.bind("<Return>", lambda e: self.quick_search())
        ttk.Button(filters, text="Искать", command=self.quick_search).grid(row=1, column=3, sticky="w", padx=4, pady=3)

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

    # ------------------------- данные для подсказок -------------------------
    def load_autocomplete_data(self):
        self.autocomplete = {
            "класс": ["эконом", "комфорт", "бизнес"],
            "марка": [],
            "модель": [],
            "гос_номер": [],
            "водитель": [],
            "клиент": [],
            "телефон": [],
            "дата": [],
        }
        if not self.conn:
            return
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT DISTINCT марка FROM АВТОМОБИЛИ WHERE марка IS NOT NULL ORDER BY марка")
                self.autocomplete["марка"] = [r[0] for r in cur.fetchall()]
                cur.execute("SELECT DISTINCT модель FROM АВТОМОБИЛИ WHERE модель IS NOT NULL ORDER BY модель")
                self.autocomplete["модель"] = [r[0] for r in cur.fetchall()]
                cur.execute("SELECT DISTINCT гос_номер FROM АВТОМОБИЛИ WHERE гос_номер IS NOT NULL ORDER BY гос_номер")
                self.autocomplete["гос_номер"] = [r[0] for r in cur.fetchall()]
                cur.execute("SELECT фамилия || ' ' || имя FROM ВОДИТЕЛИ ORDER BY фамилия, имя")
                self.autocomplete["водитель"] = [r[0] for r in cur.fetchall()]
                cur.execute("SELECT COALESCE(фамилия,'') || ' ' || имя FROM КЛИЕНТЫ ORDER BY фамилия, имя")
                self.autocomplete["клиент"] = [r[0].strip() for r in cur.fetchall()]
                cur.execute("SELECT телефон FROM КЛИЕНТЫ UNION SELECT телефон FROM ВОДИТЕЛИ ORDER BY телефон")
                self.autocomplete["телефон"] = [r[0] for r in cur.fetchall()]
            self.conn.commit()
        except Exception:
            self.conn.rollback()

    def on_filter_typing(self, event=None):
        field = self.filter_field_var.get()
        text = self.filter_value_var.get().lower().strip()
        values = self.autocomplete.get(field, [])
        if not text:
            self.filter_value_combo["values"] = values[:20]
            return
        matches = [v for v in values if text in str(v).lower()][:20]
        self.filter_value_combo["values"] = matches

    def clear_filters(self):
        self.filter_value_var.set("")
        self.search_var.set("")
        self.latest_rides()

    def build_ride_filter(self):
        field = self.filter_field_var.get()
        value = self.filter_value_var.get().strip()
        if not value:
            return "", []
        mapping = {
            "класс": "a.класс ILIKE %s",
            "марка": "a.марка ILIKE %s",
            "модель": "a.модель ILIKE %s",
            "гос_номер": "a.гос_номер ILIKE %s",
            "водитель": "(v.фамилия ILIKE %s OR v.имя ILIKE %s)",
            "клиент": "(k.фамилия ILIKE %s OR k.имя ILIKE %s)",
            "телефон": "(v.телефон ILIKE %s OR k.телефон ILIKE %s)",
            "дата": "CAST(p.дата AS TEXT) ILIKE %s",
        }
        cond = mapping.get(field, "a.класс ILIKE %s")
        if cond.count("%s") == 2:
            return " AND " + cond, [f"%{value}%", f"%{value}%"]
        return " AND " + cond, [f"%{value}%"]

    # ------------------------- просмотр и отчёты -------------------------
    def db_stats(self):
        query = """
            SELECT 'АВТОМОБИЛИ' AS таблица, COUNT(*) AS записей FROM АВТОМОБИЛИ
            UNION ALL SELECT 'ВОДИТЕЛИ', COUNT(*) FROM ВОДИТЕЛИ
            UNION ALL SELECT 'КЛИЕНТЫ', COUNT(*) FROM КЛИЕНТЫ
            UNION ALL SELECT 'ТАРИФЫ', COUNT(*) FROM ТАРИФЫ
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
              AND table_name IN ('АВТОМОБИЛИ','ВОДИТЕЛИ','КЛИЕНТЫ','ТАРИФЫ','ПОЕЗДКИ','СЕЗОН')
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
                       a.гос_номер, a.марка, a.модель, a.класс,
                       v.фамилия AS водитель, k.имя AS клиент,
                       p.расстояние_км, p.время_мин, p.стоимость
                FROM ПОЕЗДКИ p
                LEFT JOIN АВТОМОБИЛИ a ON a.код = p.автомобиль
                LEFT JOIN ВОДИТЕЛИ v ON v.код = p.водитель
                LEFT JOIN КЛИЕНТЫ k ON k.код = p.клиент
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
                   a.гос_номер, a.марка, a.модель, a.класс,
                   v.фамилия || ' ' || v.имя AS водитель,
                   COALESCE(k.фамилия || ' ', '') || k.имя AS клиент,
                   p.расстояние_км, p.время_мин, p.стоимость
            FROM ПОЕЗДКИ p
            LEFT JOIN АВТОМОБИЛИ a ON a.код = p.автомобиль
            LEFT JOIN ВОДИТЕЛИ v ON v.код = p.водитель
            LEFT JOIN КЛИЕНТЫ k ON k.код = p.клиент
            WHERE 1=1 {cond}
            ORDER BY p.дата DESC
            LIMIT %s
        """
        self.execute_and_display(query, params=params + [limit], title="Последние поездки", status="Последние поездки")

    def top_drivers(self):
        query = """
            SELECT v.код, v.фамилия, v.имя, v.телефон, v.стаж_лет, v.рейтинг,
                   COUNT(p.код_поездки) AS поездок,
                   ROUND(COALESCE(SUM(p.стоимость),0), 2) AS выручка,
                   ROUND(COALESCE(AVG(p.стоимость),0), 2) AS средний_чек
            FROM ВОДИТЕЛИ v
            LEFT JOIN ПОЕЗДКИ p ON p.водитель = v.код
            GROUP BY v.код, v.фамилия, v.имя, v.телефон, v.стаж_лет, v.рейтинг
            ORDER BY выручка DESC, поездок DESC
            LIMIT %s
        """
        self.execute_and_display(query, [self.get_limit()], title="Топ водителей", status="Топ водителей")

    def top_clients(self):
        query = """
            SELECT k.код, k.фамилия, k.имя, k.телефон, k.email,
                   COUNT(p.код_поездки) AS поездок,
                   ROUND(COALESCE(SUM(p.стоимость),0), 2) AS сумма,
                   ROUND(COALESCE(AVG(p.стоимость),0), 2) AS средний_чек
            FROM КЛИЕНТЫ k
            LEFT JOIN ПОЕЗДКИ p ON p.клиент = k.код
            GROUP BY k.код, k.фамилия, k.имя, k.телефон, k.email
            ORDER BY сумма DESC, поездок DESC
            LIMIT %s
        """
        self.execute_and_display(query, [self.get_limit()], title="Топ клиентов", status="Топ клиентов")

    def revenue_by_class(self):
        query = """
            SELECT a.класс,
                   COUNT(p.код_поездки) AS поездок,
                   ROUND(SUM(p.стоимость), 2) AS выручка,
                   ROUND(AVG(p.стоимость), 2) AS средний_чек,
                   ROUND(AVG(p.расстояние_км), 2) AS среднее_расстояние,
                   ROUND(AVG(p.время_мин), 2) AS среднее_время
            FROM ПОЕЗДКИ p
            JOIN АВТОМОБИЛИ a ON a.код = p.автомобиль
            GROUP BY a.класс
            ORDER BY выручка DESC
        """
        self.execute_and_display(query, title="Доход по классам автомобилей", status="Доход по классам")

    def car_stats(self):
        query = """
            SELECT a.код, a.гос_номер, a.марка, a.модель, a.класс,
                   COUNT(p.код_поездки) AS поездок,
                   ROUND(COALESCE(SUM(p.стоимость),0), 2) AS выручка,
                   ROUND(COALESCE(AVG(p.расстояние_км),0), 2) AS средний_км
            FROM АВТОМОБИЛИ a
            LEFT JOIN ПОЕЗДКИ p ON p.автомобиль = a.код
            GROUP BY a.код, a.гос_номер, a.марка, a.модель, a.класс
            ORDER BY выручка DESC, поездок DESC
            LIMIT %s
        """
        self.execute_and_display(query, [self.get_limit()], title="Статистика автомобилей", status="Статистика автомобилей")

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
                    WHEN стоимость < 300 THEN 'до 300'
                    WHEN стоимость < 600 THEN '300-599'
                    WHEN стоимость < 1000 THEN '600-999'
                    ELSE '1000+'
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
        text = self.search_var.get().strip()
        if not text:
            messagebox.showinfo("Поиск", "Введите текст для поиска")
            return
        like = f"%{text}%"
        query = """
            SELECT 'автомобиль' AS тип, код::text, гос_номер || ' ' || марка || ' ' || модель AS найдено
            FROM АВТОМОБИЛИ
            WHERE гос_номер ILIKE %s OR марка ILIKE %s OR модель ILIKE %s OR класс ILIKE %s
            UNION ALL
            SELECT 'водитель', код::text, фамилия || ' ' || имя || ' ' || телефон
            FROM ВОДИТЕЛИ
            WHERE фамилия ILIKE %s OR имя ILIKE %s OR телефон ILIKE %s
            UNION ALL
            SELECT 'клиент', код::text, COALESCE(фамилия || ' ', '') || имя || ' ' || телефон
            FROM КЛИЕНТЫ
            WHERE фамилия ILIKE %s OR имя ILIKE %s OR телефон ILIKE %s OR email ILIKE %s
            ORDER BY тип, найдено
            LIMIT %s
        """
        params = [like, like, like, like, like, like, like, like, like, like, like, self.get_limit()]
        self.execute_and_display(query, params, title=f"Быстрый поиск: {text}", status="Поиск")

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
        self.open_line_chart(months, revenue, "Динамика выручки по месяцам", "Месяц", "Выручка")

    def chart_class_pie(self):
        if not self.conn:
            messagebox.showerror("Ошибка", "Нет подключения к БД")
            return
        query = """
            SELECT a.класс, COUNT(*) AS поездок
            FROM ПОЕЗДКИ p
            JOIN АВТОМОБИЛИ a ON a.код = p.автомобиль
            GROUP BY a.класс
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
        self.open_pie_chart(labels, sizes, "Доля поездок по классам")

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
        table = simpledialog.askstring("Добавление", "Что добавить? car / driver / client / tariff / ride")
        if not table:
            return
        table = table.lower().strip()
        if table in ["car", "авто", "автомобиль"]:
            self.add_car()
        elif table in ["driver", "водитель"]:
            self.add_driver()
        elif table in ["client", "клиент"]:
            self.add_client()
        elif table in ["tariff", "тариф"]:
            self.add_tariff()
        elif table in ["ride", "поездка"]:
            self.add_ride()
        else:
            messagebox.showerror("Ошибка", "Введите: car, driver, client, tariff или ride")

    def add_car(self):
        data = self.ask_fields("Добавить автомобиль", [
            ("num", "Гос. номер", "А999АА"),
            ("brand", "Марка", "Hyundai"),
            ("model", "Модель", "Solaris"),
            ("year", "Год выпуска", "2022"),
            ("color", "Цвет", "Белый"),
            ("cls", "Класс", "эконом"),
        ])
        if not data:
            return
        query = """
            INSERT INTO АВТОМОБИЛИ (гос_номер, марка, модель, год_выпуска, цвет, класс)
            VALUES (%s, %s, %s, NULLIF(%s,'')::int, %s, %s)
        """
        self.execute_and_display(query, [data["num"], data["brand"], data["model"], data["year"], data["color"], data["cls"]],
                                 title="Добавление автомобиля", status="Автомобиль добавлен", fetch=False)
        self.load_autocomplete_data()

    def add_driver(self):
        data = self.ask_fields("Добавить водителя", [
            ("surname", "Фамилия", "Иванов"),
            ("name", "Имя", "Иван"),
            ("patronymic", "Отчество", ""),
            ("phone", "Телефон", "+79000000000"),
            ("exp", "Стаж лет", "5"),
            ("cat", "Категория прав", "B"),
            ("rating", "Рейтинг", "4.80"),
        ])
        if not data:
            return
        query = """
            INSERT INTO ВОДИТЕЛИ (фамилия, имя, отчество, телефон, стаж_лет, категория_прав, рейтинг)
            VALUES (%s, %s, NULLIF(%s,''), %s, NULLIF(%s,'')::int, NULLIF(%s,''), NULLIF(%s,'')::numeric)
        """
        params = [data["surname"], data["name"], data["patronymic"], data["phone"], data["exp"], data["cat"], data["rating"]]
        self.execute_and_display(query, params, title="Добавление водителя", status="Водитель добавлен", fetch=False)
        self.load_autocomplete_data()

    def add_client(self):
        data = self.ask_fields("Добавить клиента", [
            ("surname", "Фамилия", "Петрова"),
            ("name", "Имя", "Анна"),
            ("phone", "Телефон", "+79010000099"),
            ("email", "Email", ""),
        ])
        if not data:
            return
        query = """
            INSERT INTO КЛИЕНТЫ (фамилия, имя, телефон, email, дата_регистрации)
            VALUES (NULLIF(%s,''), %s, %s, NULLIF(%s,''), CURRENT_DATE)
        """
        self.execute_and_display(query, [data["surname"], data["name"], data["phone"], data["email"]],
                                 title="Добавление клиента", status="Клиент добавлен", fetch=False)
        self.load_autocomplete_data()

    def add_tariff(self):
        data = self.ask_fields("Добавить тариф", [
            ("cls", "Класс", "премиум"),
            ("km", "Цена за км", "50"),
            ("hour", "Цена за час", "800"),
            ("min", "Минимальная стоимость", "300"),
        ])
        if not data:
            return
        query = """
            INSERT INTO ТАРИФЫ (класс, цена_за_км, цена_за_час, минимальная_стоимость)
            VALUES (%s, %s::numeric, %s::numeric, %s::numeric)
        """
        self.execute_and_display(query, [data["cls"], data["km"], data["hour"], data["min"]],
                                 title="Добавление тарифа", status="Тариф добавлен", fetch=False)

    def add_ride(self):
        data = self.ask_fields("Добавить поездку", [
            ("car", "Код автомобиля", "1"),
            ("driver", "Код водителя", "1"),
            ("client", "Код клиента", "1"),
            ("km", "Расстояние км", "10"),
            ("min", "Время мин", "25"),
            ("cost", "Стоимость", "500"),
        ])
        if not data:
            return
        query = """
            INSERT INTO ПОЕЗДКИ (дата, автомобиль, водитель, клиент, расстояние_км, время_мин, стоимость)
            VALUES (NOW(), %s::int, %s::int, %s::int, %s::numeric, %s::int, %s::numeric)
        """
        params = [data["car"], data["driver"], data["client"], data["km"], data["min"], data["cost"]]
        self.execute_and_display(query, params, title="Добавление поездки", status="Поездка добавлена", fetch=False)

    def edit_record_window(self):
        action = simpledialog.askstring("Редактирование", "Что изменить? driver_phone / driver_rating / client_phone / tariff / car_class")
        if not action:
            return
        action = action.lower().strip()
        if action == "driver_phone":
            self.update_driver_phone()
        elif action == "driver_rating":
            self.update_driver_rating()
        elif action == "client_phone":
            self.update_client_phone()
        elif action == "tariff":
            self.update_tariff()
        elif action == "car_class":
            self.update_car_class()
        else:
            messagebox.showerror("Ошибка", "Варианты: driver_phone, driver_rating, client_phone, tariff, car_class")

    def update_driver_phone(self):
        data = self.ask_fields("Изменить телефон водителя", [("id", "Код водителя", "1"), ("phone", "Новый телефон", "+79000000001")])
        if data:
            self.execute_and_display("UPDATE ВОДИТЕЛИ SET телефон=%s WHERE код=%s::int", [data["phone"], data["id"]],
                                     title="Изменение телефона водителя", status="Телефон изменён", fetch=False)

    def update_driver_rating(self):
        data = self.ask_fields("Изменить рейтинг водителя", [("id", "Код водителя", "1"), ("rating", "Новый рейтинг", "4.90")])
        if data:
            self.execute_and_display("UPDATE ВОДИТЕЛИ SET рейтинг=%s::numeric WHERE код=%s::int", [data["rating"], data["id"]],
                                     title="Изменение рейтинга водителя", status="Рейтинг изменён", fetch=False)

    def update_client_phone(self):
        data = self.ask_fields("Изменить телефон клиента", [("id", "Код клиента", "1"), ("phone", "Новый телефон", "+79010000999")])
        if data:
            self.execute_and_display("UPDATE КЛИЕНТЫ SET телефон=%s WHERE код=%s::int", [data["phone"], data["id"]],
                                     title="Изменение телефона клиента", status="Телефон изменён", fetch=False)

    def update_tariff(self):
        data = self.ask_fields("Изменить тариф", [
            ("cls", "Класс тарифа", "эконом"),
            ("km", "Цена за км", "30"),
            ("hour", "Цена за час", "500"),
            ("min", "Минимальная стоимость", "150"),
        ])
        if data:
            query = """
                UPDATE ТАРИФЫ
                SET цена_за_км=%s::numeric, цена_за_час=%s::numeric, минимальная_стоимость=%s::numeric
                WHERE класс=%s
            """
            self.execute_and_display(query, [data["km"], data["hour"], data["min"], data["cls"]],
                                     title="Изменение тарифа", status="Тариф изменён", fetch=False)

    def update_car_class(self):
        data = self.ask_fields("Изменить класс автомобиля", [("id", "Код автомобиля", "1"), ("cls", "Новый класс", "комфорт")])
        if data:
            self.execute_and_display("UPDATE АВТОМОБИЛИ SET класс=%s WHERE код=%s::int", [data["cls"], data["id"]],
                                     title="Изменение класса автомобиля", status="Класс изменён", fetch=False)

    def delete_record_window(self):
        table = simpledialog.askstring("Удаление", "Что удалить? car / driver / client / ride / tariff")
        if not table:
            return
        table = table.lower().strip()
        code = simpledialog.askinteger("Код", "Введите код записи")
        if not code:
            return
        if not messagebox.askyesno("Подтверждение", f"Удалить {table} с кодом {code}?"):
            return
        if table in ["ride", "поездка"]:
            self.execute_and_display("DELETE FROM ПОЕЗДКИ WHERE код_поездки=%s", [code], title="Удаление поездки", status="Удалено", fetch=False)
        elif table in ["client", "клиент"]:
            self.execute_and_display("DELETE FROM ПОЕЗДКИ WHERE клиент=%s; DELETE FROM КЛИЕНТЫ WHERE код=%s", [code, code], title="Удаление клиента", status="Удалено", fetch=False)
        elif table in ["driver", "водитель"]:
            self.execute_and_display("DELETE FROM ПОЕЗДКИ WHERE водитель=%s; DELETE FROM ВОДИТЕЛИ WHERE код=%s", [code, code], title="Удаление водителя", status="Удалено", fetch=False)
        elif table in ["car", "авто", "автомобиль"]:
            self.execute_and_display("DELETE FROM ПОЕЗДКИ WHERE автомобиль=%s; DELETE FROM АВТОМОБИЛИ WHERE код=%s", [code, code], title="Удаление автомобиля", status="Удалено", fetch=False)
        elif table in ["tariff", "тариф"]:
            self.execute_and_display("DELETE FROM ТАРИФЫ WHERE код=%s", [code], title="Удаление тарифа", status="Удалено", fetch=False)
        else:
            messagebox.showerror("Ошибка", "Варианты: car, driver, client, ride, tariff")

    def update_before_after(self):
        data = self.ask_fields("UPDATE до/после", [("id", "Код водителя", "1"), ("rating", "Новый рейтинг", "4.95")])
        if not data:
            return
        driver_id = data["id"]
        new_rating = data["rating"]
        before = self.execute("SELECT * FROM ВОДИТЕЛИ WHERE код=%s::int", [driver_id], title="ДО UPDATE")
        update = self.execute("UPDATE ВОДИТЕЛИ SET рейтинг=%s::numeric WHERE код=%s::int", [new_rating, driver_id], title="UPDATE", fetch=False)
        after = self.execute("SELECT * FROM ВОДИТЕЛИ WHERE код=%s::int", [driver_id], title="ПОСЛЕ UPDATE")
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
            ("Автомобилей", "SELECT COUNT(*) FROM АВТОМОБИЛИ"),
            ("Водителей", "SELECT COUNT(*) FROM ВОДИТЕЛИ"),
            ("Клиентов", "SELECT COUNT(*) FROM КЛИЕНТЫ"),
            ("Тарифов", "SELECT COUNT(*) FROM ТАРИФЫ"),
        ]
        lines = ["Дашборд TAXI", "============", ""]
        for label, query in queries:
            rows, _ = self.fetch_rows(query)
            value = rows[0][0] if rows else "—"
            lines.append(f"{label}: {value}")

        blocks = [
            ("\nТоп-3 класса по выручке", """
                SELECT a.класс, COUNT(*) AS поездок, ROUND(SUM(p.стоимость),2) AS выручка
                FROM ПОЕЗДКИ p JOIN АВТОМОБИЛИ a ON a.код = p.автомобиль
                GROUP BY a.класс
                ORDER BY выручка DESC
                LIMIT 3
            """),
            ("\nТоп-5 водителей по выручке", """
                SELECT v.фамилия || ' ' || v.имя AS водитель,
                       COUNT(p.код_поездки) AS поездок,
                       ROUND(COALESCE(SUM(p.стоимость),0),2) AS выручка
                FROM ВОДИТЕЛИ v LEFT JOIN ПОЕЗДКИ p ON p.водитель = v.код
                GROUP BY v.код, v.фамилия, v.имя
                ORDER BY выручка DESC
                LIMIT 5
            """),
            ("\nПоследние 5 поездок", """
                SELECT p.код_поездки, p.дата, a.гос_номер,
                       v.фамилия AS водитель, p.стоимость
                FROM ПОЕЗДКИ p
                LEFT JOIN АВТОМОБИЛИ a ON a.код = p.автомобиль
                LEFT JOIN ВОДИТЕЛИ v ON v.код = p.водитель
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
            SELECT p.код_поездки, p.дата, a.гос_номер, a.класс,
                   v.фамилия || ' ' || v.имя AS водитель,
                   COALESCE(k.фамилия || ' ', '') || k.имя AS клиент,
                   p.расстояние_км, p.время_мин, p.стоимость
            FROM ПОЕЗДКИ p
            LEFT JOIN АВТОМОБИЛИ a ON a.код = p.автомобиль
            LEFT JOIN ВОДИТЕЛИ v ON v.код = p.водитель
            LEFT JOIN КЛИЕНТЫ k ON k.код = p.клиент
            ORDER BY p.стоимость DESC
            LIMIT %s
        """
        self.execute_and_display(query, [self.get_limit()], title="Самые дорогие поездки", status="Дорогие поездки")

    def long_rides(self):
        query = """
            SELECT p.код_поездки, p.дата, a.гос_номер, a.класс,
                   v.фамилия || ' ' || v.имя AS водитель,
                   p.расстояние_км, p.время_мин, p.стоимость
            FROM ПОЕЗДКИ p
            LEFT JOIN АВТОМОБИЛИ a ON a.код = p.автомобиль
            LEFT JOIN ВОДИТЕЛИ v ON v.код = p.водитель
            ORDER BY p.расстояние_км DESC
            LIMIT %s
        """
        self.execute_and_display(query, [self.get_limit()], title="Самые длинные поездки", status="Длинные поездки")

    def inactive_drivers(self):
        query = """
            SELECT v.код, v.фамилия, v.имя, v.телефон, v.стаж_лет, v.рейтинг
            FROM ВОДИТЕЛИ v
            LEFT JOIN ПОЕЗДКИ p ON p.водитель = v.код
            WHERE p.код_поездки IS NULL
            ORDER BY v.код
        """
        self.execute_and_display(query, title="Водители без поездок", status="Неактивные водители")

    def inactive_cars(self):
        query = """
            SELECT a.код, a.гос_номер, a.марка, a.модель, a.год_выпуска, a.цвет, a.класс
            FROM АВТОМОБИЛИ a
            LEFT JOIN ПОЕЗДКИ p ON p.автомобиль = a.код
            WHERE p.код_поездки IS NULL
            ORDER BY a.код
        """
        self.execute_and_display(query, title="Автомобили без поездок", status="Неиспользуемые авто")

    def data_quality_check(self):
        query = """
            SELECT 'Поездки без автомобиля' AS проверка, COUNT(*) AS найдено FROM ПОЕЗДКИ WHERE автомобиль IS NULL
            UNION ALL SELECT 'Поездки без водителя', COUNT(*) FROM ПОЕЗДКИ WHERE водитель IS NULL
            UNION ALL SELECT 'Поездки без клиента', COUNT(*) FROM ПОЕЗДКИ WHERE клиент IS NULL
            UNION ALL SELECT 'Автомобили без класса', COUNT(*) FROM АВТОМОБИЛИ WHERE класс IS NULL OR класс = ''
            UNION ALL SELECT 'Водители без рейтинга', COUNT(*) FROM ВОДИТЕЛИ WHERE рейтинг IS NULL
            UNION ALL SELECT 'Клиенты без email', COUNT(*) FROM КЛИЕНТЫ WHERE email IS NULL OR email = ''
            UNION ALL SELECT 'Неположительная стоимость', COUNT(*) FROM ПОЕЗДКИ WHERE стоимость <= 0
            UNION ALL SELECT 'Неположительная дистанция', COUNT(*) FROM ПОЕЗДКИ WHERE расстояние_км <= 0
        """
        self.execute_and_display(query, title="Проверка качества данных", status="Проверка связей")

    def chart_driver_revenue(self):
        query = """
            SELECT v.фамилия || ' ' || v.имя AS водитель,
                   ROUND(COALESCE(SUM(p.стоимость),0),2) AS выручка
            FROM ВОДИТЕЛИ v
            LEFT JOIN ПОЕЗДКИ p ON p.водитель = v.код
            GROUP BY v.код, v.фамилия, v.имя
            ORDER BY выручка DESC
            LIMIT 10
        """
        rows, _ = self.fetch_rows(query)
        if not rows:
            messagebox.showinfo("График", "Нет данных")
            return
        labels = [r[0] for r in rows]
        values = [float(r[1] or 0) for r in rows]
        self.open_bar_chart(labels, values, "Топ-10 водителей по выручке", "Водитель", "Выручка")

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
        self.open_bar_chart(labels, values, "Выручка по дням недели", "День недели", "Выручка")

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

    def add_ride_calculated(self):
        data = self.ask_fields("Добавить поездку с автоматическим расчётом", [
            ("car", "Код автомобиля", "1"),
            ("driver", "Код водителя", "1"),
            ("client", "Код клиента", "1"),
            ("km", "Расстояние, км", "10"),
            ("minutes", "Время, мин", "25"),
            ("date", "Дата/время YYYY-MM-DD HH:MM:SS", "2026-06-24 12:00:00"),
        ])
        if not data:
            return
        rows, _ = self.fetch_rows("""
            SELECT a.класс, t.цена_за_км, t.цена_за_час, t.минимальная_стоимость
            FROM АВТОМОБИЛИ a
            JOIN ТАРИФЫ t ON t.класс = a.класс
            WHERE a.код = %s::int
        """, [data["car"]])
        if not rows:
            messagebox.showerror("Ошибка", "Для выбранного автомобиля не найден тариф по классу")
            return
        _, price_km, price_hour, min_price = rows[0]
        km = float(data["km"])
        minutes = int(data["minutes"])
        cost = max(float(min_price), km * float(price_km) + (minutes / 60) * float(price_hour))
        query = """
            INSERT INTO ПОЕЗДКИ (дата, автомобиль, водитель, клиент, расстояние_км, время_мин, стоимость)
            VALUES (%s::timestamp, %s::int, %s::int, %s::int, %s::numeric, %s::int, %s::numeric)
        """
        self.execute_and_display(query, [data["date"], data["car"], data["driver"], data["client"], data["km"], data["minutes"], round(cost, 2)],
                                 title=f"Добавлена поездка. Расчётная стоимость: {round(cost, 2)}", status="Поездка добавлена", fetch=False)
        self.load_autocomplete_data()

    def edit_any_record(self):
        table = simpledialog.askstring("Полное редактирование", "Таблица: АВТОМОБИЛИ / ВОДИТЕЛИ / КЛИЕНТЫ / ТАРИФЫ / ПОЕЗДКИ")
        if not table:
            return
        table = table.strip().upper()
        if table not in self.TABLES:
            messagebox.showerror("Ошибка", "Такой таблицы нет в списке GUI")
            return
        pk = "код_поездки" if table == "ПОЕЗДКИ" else "код"
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
                   a.гос_номер, a.марка, a.модель, a.класс,
                   v.фамилия || ' ' || v.имя AS водитель,
                   COALESCE(k.фамилия || ' ', '') || k.имя AS клиент,
                   p.расстояние_км, p.время_мин, p.стоимость
            FROM ПОЕЗДКИ p
            LEFT JOIN АВТОМОБИЛИ a ON a.код = p.автомобиль
            LEFT JOIN ВОДИТЕЛИ v ON v.код = p.водитель
            LEFT JOIN КЛИЕНТЫ k ON k.код = p.клиент;

            CREATE OR REPLACE VIEW taxi_driver_report AS
            SELECT v.код, v.фамилия, v.имя, v.телефон, v.стаж_лет, v.рейтинг,
                   COUNT(p.код_поездки) AS поездок,
                   ROUND(COALESCE(SUM(p.стоимость),0),2) AS выручка,
                   ROUND(COALESCE(AVG(p.стоимость),0),2) AS средний_чек
            FROM ВОДИТЕЛИ v
            LEFT JOIN ПОЕЗДКИ p ON p.водитель = v.код
            GROUP BY v.код, v.фамилия, v.имя, v.телефон, v.стаж_лет, v.рейтинг;

            CREATE OR REPLACE VIEW taxi_client_report AS
            SELECT k.код, k.фамилия, k.имя, k.телефон, k.email,
                   COUNT(p.код_поездки) AS поездок,
                   ROUND(COALESCE(SUM(p.стоимость),0),2) AS сумма,
                   ROUND(COALESCE(AVG(p.стоимость),0),2) AS средний_чек
            FROM КЛИЕНТЫ k
            LEFT JOIN ПОЕЗДКИ p ON p.клиент = k.код
            GROUP BY k.код, k.фамилия, k.имя, k.телефон, k.email;
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

            CREATE OR REPLACE FUNCTION taxi_calc_price(cls text, km numeric, minutes integer)
            RETURNS numeric AS $$
                SELECT ROUND(GREATEST(t.минимальная_стоимость,
                                      km * t.цена_за_км + (minutes::numeric / 60) * t.цена_за_час), 2)
                FROM ТАРИФЫ t
                WHERE t.класс = cls;
            $$ LANGUAGE SQL;
        """
        self.execute_and_display(query, title="SQL-функции созданы", status="Функции созданы", fetch=False)

    def functions_demo(self):
        data = self.ask_fields("Демо функций", [
            ("driver", "Код водителя", "1"),
            ("client", "Код клиента", "1"),
            ("cls", "Класс", "эконом"),
            ("km", "Километры", "10"),
            ("minutes", "Минуты", "25"),
        ])
        if not data:
            return
        query = """
            SELECT taxi_driver_revenue(%s::int) AS выручка_водителя,
                   taxi_client_spent(%s::int) AS сумма_клиента,
                   taxi_calc_price(%s, %s::numeric, %s::int) AS расчёт_стоимости
        """
        self.execute_and_display(query, [data["driver"], data["client"], data["cls"], data["km"], data["minutes"]],
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

    def show_about(self):
        messagebox.showinfo(
            "О программе",
            "TAXI: система управления поездками\n"
            "GUI для таблиц: автомобили, водители, клиенты, тарифы, поездки, сезон.\n\n"
            "Реализовано: просмотр, фильтры, поиск, рейтинги, аналитика, графики, CRUD,\n"
            "UPDATE/DELETE до-после, экспорт, бэкап и запуск SQL-файлов."
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = TaxiApp(root)
    root.mainloop()
