"""Запуск скриптов: представления и функции из queries/, SQL-файлы проекта,
./help.sh и ./python_reports.sh, экспорт в CSV и бэкап."""

import csv
import os
import shutil
import subprocess
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, simpledialog

from psycopg2 import sql as psql

from scripts.db_config import DB_CONFIG

from . import sql

SQL_DIRS = ["schema", "data", "helper", "queries", "setup"]

# Окно команд ./help.sh: (раздел, [(команда, описание, поля ввода или None)]).
# Поля: [(ключ, подпись, значение по умолчанию)] — значения идут параметрами команды по порядку.
CODE = [("code", "Код водителя", "1")]
HELP_SECTIONS = [
    ("Данные", [
        ("fetch", "Скачать недостающие дни из открытых данных Чикаго", None),
        ("load", "Загрузить скачанные поездки в базу (только новые дни)", None),
    ]),
    ("Основные задачи", [
        ("task1", "Выручка по сезонам", None),
        ("task2", "Выручка по сезонам и таксопаркам", None),
        ("task3", "Выручка по дням недели и водителям", None),
        ("task4", "Выручка по водителям за выбранный день", [("day", "День недели: 1 — пн ... 7 — вс", "1")]),
    ]),
    ("Просмотр данных", [
        ("companies", "Все таксопарки", None),
        ("drivers", "Водители (первые 50)", None),
        ("clients", "Типы клиентов", None),
        ("count", "Количество поездок", None),
        ("latest", "Последние поездки", None),
        ("clients-rides", "Типы клиентов с числом поездок", None),
        ("tables", "Структура таблиц", None),
    ]),
    ("JOIN", [
        ("join-inner", "INNER JOIN", None),
        ("join-left", "LEFT JOIN", None),
        ("join-right", "RIGHT JOIN", None),
        ("join-full", "FULL JOIN", None),
        ("join-cross", "CROSS JOIN", None),
        ("join-self", "SELF JOIN", None),
    ]),
    ("Показать до/после", [
        ("update-before", "ДО UPDATE", None),
        ("update-do", "Выполнить UPDATE", None),
        ("update-after", "ПОСЛЕ UPDATE", None),
        ("delete-before", "ДО DELETE", None),
        ("delete-do", "Выполнить DELETE", None),
        ("delete-after", "ПОСЛЕ DELETE", None),
    ]),
    ("Аналитика", [
        ("top-areas", "Топ-10 районов по выручке", None),
        ("top-drivers", "Топ-10 водителей по выручке", None),
        ("by-month", "Выручка по месяцам", None),
        ("avg-check", "Средний чек", None),
        ("by-hour", "Поездки по часам", None),
        ("company-stats", "Статистика по таксопаркам", None),
        ("driver-load", "Загруженность водителей", None),
        ("tips-by-client", "Средние чаевые по типам клиентов", None),
        ("by-weekday", "Выручка по дням недели", None),
        ("revenue-by-client", "Выручка по типам клиентов", None),
        ("distance-by-company", "Средний пробег по таксопаркам", None),
        ("hour-share", "Распределение поездок по часам", None),
        ("check-by-hour", "Средний чек по часам", None),
        ("top-tips", "Топ-10 водителей по чаевым", None),
    ]),
    ("Запросы с параметрами", [
        ("find-company", "Таксопарки по части названия", [("text", "Часть названия", "Cab")]),
        ("driver", "Информация о водителе", CODE),
        ("driver-rides", "Последние поездки водителя", CODE),
        ("rides-above", "Поездки дороже суммы", [("amount", "Сумма $", "100")]),
        ("drivers-above", "Водители с выручкой выше суммы", [("amount", "Сумма $", "10000")]),
        ("rename-company", "Переименовать таксопарк", [("code", "Код таксопарка", "1"), ("name", "Новое название", "")]),
        ("client-desc", "Изменить описание типа клиента", [("code", "Код типа клиента", "1"), ("desc", "Новое описание", "")]),
        ("delete-driver", "Удалить водителя вместе с поездками", [("code", "Код водителя", "32")]),
        ("add-company", "Добавить таксопарк", [("name", "Название", "Новый таксопарк")]),
        ("add-driver", "Добавить водителя", [("taxi_id", "taxi_id (до 16 символов)", "manual00000001")]),
        ("set-ride-company", "Сменить таксопарк поездки", [("ride", "Код поездки", "1"), ("company", "Код таксопарка", "1")]),
        ("set-tips", "Изменить чаевые поездки", [("ride", "Код поездки", "1"), ("tips", "Чаевые $", "2.00")]),
    ]),
    ("Представления и подзапросы", [
        ("view-user", "Создать пользовательское представление", None),
        ("view-tech", "Создать технологическое представление", None),
        ("view-check", "Проверить представления", None),
        ("sub-deviation", "Отклонение стоимости поездки", None),
        ("sub-company-rating", "Рейтинг таксопарков", None),
        ("sub-above-company-avg", "Поездки дороже среднего по таксопарку", None),
        ("sub-company-stats", "Статистика по таксопаркам", None),
        ("sub-top3", "Топ-3 водителя в каждом таксопарке", None),
        ("sub-above-driver-avg", "Поездки дороже среднего по водителю", CODE),
        ("sub-good-drivers", "Водители без поездок дешевле $10", None),
        ("sub-best-drivers", "Лучшие водители", None),
        ("sub-expensive", "Самые дорогие поездки", None),
        ("sub-all", "Выполнить все запросы с подзапросами", None),
    ]),
    ("Функции", [
        ("func-create", "Создать все функции", None),
        ("func-drivers-above", "Водители с выручкой выше порога", [("amount", "Порог $", "10000")]),
        ("func-company-season", "Выручка по таксопаркам и сезонам", None),
        ("func-pivot", "Сводная таблица водители × способы оплаты", None),
        ("func-all", "Выполнить всё по функциям", None),
    ]),
]
# долгие команды: скачивание и загрузка данных
HELP_TIMEOUTS = {"fetch": 1800, "load": 600}
# команды, перед которыми нужно подтверждение
HELP_CONFIRM = {"delete-driver": "Удалить водителя с кодом {0} вместе с его поездками?"}

DRIVER_OPT = ("driver", "Код водителя, можно пусто", "")
CLIENT_OPT = ("cls", "Тип клиента, можно пусто", "")


def find_bash():
    """bash из Git for Windows: в System32 может лежать bash.exe от WSL, он не подходит."""
    git = shutil.which("git")
    if git:
        for parent in Path(git).resolve().parents:
            candidate = parent / "bin" / "bash.exe"
            if candidate.exists():
                return str(candidate)
    return shutil.which("bash") or "bash"


def pg_env():
    env = os.environ.copy()
    if DB_CONFIG.get("password"):
        env["PGPASSWORD"] = str(DB_CONFIG.get("password"))
    return env


def pg_args():
    return ["-h", str(DB_CONFIG.get("host", "localhost")),
            "-p", str(DB_CONFIG.get("port", 5432)),
            "-U", str(DB_CONFIG.get("user", "postgres"))]


class ScriptsMixin:

    # ------------------------- представления и функции из queries/ -------------------------
    def create_views(self):
        error = self.run_project_files(sql.VIEW_FILES)
        self.display(f"Ошибка SQL: {error}\n" if error else
                     "Представления v_rides_user и v_rides_tech созданы из queries/views/.\n")
        self.set_status("Views созданы" if not error else "Ошибка создания views")

    def check_views(self):
        # ./help.sh rebuild создаёт представления; если их нет (например, после ручного DROP), они пересоздаются
        rows, _ = self.fetch_rows(sql.MISSING_VIEWS, [sql.PROJECT_VIEWS])
        note = ""
        if rows:
            error = self.run_project_files(sql.VIEW_FILES)
            if error:
                self.display(f"Ошибка SQL: {error}\n")
                return
            note = "Пересозданы отсутствовавшие представления: " + ", ".join(r[0] for r in rows) + "\n\n"
        self.display(note + self.execute(sql.CHECK_VIEWS, title="Проверка представлений"))
        self.set_status("Views проверены")

    def create_functions(self):
        error = self.run_project_files(sql.FUNCTION_FILES)
        self.display(f"Ошибка SQL: {error}\n" if error else
                     "Функции из queries/functions/ созданы: get_driver_revenue, drivers_above_revenue,\n"
                     "get_company_avg_revenue, revenue_by_company_and_season,\n"
                     "get_driver_revenue_by_payment, display_pivot_table.\n")
        self.set_status("Функции созданы" if not error else "Ошибка создания функций")

    def functions_demo(self):
        companies = self.autocomplete.get("таксопарк") or ["Flash Cab"]
        default_company = "Flash Cab" if "Flash Cab" in companies else companies[0]
        data = self.ask_fields("Демо функций", [
            ("driver", "Код водителя", "1"),
            ("company", "Таксопарк (точное название)", default_company),
            ("client", "Способ оплаты (тип: Cash, Credit Card ...)", "Credit Card"),
            ("km", "Километры для оценки цены", "10"),
            ("minutes", "Минуты для оценки цены", "25"),
        ])
        if data:
            self.execute_and_display(sql.FUNCTIONS_DEMO, data, title="Демонстрация SQL-функций из queries/functions",
                                     status="Демо функций")

    # ------------------------- экспорт и бэкап -------------------------
    def _write_csv(self, path, cols, rows):
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(cols)
            writer.writerows(rows)

    def export_current_csv(self):
        if not self.last_cols:
            messagebox.showinfo("Экспорт", "Сначала выполните отчёт или откройте таблицу")
            return
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not filename:
            return
        try:
            self._write_csv(filename, self.last_cols, self.last_rows)
            messagebox.showinfo("Экспорт", f"Сохранено: {filename}")
        except OSError as e:
            messagebox.showerror("Ошибка", str(e))

    def export_all_tables_csv(self):
        directory = filedialog.askdirectory(title="Куда сохранить CSV-файлы")
        if not directory:
            return
        saved = 0
        for table in sql.TABLES:
            rows, cols = self.fetch_rows(psql.SQL("SELECT * FROM {}").format(psql.Identifier(table)))
            if not cols:
                break
            try:
                self._write_csv(Path(directory) / f"{table}.csv", cols, rows)
            except OSError as e:
                messagebox.showerror("Ошибка", str(e))
                return
            saved += 1
        messagebox.showinfo("Экспорт", f"Экспортировано таблиц: {saved}")

    def backup_db(self):
        filename = filedialog.asksaveasfilename(defaultextension=".dump",
                                                filetypes=[("PostgreSQL dump", "*.dump"), ("All files", "*.*")])
        if not filename:
            return
        cmd = ["pg_dump", *pg_args(), "-Fc", "-f", filename, str(DB_CONFIG.get("dbname", "taxi"))]
        try:
            subprocess.run(cmd, env=pg_env(), check=True, capture_output=True, text=True)
            messagebox.showinfo("Бэкап", f"Бэкап создан: {filename}")
        except Exception as e:
            messagebox.showerror("Ошибка бэкапа", str(e))

    # ------------------------- SQL-файлы проекта -------------------------
    def find_project_sql_files(self):
        root = self.project_root()
        files = set()
        for folder in SQL_DIRS:
            base = root / folder
            if base.exists():
                files.update(base.rglob("*.sql"))
        return sorted(files, key=lambda p: str(p.relative_to(root)).lower())

    def prepare_sql_with_params(self, sql_text, params_text=None):
        """Подстановка параметров $1, $2, :param1, :1 в SQL-файл (значения в кавычках)."""
        if params_text is None:
            if any(marker in sql_text for marker in ("$1", ":param1", ":1")):
                params_text = simpledialog.askstring(
                    "Параметры SQL-файла",
                    "Введите параметры через пробел. Например: Flash 12\nМожно оставить пустым:",
                    parent=self.root,
                )
            params_text = params_text or ""
        prepared = sql_text
        for idx, value in enumerate(params_text.split(), start=1):
            quoted = "'" + value.replace("'", "''") + "'"
            for marker in (f"$${idx}", f"${idx}", f":param{idx}", f":{idx}"):
                prepared = prepared.replace(marker, quoted)
        return prepared

    def run_project_sql_file(self, path, use_psql=False):
        """Выполняет SQL-файл проекта и выводит результат в главное окно."""
        path = Path(path)
        if not path.exists():
            messagebox.showerror("SQL-файл", f"Файл не найден:\n{path}")
            return
        if use_psql:
            self.run_project_sql_file_psql(path)
            return
        sql_text = self.prepare_sql_with_params(self.read_sql_text(path))
        title = f"SQL-файл проекта: {path.relative_to(self.project_root())}"
        self.display(self.execute(sql_text, title=title))
        self.set_status(f"Выполнен SQL-файл: {path.name}")

    def run_project_sql_file_psql(self, path):
        """Запуск через psql — для файлов с командами psql (\\echo, \\set и т. п.)."""
        path = Path(path)
        cmd = ["psql", *pg_args(), "-d", str(DB_CONFIG.get("dbname", "")), "-f", str(path)]
        try:
            proc = subprocess.run(cmd, env=pg_env(), capture_output=True, text=True,
                                  encoding="utf-8", errors="replace")
        except FileNotFoundError:
            messagebox.showerror("psql", "Команда psql не найдена. Проверьте установку PostgreSQL и PATH.")
            return
        title = f"psql: {path.relative_to(self.project_root())}"
        out = [title, "=" * len(title), ""]
        if proc.stdout:
            out.append(proc.stdout)
        if proc.stderr:
            out.append("\nСообщения/ошибки psql:\n" + proc.stderr)
        out.append(f"\nКод завершения: {proc.returncode}")
        self.display("\n".join(out))
        self.set_status(f"psql выполнен: {path.name}")

    def run_sql_directory(self):
        """Запускает все SQL-файлы выбранной папки по порядку."""
        root = self.project_root()
        directory = filedialog.askdirectory(initialdir=str(root), title="Выберите папку с SQL-файлами")
        if not directory:
            return
        folder = Path(directory)
        files = sorted(folder.rglob("*.sql"))
        if not files:
            messagebox.showinfo("SQL-папка", "В выбранной папке нет .sql файлов.")
            return
        if not messagebox.askyesno(
            "Запуск папки SQL",
            f"Будет выполнено {len(files)} SQL-файлов из папки:\n{folder}\n\n"
            "Внимание: среди них могут быть INSERT, UPDATE, DELETE или DROP. Продолжить?",
        ):
            return
        reports = []
        for file in files:
            sql_text = self.prepare_sql_with_params(self.read_sql_text(file), params_text="")
            try:
                name = str(file.relative_to(root))
            except ValueError:
                name = str(file)
            reports.append(self.execute(sql_text, title=name))
        self.display("\n\n".join(reports))
        self.set_status(f"Выполнена папка SQL: {folder.name}")

    def run_sql_file(self):
        filename = filedialog.askopenfilename(filetypes=[("SQL files", "*.sql"), ("All files", "*.*")])
        if filename:
            self.display(self.execute(self.read_sql_text(filename), title=f"SQL-файл: {Path(filename).name}"))
            self.set_status("SQL-файл выполнен")

    def sql_scripts_manager(self):
        """Окно навигации по SQL-скриптам проекта: поиск, просмотр, запуск."""
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

        def selected_file():
            sel = listbox.curselection()
            return visible_files[sel[0]] if sel else None

        def show_preview(*_):
            file = selected_file()
            preview.delete("1.0", tk.END)
            if not file:
                preview.insert(tk.END, "Выберите SQL-файл слева.")
                return
            header = f"-- {file.relative_to(root)}\n-- Размер: {file.stat().st_size} байт\n\n"
            preview.insert(tk.END, header + self.read_sql_text(file))

        def refresh_list(*_):
            query = search_var.get().strip().lower()
            listbox.delete(0, tk.END)
            visible_files.clear()
            for file in all_files:
                name = str(file.relative_to(root))
                if not query or query in name.lower():
                    visible_files.append(file)
                    listbox.insert(tk.END, name)
            if visible_files:
                listbox.selection_set(0)
                show_preview()
            else:
                preview.delete("1.0", tk.END)
                preview.insert(tk.END, "SQL-файлы не найдены.")

        def run_selected(use_psql):
            file = selected_file()
            if file:
                self.run_project_sql_file(file, use_psql=use_psql)

        def copy_path():
            file = selected_file()
            if file:
                self.root.clipboard_clear()
                self.root.clipboard_append(str(file))
                self.set_status("Путь к SQL-файлу скопирован")

        actions = ttk.Frame(win, padding=6)
        actions.pack(fill=tk.X)
        ttk.Button(actions, text="Выполнить выбранный SQL", command=lambda: run_selected(False)).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Выполнить через psql", command=lambda: run_selected(True)).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Выполнить папку SQL", command=self.run_sql_directory).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Скопировать путь", command=copy_path).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Обновить список", command=refresh_list).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Закрыть", command=win.destroy).pack(side=tk.RIGHT, padx=4)

        search_var.trace_add("write", refresh_list)
        listbox.bind("<<ListboxSelect>>", show_preview)
        search_entry.bind("<Return>", lambda e: refresh_list())
        refresh_list()

    # ------------------------- ./help.sh и ./python_reports.sh -------------------------
    def run_shell_tool(self, tool_name, args=None, title=None, timeout=180):
        """Запускает ./help.sh или ./python_reports.sh из корня проекта и выводит результат."""
        args = [str(a) for a in (args or []) if str(a) != ""]
        root = self.project_root()
        tool_path = root / tool_name
        if not tool_path.exists():
            messagebox.showerror("Файл не найден", f"Не найден файл {tool_path}")
            return
        cmd = [str(tool_path)] + args
        if os.name == "nt":
            # Windows не запускает .sh напрямую
            cmd = [find_bash()] + cmd
        shown = " ".join(["./" + tool_name] + args)
        self.set_status("Выполняю: " + shown)
        env = os.environ.copy()
        env.setdefault("PYTHONIOENCODING", "utf-8")
        env.setdefault("PGCLIENTENCODING", "UTF8")
        try:
            completed = subprocess.run(cmd, cwd=str(root), capture_output=True, encoding="utf-8",
                                       errors="replace", timeout=timeout, env=env)
        except subprocess.TimeoutExpired:
            self.display(f"Команда выполнялась слишком долго и была остановлена:\n{shown}\n")
            self.set_status("Команда остановлена по таймауту")
            return
        except Exception as e:
            messagebox.showerror("Ошибка запуска", str(e))
            self.set_status("Ошибка запуска команды")
            return
        header = title or shown
        output = [header, "=" * len(header), "Команда: " + shown, f"Код завершения: {completed.returncode}"]
        if completed.stdout:
            output.append("\nSTDOUT:\n" + completed.stdout)
        if completed.stderr:
            output.append("\nSTDERR:\n" + completed.stderr)
        self.last_rows = []
        self.last_cols = []
        self.display("\n".join(output))
        self.set_status("Готово: " + shown)

    def run_h(self, *args, title=None):
        self.run_shell_tool("help.sh", list(args), title=title,
                            timeout=HELP_TIMEOUTS.get(str(args[0]) if args else "", 180))

    def run_python_report(self, *args, title=None):
        self.run_shell_tool("python_reports.sh", list(args), title=title, timeout=240)

    def _help_action(self, command, desc, fields):
        title = f"./help.sh {command} — {desc.lower()}"
        if not fields:
            return lambda: self.run_h(command, title=title)

        def ask_and_run():
            data = self.ask_fields(title, fields)
            if data is None:
                return
            values = [data[key] for key, _, _ in fields]
            confirm = HELP_CONFIRM.get(command)
            if confirm and not messagebox.askyesno("Подтверждение", confirm.format(*values)):
                return
            self.run_h(command, *values, title=title)
        return ask_and_run

    def h_commands_window(self):
        _, body = self.make_scrollable_window("Команды ./help.sh — полное меню TAXI")
        ttk.Label(
            body,
            text="Команды ./help.sh. Простые запускаются сразу, с параметрами — открывают окно ввода.",
            wraplength=680,
        ).pack(anchor="w", pady=(0, 8))
        for section, commands in HELP_SECTIONS:
            self.add_command_section(body, section, [
                (command, desc, self._help_action(command, desc, fields)) for command, desc, fields in commands
            ])

    def _python_with_fields(self, command, title, fields, extra=()):
        def ask_and_run():
            data = self.ask_fields(title, fields)
            if data is None:
                return
            values = [data[key] for key, _, _ in fields if data[key]]
            self.run_python_report(command, *values, *extra, title=title)
        return ask_and_run

    def python_commands_window(self):
        _, body = self.make_scrollable_window("Команды ./python_reports.sh — отчёты TAXI", width=720, height=560)
        ttk.Label(
            body,
            text="Эти кнопки запускают ./python_reports.sh. Графики сохраняются в docs/ проекта.",
            wraplength=640,
        ).pack(anchor="w", pady=(0, 8))
        p = "./python_reports.sh"
        self.add_command_section(body, "Отчёты", [
            ("python_reports.sh 1", "Отчёт по водителям и типам клиентов; оба параметра необязательны",
             self._python_with_fields("1", f"{p} 1", [DRIVER_OPT, CLIENT_OPT])),
            ("python_reports.sh 1s", "Отчёт со звёздочкой * в углу",
             self._python_with_fields("1s", f"{p} 1s", [DRIVER_OPT, CLIENT_OPT])),
            ("python_reports.sh 2", "Сводная таблица; тип клиента необязателен",
             self._python_with_fields("2", f"{p} 2", [CLIENT_OPT])),
            # из GUI график всегда строится заново, без вопроса о перезаписи
            ("python_reports.sh 3", "График динамики",
             lambda: self.run_python_report("3", "--force", title=f"{p} 3 --force — график динамики")),
            ("python_reports.sh 4", "Круговая диаграмма; водитель необязателен",
             self._python_with_fields("4", f"{p} 4 --force", [DRIVER_OPT], extra=["--force"])),
        ])
        self.add_command_section(body, "Пакетный запуск и сохранение", [
            ("python_reports.sh all", "Выполнить всё", lambda: self.run_python_report("all", title=f"{p} all")),
            ("python_reports.sh save", "Сохранить все графики", lambda: self.run_python_report("save", title=f"{p} save")),
            ("python_reports.sh save --force", "Сохранить все графики с перезаписью",
             lambda: self.run_python_report("save", "--force", title=f"{p} save --force")),
        ])
        self.add_command_section(body, "Дополнительно", [
            ("Открыть docs", "Показать папку docs с графиками", self.open_docs_folder),
            ("Показать меню python_reports.sh", "Запустить ./python_reports.sh без параметров",
             lambda: self.run_python_report(title=f"{p} — меню")),
        ])

    def open_docs_folder(self):
        docs = self.project_root() / "docs"
        docs.mkdir(exist_ok=True)
        try:
            if os.name == "nt":
                os.startfile(docs)  # noqa: S606 — открыть папку в Проводнике
            else:
                subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", str(docs)], check=False)
            self.set_status(f"Открыта папка {docs}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
