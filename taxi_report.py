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

os.makedirs('docs', exist_ok=True)

def get_connection():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.Error as e:
        print(f"Ошибка подключения: {e}")
        sys.exit(1)

def file_exists(filename, force=False):
    if not force and os.path.exists(filename):
        response = input(f"Файл {filename} уже существует. Перезаписать? (y/N): ")
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
        к.описание AS тип_клиента,
        COALESCE(SUM(p.стоимость), 0) AS выручка,
        COUNT(p.код_поездки) AS количество_поездок
    FROM водители d
    CROSS JOIN КЛИЕНТЫ к
    LEFT JOIN ПОЕЗДКИ p ON p.водитель = d.код AND p.клиент = к.код
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
        print('  ОТЧЁТ: ВЫРУЧКА ПО ВОДИТЕЛЯМ И ТИПАМ КЛИЕНТОВ *')
    else:
        print('  ОТЧЁТ: ВЫРУЧКА ПО ВОДИТЕЛЯМ И ТИПАМ КЛИЕНТОВ')
    print('=' * 70)
    if driver_param:
        print(f'  Параметр: водитель = {driver_param}')
    if class_param:
        print(f'  Параметр: тип клиента = {class_param}')
    if not driver_param:
        print('  15 водителей с наибольшей выручкой, суммы в $')
    print('-' * 70)
    
    if not rows:
        print("  Данные не найдены")
        cur.close()
        conn.close()
        return
    
    col_widths = [4, 16, 22, 14, 8]
    headers = ['№', 'Водитель (x)', 'Тип клиента (y)', 'Выручка (F)', 'Поездок']
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
        print(f'  Параметр: тип клиента = {class_param}')
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
    
    filename = 'docs/task3_chart.png'
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
        FROM КЛИЕНТЫ к
        LEFT JOIN ПОЕЗДКИ p ON p.клиент = к.код
         AND (%(driver)s::int IS NULL OR p.водитель = %(driver)s::int)
        GROUP BY к.описание
        ORDER BY выручка DESC
    """, {"driver": code})
    if code:
        filename = f'docs/task4_chart_{code}.png'
        title = f'Распределение выручки по типам клиентов (водитель №{code})'
    else:
        filename = 'docs/task4_chart.png'
        title = 'Распределение выручки по типам клиентов (все водители)'
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    if not rows:
        print("Нет данных для построения диаграммы")
        return
    
    labels = [row[0] for row in rows]
    sizes = [float(row[1]) for row in rows]
    
    filtered = [(l, s) for l, s in zip(labels, sizes) if s > 0]
    if not filtered:
        print("Нет положительной выручки для отображения")
        return
    
    labels, sizes = zip(*filtered)
    
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

def save_all(force=False):
    print("Сохранение всех графиков и диаграмм...")
    task3_chart(force)
    task4_chart(force=force)
    task4_chart("1", force=force)
    print("Все изображения сохранены в папку docs/")

def show_help():
    print("=" * 60)
    print("  PYTHON-ОТЧЁТЫ - TAXI")
    print("=" * 60)
    print()
    print("Использование:")
    print("  python taxi_report.py task1 [код_водителя] [тип_клиента]")
    print("  python taxi_report.py task1s [код_водителя] [тип_клиента]   - со звездочкой *")
    print("  python taxi_report.py task2 [тип_клиента]")
    print("  python taxi_report.py task3 [--force]")
    print("  python taxi_report.py task4 [код_водителя] [--force]")
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
    elif command == "save-all":
        save_all(force)
    else:
        show_help()
