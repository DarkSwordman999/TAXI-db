"""Общая основа окна: подключение к БД, выполнение запросов, вывод таблиц, диалоги и графики."""

from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # noqa: E402

import psycopg2  # noqa: E402

from scripts.db_config import DB_CONFIG  # noqa: E402

# корень проекта: app/taxi_gui/base.py -> на два уровня выше
PROJECT_ROOT = Path(__file__).resolve().parents[2]
MAX_SHOWN_ROWS = 1000


class BaseMixin:
    """Методы, которыми пользуются все разделы GUI."""

    # ------------------------- подключение -------------------------
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

    def project_root(self):
        return PROJECT_ROOT

    # ------------------------- вывод -------------------------
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
        """Таблица псевдографикой; запоминает строки для экспорта в CSV."""
        self.last_rows = rows or []
        self.last_cols = cols or []
        if not rows:
            return (title + "\n\n" if title else "") + "Нет данных.\n"

        shown = [["" if v is None else str(v) for v in row] for row in rows[:MAX_SHOWN_ROWS]]
        widths = [len(str(c)) for c in cols]
        for row in shown:
            for i, val in enumerate(row):
                widths[i] = max(widths[i], len(val))
        widths = [min(w, 34) for w in widths]

        def line(values):
            return "│" + "│".join(f" {str(v)[:w].ljust(w)} " for v, w in zip(values, widths)) + "│"

        out = []
        if title:
            out += [title, "=" * len(title)]
        out.append("┌" + "┬".join("─" * (w + 2) for w in widths) + "┐")
        out.append(line(cols))
        out.append("├" + "┼".join("─" * (w + 2) for w in widths) + "┤")
        out += [line(row) for row in shown]
        out.append("└" + "┴".join("─" * (w + 2) for w in widths) + "┘")
        out.append(f"\nВсего строк: {len(rows)}")
        if len(rows) > MAX_SHOWN_ROWS:
            out.append(f"Показаны первые {MAX_SHOWN_ROWS} строк.")
        return "\n".join(out) + "\n"

    # ------------------------- запросы -------------------------
    def execute(self, query, params=None, title="", fetch=True):
        """Выполняет запрос и возвращает текст для окна результата."""
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
        self.display(self.execute(query, params=params, title=title, fetch=fetch))
        self.set_status(status)

    def fetch_rows(self, query, params=None, show_error=True):
        """Возвращает (rows, cols) для внутренних расчётов и графиков."""
        if not self.conn:
            if show_error:
                messagebox.showerror("Ошибка", "Нет подключения к БД")
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
            if show_error:
                messagebox.showerror("Ошибка SQL", str(e))
            return [], []

    def read_sql_text(self, path):
        """Читает SQL-файл: UTF-8, при неудаче — cp1251."""
        path = Path(path)
        for enc in ("utf-8", "utf-8-sig", "cp1251"):
            try:
                return path.read_text(encoding=enc)
            except UnicodeDecodeError:
                continue
        return path.read_text(encoding="utf-8", errors="replace")

    def run_project_files(self, files):
        """Выполняет SQL-файлы проекта (пути от корня) одной транзакцией. Возвращает текст ошибки или None."""
        if not self.conn:
            return "Нет подключения к БД"
        try:
            with self.conn.cursor() as cur:
                for rel in files:
                    cur.execute(self.read_sql_text(PROJECT_ROOT / rel))
            self.conn.commit()
            return None
        except Exception as e:
            self.conn.rollback()
            return str(e)

    # ------------------------- окна и элементы -------------------------
    def add_button_group(self, parent, title, buttons):
        frame = ttk.LabelFrame(parent, text=title, padding=6)
        frame.pack(fill=tk.X, pady=4)
        for text, command in buttons:
            ttk.Button(frame, text=text, command=command).pack(fill=tk.X, pady=2)

    def ask_fields(self, title, fields):
        """Модальное окно ввода. fields: [(ключ, подпись, значение по умолчанию)]. None — отмена."""
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("430x" + str(90 + len(fields) * 38))
        win.transient(self.root)
        win.grab_set()
        values = {}
        entries = []
        for i, (key, label, default) in enumerate(fields):
            ttk.Label(win, text=label).grid(row=i, column=0, sticky="w", padx=10, pady=6)
            var = tk.StringVar(value=str(default or ""))
            entry = ttk.Entry(win, textvariable=var, width=34)
            entry.grid(row=i, column=1, sticky="w", padx=10, pady=6)
            values[key] = var
            entries.append(entry)
        result = {"ok": False}

        def ok():
            result["ok"] = True
            win.destroy()

        btns = ttk.Frame(win)
        btns.grid(row=len(fields), column=0, columnspan=2, pady=12)
        ttk.Button(btns, text="OK", command=ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btns, text="Отмена", command=win.destroy).pack(side=tk.LEFT, padx=5)
        if entries:
            entries[0].focus_set()
        self.root.wait_window(win)
        if not result["ok"]:
            return None
        return {k: v.get().strip() for k, v in values.items()}

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
        """Раздел окна команд: [(надпись кнопки, описание, действие)]."""
        section = ttk.LabelFrame(parent, text=title, padding=8)
        section.pack(fill=tk.X, pady=6)
        for label, desc, action in items:
            row = ttk.Frame(section)
            row.pack(fill=tk.X, pady=2)
            ttk.Button(row, text=label, command=action, width=22).pack(side=tk.LEFT, padx=(0, 8))
            ttk.Label(row, text=desc, wraplength=470, justify=tk.LEFT).pack(side=tk.LEFT, fill=tk.X, expand=True)

    # ------------------------- графики -------------------------
    def _chart_window(self, title, size, fig):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry(size)
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.set_status(title)

    def open_line_chart(self, x, y, title, xlabel, ylabel):
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(x, y, marker="o", linewidth=2)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)
        fig.autofmt_xdate()
        self._chart_window(title, "850x540", fig)

    def open_bar_chart(self, labels, values, title, xlabel, ylabel):
        fig, ax = plt.subplots(figsize=(9, 5.2))
        ax.bar(labels, values)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True, axis="y", alpha=0.3)
        ax.tick_params(axis="x", labelrotation=35)
        for label in ax.get_xticklabels():
            label.set_horizontalalignment("right")
        self._chart_window(title, "900x560", fig)

    def open_pie_chart(self, labels, sizes, title):
        # доли меньше 3% (редкие способы оплаты) — одним сектором, иначе подписи налезают друг на друга
        total = sum(sizes)
        small = sum(s for s in sizes if s < total * 0.03)
        if small:
            kept = [(l, s) for l, s in zip(labels, sizes) if s >= total * 0.03]
            labels = [l for l, _ in kept] + ["Прочие"]
            sizes = [s for _, s in kept] + [small]
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.pie(sizes, labels=labels, autopct="%1.1f%%")
        ax.set_title(title)
        self._chart_window(title, "700x600", fig)
