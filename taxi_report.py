#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import defaultdict
import os

# настройки подключения общие с GUI: app/scripts/db_config.py
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app'))
from scripts.db_config import DB_CONFIG

# папка для графиков; автотесты подменяют её через TAXI_DOCS_DIR, чтобы не трогать docs/
DOCS_DIR = os.environ.get('TAXI_DOCS_DIR') or 'docs'
os.makedirs(DOCS_DIR, exist_ok=True)

def get_connection():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.Error as e:
        print(f"Ошибка подключения: {e}")
        sys.exit(1)

def file_exists(filename, force=False):
    if not force and os.path.exists(filename):
        # без терминала (GUI, автотесты, конвейер) спросить некого, а input() ждал бы вечно
        if not sys.stdin or not sys.stdin.isatty():
            print(f"Файл {filename} уже существует; для перезаписи добавьте --force")
            return True
        try:
            response = input(f"Файл {filename} уже существует. Перезаписать? (y/N): ")
        except EOFError:
            print(f"\nФайл {filename} уже существует; для перезаписи добавьте --force")
            return True
        return response.lower() != 'y'
    return False

def print_header(col_widths, headers, alignments):
    print('┌' + '┬'.join('─' * (w + 2) for w in col_widths) + '┐')
    row = '│'
    for i, h in enumerate(headers):
        if alignments[i] == 'r':
            row += f' {h:>{col_widths[i]}} │'
        else:
            row += f' {h:<{col_widths[i]}} │'
    print(row)
    print('├' + '┼'.join('─' * (w + 2) for w in col_widths) + '┤')

def print_row(cells, col_widths, alignments):
    row = '│'
    for i, cell in enumerate(cells):
        if alignments[i] == 'r':
            row += f' {str(cell):>{col_widths[i]}} │'
        else:
            row += f' {str(cell):<{col_widths[i]}} │'
    print(row)

def print_separator(col_widths):
    print('├' + '┼'.join('─' * (w + 2) for w in col_widths) + '┤')

def print_footer(col_widths, star_bottom=False):
    if star_bottom:
        # Вместо левого нижнего угла ставим звездочку
        print('*' + '┴'.join('─' * (w + 2) for w in col_widths) + '┘')
    else:
        print('└' + '┴'.join('─' * (w + 2) for w in col_widths) + '┘')

DRIVERS_SQL = """
    WITH водители AS (
        -- конкретный водитель по коду или 15 водителей с наибольшей выручкой
        SELECT В.код
        FROM ВОДИТЕЛИ В
        JOIN ПОЕЗДКИ П ON П.водитель = В.код
        WHERE %(driver)s::int IS NULL OR В.код = %(driver)s::int
        GROUP BY В.код
        ORDER BY SUM(П.стоимость) DESC
        LIMIT 15
    )
    SELECT
        'Водитель №' || d.код AS водитель,
        к.описание AS способ_оплаты,
        COALESCE(SUM(p.стоимость), 0) AS выручка,
        COUNT(p.код_поездки) AS количество_поездок
    FROM водители d
    CROSS JOIN ОПЛАТА к
    LEFT JOIN ПОЕЗДКИ p ON p.водитель = d.код AND p.оплата = к.код
    WHERE %(client)s::text IS NULL
       OR к.описание ILIKE %(client)s OR к.тип ILIKE %(client)s
    GROUP BY d.код, к.описание
    ORDER BY d.код, к.описание
"""


def driver_code(driver_param):
    """Код водителя из параметра: "12" или "Водитель №12"."""
    if not driver_param:
        return None
    digits = "".join(ch for ch in driver_param if ch.isdigit())
    if not digits:
        print(f"Водитель задаётся кодом, например 12; получено: {driver_param}")
        sys.exit(1)
    return int(digits)


def fetch_driver_client_rows(cur, driver_param=None, class_param=None):
    cur.execute(DRIVERS_SQL, {"driver": driver_code(driver_param),
                              "client": f"%{class_param}%" if class_param else None})
    return cur.fetchall()


def task1_report(driver_param=None, class_param=None, star_bottom=False):
    conn = get_connection()
    cur = conn.cursor()
    
    rows = fetch_driver_client_rows(cur, driver_param, class_param)
    
    print()
    print('=' * 70)
    if star_bottom:
        print('  ОТЧЁТ: ВЫРУЧКА ПО ВОДИТЕЛЯМ И СПОСОБАМ ОПЛАТЫ *')
    else:
        print('  ОТЧЁТ: ВЫРУЧКА ПО ВОДИТЕЛЯМ И СПОСОБАМ ОПЛАТЫ')
    print('=' * 70)
    if driver_param:
        print(f'  Параметр: водитель = {driver_param}')
    if class_param:
        print(f'  Параметр: способ оплаты = {class_param}')
    if not driver_param:
        print('  15 водителей с наибольшей выручкой, суммы в $')
    print('-' * 70)
    
    if not rows:
        print("  Данные не найдены")
        cur.close()
        conn.close()
        return
    
    col_widths = [4, 16, 22, 14, 8]
    headers = ['№', 'Водитель (x)', 'Способ оплаты (y)', 'Выручка (F)', 'Поездок']
    alignments = ['r', 'l', 'l', 'r', 'r']
    
    print_header(col_widths, headers, alignments)
    
    current_driver = None
    driver_total = 0
    driver_count = 0
    grand_total = 0
    grand_count = 0
    global_row_num = 1
    
    for driver, class_name, revenue, rides in rows:
        revenue = float(revenue)
        rides = int(rides)
        
        if current_driver != driver:
            if current_driver is not None:
                print_row(['', current_driver[:20], 'ИТОГ:', f'{driver_total:.2f}', str(driver_count)], col_widths, alignments)
                print_separator(col_widths)
            
            current_driver = driver
            driver_total = 0
            driver_count = 0
        
        print_row([global_row_num, driver[:20], class_name, f'{revenue:.2f}', str(rides)], col_widths, alignments)
        
        driver_total += revenue
        driver_count += rides
        grand_total += revenue
        grand_count += rides
        global_row_num += 1
    
    if current_driver is not None:
        print_row(['', current_driver[:20], 'ИТОГ:', f'{driver_total:.2f}', str(driver_count)], col_widths, alignments)
        print_separator(col_widths)
    
    print_row(['', 'ВСЕГО', '', f'{grand_total:.2f}', str(grand_count)], col_widths, alignments)
    print_footer(col_widths, star_bottom)
    
    cur.close()
    conn.close()

def task1_star_report(driver_param=None, class_param=None):
    """Отчет со звездочкой вместо левого нижнего угла"""
    task1_report(driver_param, class_param, star_bottom=True)

def task2_pivot_table(class_param=None):
    conn = get_connection()
    cur = conn.cursor()
    
    rows = fetch_driver_client_rows(cur, class_param=class_param)
    
    data_T = {}
    data_nT = {}
    drivers_set = set()
    classes_set = set()
    
    for driver, class_name, revenue, rides in rows:
        revenue = float(revenue)
        rides = int(rides)
        if driver not in data_T:
            data_T[driver] = {}
            data_nT[driver] = {}
        data_T[driver][class_name] = revenue
        data_nT[driver][class_name] = rides
        drivers_set.add(driver)
        classes_set.add(class_name)
    
    drivers = sorted(drivers_set, key=lambda d: int(d.split('№')[1]))
    classes = sorted(classes_set)
    
    print()
    print('=' * 70)
    print('  СВОДНАЯ ТАБЛИЦА: ВЫРУЧКА (T) И КОЛИЧЕСТВО ПОЕЗДОК (nT)')
    print('=' * 70)
    if class_param:
        print(f'  Параметр: способ оплаты = {class_param}')
    print('  15 водителей с наибольшей выручкой, суммы в $')
    print('-' * 70)
    
    col_widths = [4, 16] + [max(12, len(c)) for c in classes] + [12]
    headers = ['№', 'Водитель (x)'] + [c for c in classes] + ['Итого']
    alignments = ['r', 'l'] + ['r'] * (len(classes) + 1)
    
    print()
    print("  [МАТРИЦА T: ВЫРУЧКА]")
    print_header(col_widths, headers, alignments)
    
    class_totals = defaultdict(float)
    
    for i, driver in enumerate(drivers, 1):
        row = [i, driver[:20]]
        driver_total = 0
        for class_name in classes:
            val = data_T.get(driver, {}).get(class_name, 0)
            row.append(f'{val:.2f}')
            driver_total += val
            class_totals[class_name] += val
        row.append(f'{driver_total:.2f}')
        print_row(row, col_widths, alignments)
    
    print_separator(col_widths)
    total_row = ['', 'ИТОГ по столбцам']
    for class_name in classes:
        total_row.append(f'{class_totals[class_name]:.2f}')
    total_row.append(f'{sum(class_totals.values()):.2f}')
    print_row(total_row, col_widths, alignments)
    print_footer(col_widths)
    
    print()
    print("  [МАТРИЦА nT: КОЛИЧЕСТВО ПОЕЗДОК]")
    print_header(col_widths, headers, alignments)
    
    class_totals_nT = defaultdict(int)
    
    for i, driver in enumerate(drivers, 1):
        row = [i, driver[:20]]
        driver_total = 0
        for class_name in classes:
            val = data_nT.get(driver, {}).get(class_name, 0)
            row.append(f'{int(val)}')
            driver_total += val
            class_totals_nT[class_name] += val
        row.append(f'{int(driver_total)}')
        print_row(row, col_widths, alignments)
    
    print_separator(col_widths)
    total_row_nT = ['', 'ИТОГ по столбцам']
    for class_name in classes:
        total_row_nT.append(f'{int(class_totals_nT[class_name])}')
    total_row_nT.append(f'{int(sum(class_totals_nT.values()))}')
    print_row(total_row_nT, col_widths, alignments)
    print_footer(col_widths)
    
    cur.close()
    conn.close()

def task3_chart(force=False):
    conn = get_connection()
    cur = conn.cursor()
    
    sql = """
    SELECT 
        DATE_TRUNC('month', дата) as месяц,
        SUM(стоимость) as выручка,
        COUNT(*) as поездок
    FROM ПОЕЗДКИ
    WHERE дата IS NOT NULL
    GROUP BY DATE_TRUNC('month', дата)
    ORDER BY месяц
    """
    
    cur.execute(sql)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    if not rows:
        print("Нет данных для построения графика")
        return
    
    months = [row[0] for row in rows]
    revenues = [float(row[1]) for row in rows]
    rides = [int(row[2]) for row in rows]
    
    fig, ax1 = plt.subplots(figsize=(12, 5))
    
    ax1.set_xlabel('Дата')
    ax1.set_ylabel('Выручка ($)', color='blue')
    ax1.plot(months, revenues, color='blue', marker='o', linewidth=2, label='Выручка')
    ax1.tick_params(axis='y', labelcolor='blue')
    
    ax2 = ax1.twinx()
    ax2.set_ylabel('Количество поездок', color='red')
    ax2.plot(months, rides, color='red', marker='s', linewidth=2, label='Поездки')
    ax2.tick_params(axis='y', labelcolor='red')
    
    plt.title('Динамика выручки и количества поездок по месяцам')
    plt.xticks(rotation=45, ha='right')
    fig.tight_layout()
    
    filename = os.path.join(DOCS_DIR, 'task3_chart.png')
    if not file_exists(filename, force):
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        print(f" График сохранён в {filename}")
    else:
        print(" Сохранение отменено")
    
    plt.close()

def task4_chart(driver_param=None, force=False):
    conn = get_connection()
    cur = conn.cursor()
    
    code = driver_code(driver_param)
    cur.execute("""
        SELECT к.описание, COALESCE(SUM(p.стоимость), 0) AS выручка
        FROM ОПЛАТА к
        LEFT JOIN ПОЕЗДКИ p ON p.оплата = к.код
         AND (%(driver)s::int IS NULL OR p.водитель = %(driver)s::int)
        GROUP BY к.описание
        ORDER BY выручка DESC
    """, {"driver": code})
    if code:
        filename = os.path.join(DOCS_DIR, f'task4_chart_{code}.png')
        title = f'Распределение выручки по способам оплаты (водитель №{code})'
    else:
        filename = os.path.join(DOCS_DIR, 'task4_chart.png')
        title = 'Распределение выручки по способам оплаты (все водители)'
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    if not rows:
        print("Нет данных для построения диаграммы")
        return
    
    labels = [row[0] for row in rows]
    sizes = [float(row[1]) for row in rows]
    
    filtered = [(label, s) for label, s in zip(labels, sizes) if s > 0]
    if not filtered:
        print("Нет положительной выручки для отображения")
        return
    
    labels, sizes = zip(*filtered)
    # доли меньше 3% (редкие способы оплаты) — одним сектором, иначе подписи налезают друг на друга
    total = sum(sizes)
    small = sum(s for s in sizes if s < total * 0.03)
    if small:
        labels, sizes = zip(*[(label, s) for label, s in zip(labels, sizes) if s >= total * 0.03])
        labels, sizes = list(labels) + ["Прочие"], list(sizes) + [small]
    
    plt.figure(figsize=(10, 8))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    plt.title(title)
    plt.axis('equal')
    
    if not file_exists(filename, force):
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        print(f" Диаграмма сохранена в {filename}")
    else:
        print(" Сохранение отменено")
    
    plt.close()

# ---------------------------------------------------------------------------
# Новые графики в стиле картинок README (docs/make_showcase.py), светлая тема.
# Заменяют по смыслу task3 (две оси Y) и task4 (круговая диаграмма); старые оставлены.
# ---------------------------------------------------------------------------

THEME = {"ink": "#0b0b0b", "ink2": "#52514e", "muted": "#8a8984", "grid": "#e4e3df",
         "accent": "#2a78d6", "surface": "#ffffff"}
MONTHS_SHORT = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]
MONTHS_GEN = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа",
              "сентября", "октября", "ноября", "декабря"]
MONTHS_PREP = ["январе", "феврале", "марте", "апреле", "мае", "июне", "июле", "августе",
               "сентябре", "октябре", "ноябре", "декабре"]


def ru_num(value, digits=0):
    """12345.6 -> '12 346', 0.4 с digits=1 -> '0,4' (пробел между разрядами, запятая в дроби)."""
    return f"{value:,.{digits}f}".replace(",", " ").replace(".", ",")


def money(value):
    """$6,7 млн, $366 тыс, $3,1 тыс, $924."""
    if value >= 1e6:
        return f"${ru_num(value / 1e6, 1)} млн"
    if value >= 1e4:
        return f"${ru_num(value / 1e3)} тыс"
    if value >= 1e3:
        return f"${ru_num(value / 1e3, 1)} тыс"
    return f"${ru_num(value)}"


def new_style():
    t = THEME
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 11,
        "text.color": t["ink"], "axes.labelcolor": t["ink2"],
        "xtick.color": t["ink2"], "ytick.color": t["ink2"],
        "axes.edgecolor": t["grid"], "axes.facecolor": t["surface"], "figure.facecolor": t["surface"],
        # без этого два знака $ в одной подписи читаются как формула
        "text.parse_math": False,
    })


def new_title(fig, text, sub):
    """Заголовок и подзаголовок; возвращает долю высоты, которую они заняли сверху."""
    h = fig.get_figheight()
    fig.text(0.02, 1 - 0.2 / h, text, fontsize=15, fontweight="bold", color=THEME["ink"], va="top")
    fig.text(0.02, 1 - 0.58 / h, sub, fontsize=10.5, color=THEME["ink2"], va="top")
    return 0.95 / h


def new_axes(ax, grid_axis="y"):
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(THEME["grid"])
    ax.tick_params(length=0)
    if grid_axis:
        ax.grid(axis=grid_axis, color=THEME["grid"], linewidth=0.8)
    ax.set_axisbelow(True)


def save_figure(fig, filename, force):
    if not file_exists(filename, force):
        fig.savefig(filename, dpi=144)
        print(f" График сохранён в {filename}")
    else:
        print(" Сохранение отменено")
    plt.close(fig)


def months_chart(force=False):
    """Выручка и цена километра по месяцам — две панели с общей осью месяцев вместо двух осей Y.

    Число поездок не показывается: сборщик берёт ровно 2000 поездок в день, и оно
    одинаково во всех месяцах. Выручка — в среднем за день, иначе короткий февраль
    выглядел бы провалом.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT DATE_TRUNC('month', дата)::date AS месяц,
               SUM(стоимость)::float / COUNT(DISTINCT дата::date) AS выручка_в_день,
               SUM(стоимость)::float / NULLIF(SUM(расстояние_км), 0)::float AS цена_км,
               COUNT(*)::float / COUNT(DISTINCT дата::date) AS поездок_в_день
        FROM ПОЕЗДКИ
        GROUP BY 1
        ORDER BY 1
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    if not rows:
        print("Нет данных для построения графика")
        return

    months = [r[0] for r in rows]
    revenue = [r[1] for r in rows]
    per_km = [r[2] or 0 for r in rows]
    per_day = round(sum(r[3] for r in rows) / len(rows))
    lo = min(range(len(rows)), key=per_km.__getitem__)
    growth = 100 * (per_km[-1] / per_km[lo] - 1) if per_km[lo] else 0
    # месяц самого большого скачка цены километра
    jump = max(range(1, len(rows)), key=lambda i: per_km[i] - per_km[i - 1]) if len(rows) > 1 else 0

    new_style()
    fig = plt.figure(figsize=(11, 6.4))
    top = 1 - new_title(
        fig, "Выручка и цена километра по месяцам",
        f"с {MONTHS_GEN[months[lo].month - 1]} {months[lo]:%Y} километр подорожал на {ru_num(growth)} % "
        f"(${ru_num(per_km[lo], 2)} → ${ru_num(per_km[-1], 2)}), больше всего — в {MONTHS_PREP[months[jump].month - 1]} "
        f"{months[jump]:%Y}; вслед за ним выросла и выручка")
    x = list(range(len(months)))
    labels = [f"{MONTHS_SHORT[m.month - 1]}\n{m:%Y}" if m.month == 1 or i == 0 else MONTHS_SHORT[m.month - 1]
              for i, m in enumerate(months)]
    height = (top - 0.22) / 2

    # панель 1: выручка в день — столбцы от нуля
    ax = fig.add_axes([0.08, 0.14 + height + 0.08, 0.90, height - 0.06])
    ax.bar(x, revenue, width=0.56, color=THEME["accent"], edgecolor=THEME["surface"], linewidth=2, zorder=3)
    new_axes(ax)
    ax.set_ylim(0, max(revenue) * 1.2)
    ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(3))
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: money(v) if v else "0"))
    ax.set_xlim(-0.6, len(months) - 0.4)
    ax.set_xticks(x, [""] * len(x))
    ax.text(0, 1.06, "выручка в среднем за день", transform=ax.transAxes, fontsize=11,
            fontweight="bold", color=THEME["ink"])
    for i in sorted({revenue.index(max(revenue)), revenue.index(min(revenue))}):
        ax.annotate(money(revenue[i]), (i, revenue[i]), xytext=(0, 4), textcoords="offset points",
                    ha="center", va="bottom", fontsize=9.5, color=THEME["ink"])

    # панель 2: цена километра — линия, ось не от нуля, чтобы был виден рост
    ax = fig.add_axes([0.08, 0.14, 0.90, height - 0.06])
    ax.plot(x, per_km, color=THEME["accent"], linewidth=2, zorder=3)
    ax.scatter(x, per_km, s=36, color=THEME["accent"], edgecolors=THEME["surface"], linewidths=2, zorder=4)
    new_axes(ax)
    span = max(per_km) - min(per_km) or 0.1
    ax.set_ylim(min(per_km) - 0.35 * span, max(per_km) + 0.45 * span)
    ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(3))
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"${ru_num(v, 2)}"))
    ax.set_xlim(-0.6, len(months) - 0.4)
    ax.set_xticks(x, labels)
    ax.text(0, 1.06, "выручка на километр пути", transform=ax.transAxes, fontsize=11,
            fontweight="bold", color=THEME["ink"])
    for i in sorted({lo, jump, len(per_km) - 1}):
        ax.annotate(f"${ru_num(per_km[i], 2)}", (i, per_km[i]), xytext=(0, 8), textcoords="offset points",
                    ha="center", va="bottom", fontsize=9.5, color=THEME["ink"])

    fig.text(0.02, 0.015, f"Выборка: {ru_num(per_day)} поездок в день, поэтому число поездок по месяцам не меняется.",
             fontsize=9, color=THEME["muted"])
    save_figure(fig, os.path.join(DOCS_DIR, "months_chart.png"), force)


def payments_chart(driver_param=None, force=False):
    """Доля выручки по способам оплаты — столбцы по убыванию вместо круговой диаграммы."""
    code = driver_code(driver_param)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT к.описание, SUM(p.стоимость)::float AS выручка
        FROM ПОЕЗДКИ p JOIN ОПЛАТА к ON к.код = p.оплата
        WHERE %(driver)s::int IS NULL OR p.водитель = %(driver)s::int
        GROUP BY к.описание
        HAVING SUM(p.стоимость) > 0
        ORDER BY выручка DESC
    """, {"driver": code})
    rows = cur.fetchall()
    cur.close()
    conn.close()
    if not rows:
        print("Нет поездок для построения графика")
        return

    total = sum(r[1] for r in rows)
    shares = [100 * r[1] / total for r in rows]
    who = f"водитель №{code}" if code else "все водители"
    new_style()
    fig = plt.figure(figsize=(9, 1.2 + 0.45 * len(rows)))
    top = 1 - new_title(fig, "Как платят за поездки",
                        f"доля выручки по способам оплаты, {who}: {rows[0][0].lower()} — {ru_num(shares[0])} %")
    ax = fig.add_axes([0.27, 0.03, 0.56, top - 0.06])
    y = list(range(len(rows)))
    ax.barh(y, shares, height=0.56, color=THEME["accent"], edgecolor=THEME["surface"], linewidth=2, zorder=3)
    ax.set_yticks(y, [r[0] for r in rows])
    ax.invert_yaxis()
    ax.tick_params(axis="y", labelsize=10.5, labelcolor=THEME["ink"])
    new_axes(ax, grid_axis=None)
    ax.spines["bottom"].set_visible(False)
    ax.set_xticks([])
    ax.set_xlim(0, max(shares))
    for i, (share, r) in enumerate(zip(shares, rows)):
        pct = "<0,1" if share < 0.1 else ru_num(share, 1) if share < 10 else ru_num(share)
        ax.annotate(f"{pct} %  ·  {money(r[1])}", (share, i), xytext=(6, 0), textcoords="offset points",
                    va="center", fontsize=10, color=THEME["ink"], annotation_clip=False)
    name = f"payments_chart_{code}.png" if code else "payments_chart.png"
    save_figure(fig, os.path.join(DOCS_DIR, name), force)


def save_all(force=False):
    print("Сохранение всех графиков и диаграмм...")
    task3_chart(force)
    task4_chart(force=force)
    task4_chart("1", force=force)
    months_chart(force)
    payments_chart(force=force)
    payments_chart("1", force=force)
    print(f"Все изображения сохранены в папку {DOCS_DIR}/")

def show_help():
    print("=" * 60)
    print("  PYTHON-ОТЧЁТЫ - TAXI")
    print("=" * 60)
    print()
    print("Использование:")
    print("  python taxi_report.py task1 [код_водителя] [способ_оплаты]")
    print("  python taxi_report.py task1s [код_водителя] [способ_оплаты]   - со звездочкой *")
    print("  python taxi_report.py task2 [способ_оплаты]")
    print("  python taxi_report.py task3 [--force]")
    print("  python taxi_report.py task4 [код_водителя] [--force]")
    print("  python taxi_report.py months [--force]                    - выручка и цена километра по месяцам")
    print("  python taxi_report.py payments [код_водителя] [--force]   - доли выручки по способам оплаты")
    print("  python taxi_report.py save-all [--force]")
    print()
    print("Примеры:")
    print("  python taxi_report.py task1")
    print("  python taxi_report.py task1s")
    print("  python taxi_report.py task1s 1")
    print("  python taxi_report.py task2")
    print("  python taxi_report.py task3 --force")
    print("  python taxi_report.py task4 1")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)
    
    command = sys.argv[1].lower()
    force = '--force' in sys.argv
    
    if command == "task1":
        driver_param = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] not in ['--force'] else None
        class_param = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] not in ['--force'] else None
        task1_report(driver_param, class_param, star_bottom=False)
    elif command == "task1s":
        driver_param = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] not in ['--force'] else None
        class_param = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] not in ['--force'] else None
        task1_report(driver_param, class_param, star_bottom=True)
    elif command == "task2":
        class_param = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] not in ['--force'] else None
        task2_pivot_table(class_param)
    elif command == "task3":
        task3_chart(force)
    elif command == "task4":
        driver_param = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] not in ['--force'] else None
        task4_chart(driver_param, force)
    elif command == "months":
        months_chart(force)
    elif command == "payments":
        driver_param = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] not in ['--force'] else None
        payments_chart(driver_param, force)
    elif command == "save-all":
        save_all(force)
    else:
        show_help()
        sys.exit(1)
