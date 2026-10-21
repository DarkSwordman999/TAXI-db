#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GUI для базы данных TAXI.
Запуск из корня проекта: ./run_app.sh (или python3 app/gui.py).
Настройки подключения — app/scripts/db_config.py.
Здесь только главное окно: меню и кнопки. Действия — в пакете taxi_gui/.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

from taxi_gui.analytics import AnalyticsMixin
from taxi_gui.base import BaseMixin, monospace_font
from taxi_gui.browse import BrowseMixin, FILTER_FIELDS
from taxi_gui.editing import EditingMixin
from taxi_gui.scripts import ScriptsMixin


class TaxiApp(BrowseMixin, AnalyticsMixin, EditingMixin, ScriptsMixin, BaseMixin):

    def __init__(self, root):
        self.root = root
        self.root.title("TAXI: поездки такси Чикаго")
        self.root.geometry("1420x860")
        self.root.minsize(1100, 700)

        self.conn = None
        self.last_rows = []
        self.last_cols = []
        self.autocomplete = {}
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
        db_menu.add_command(label="Проверить pg_trgm", command=self.ensure_pg_trgm)
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

        left = self.create_scrollable_panel(main, width=260)

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
            ("Способы оплаты", self.top_clients),
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
            ("Проверить pg_trgm", self.ensure_pg_trgm),
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

        def grid(widget, row, column, **kw):
            widget.grid(row=row, column=column, sticky=kw.pop("sticky", "w"), padx=4, pady=3, **kw)
            return widget

        grid(ttk.Label(filters, text="Количество:"), 0, 0)
        grid(ttk.Spinbox(filters, from_=1, to=5000, textvariable=self.limit_var, width=8), 0, 1)

        grid(ttk.Label(filters, text="Фильтр поездок по полю:"), 0, 2)
        field_combo = grid(ttk.Combobox(filters, textvariable=self.filter_field_var, values=FILTER_FIELDS,
                                        width=18, state="readonly"), 0, 3)
        field_combo.bind("<<ComboboxSelected>>", lambda e: self.filter_value_var.set(""))

        grid(ttk.Label(filters, text="Значение:"), 0, 4)
        value_entry = grid(ttk.Entry(filters, textvariable=self.filter_value_var, width=28), 0, 5)
        value_entry.bind("<Return>", lambda e: self.latest_rides())

        grid(ttk.Button(filters, text="Применить", command=self.latest_rides), 0, 6)
        grid(ttk.Button(filters, text="Сбросить", command=self.clear_filters), 0, 7)

        hint = "Примеры: таксопарк = Flash; водитель = 12; откуда = Loop; дата = 2026-03-15; стоимость >= 50"
        ttk.Label(filters, text=hint, foreground="#666").grid(row=1, column=2, columnspan=6, sticky="w", padx=4, pady=1)

        grid(ttk.Label(filters, text="Триграммный поиск:"), 2, 0)
        search_entry = grid(ttk.Entry(filters, textvariable=self.search_var, width=32), 2, 1, columnspan=2)
        search_entry.bind("<Return>", lambda e: self.quick_search())

        grid(ttk.Label(filters, text="Порог:"), 2, 3, sticky="e")
        grid(ttk.Spinbox(filters, from_=0.05, to=1.0, increment=0.05, textvariable=self.similarity_var, width=6), 2, 4)
        grid(ttk.Button(filters, text="Искать похоже", command=self.quick_search), 2, 5)
        grid(ttk.Button(filters, text="Проверить pg_trgm", command=self.ensure_pg_trgm), 2, 6)

        self.result = scrolledtext.ScrolledText(right, wrap=tk.NONE, font=monospace_font(11), state=tk.DISABLED)
        self.result.pack(fill=tk.BOTH, expand=True)

        ttk.Label(right, textvariable=self.status_var, anchor="w").pack(fill=tk.X, pady=(5, 0))

    def create_scrollable_panel(self, parent, width):
        """Левая панель кнопок с прокруткой: на невысоком экране нижние группы иначе обрезаются."""
        outer = ttk.Frame(parent, width=width)
        outer.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        canvas = tk.Canvas(outer, width=width - 18, highlightthickness=0, borderwidth=0,
                           background=ttk.Style().lookup("TFrame", "background"))
        scrollbar = ttk.Scrollbar(outer, orient=tk.VERTICAL, command=canvas.yview)
        inner = ttk.Frame(canvas)
        window = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.Y, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def on_wheel(event):
            if event.num == 4 or event.delta > 0:
                canvas.yview_scroll(-1, "units")
            else:
                canvas.yview_scroll(1, "units")

        # колесо мыши прокручивает панель, только пока курсор над ней
        def bind_wheel(_):
            canvas.bind_all("<MouseWheel>", on_wheel)
            canvas.bind_all("<Button-4>", on_wheel)
            canvas.bind_all("<Button-5>", on_wheel)

        def unbind_wheel(_):
            for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                canvas.unbind_all(seq)

        outer.bind("<Enter>", bind_wheel)
        outer.bind("<Leave>", unbind_wheel)
        return inner

    def show_about(self):
        messagebox.showinfo(
            "О программе",
            "TAXI: поездки такси Чикаго\n"
            "Реальные открытые данные города (Chicago Data Portal, Taxi Trips).\n"
            "Таблицы: таксопарки, водители, способы оплаты, районы, поездки, сезон.\n\n"
            "Реализовано: просмотр, фильтры, поиск, рейтинги, аналитика, графики, CRUD,\n"
            "UPDATE/DELETE до-после, экспорт, бэкап и запуск SQL-файлов."
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = TaxiApp(root)
    root.mainloop()
