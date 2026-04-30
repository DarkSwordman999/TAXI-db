#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
import sys
import matplotlib.pyplot as plt
from collections import defaultdict

DB_CONFIG = {
    'dbname': 'taxi_lab5',
    'user': 'uliavladimirovna',
    'password': '',
    'host': 'localhost'
}

def get_connection():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.Error as e:
        print(f"Ошибка подключения: {e}")
        sys.exit(1)

def print_header(col_widths, headers):
    print('┌' + '┬'.join('─' * (w + 2) for w in col_widths) + '┐')
    row = '│'
    for i, h in enumerate(headers):
        row += f' {h:<{col_widths[i]}} │'
    print(row)
    print('├' + '┼'.join('─' * (w + 2) for w in col_widths) + '┤')

def print_row(cells, col_widths):
    row = '│'
    for i, cell in enumerate(cells):
        row += f' {str(cell):<{col_widths[i]}} │'
    print(row)

def print_separator(col_widths):
    print('├' + '┼'.join('─' * (w + 2) for w in col_widths) + '┤')

def print_footer(col_widths):
    print('└' + '┴'.join('─' * (w + 2) for w in col_widths) + '┘')

def task1_report(driver_param=None, class_param=None):
    """Задача 1: Отчёт о выручке по водителям (x) и классам (y)"""
    conn = get_connection()
    cur = conn.cursor()
    
    sql = """
    SELECT 
        водитель,
        класс,
        выручка,
        количество_поездок
    FROM v_report_data
    WHERE (LOWER(водитель) LIKE LOWER(%s) OR %s IS NULL)
      AND (LOWER(класс) LIKE LOWER(%s) OR %s IS NULL)
    ORDER BY водитель, класс
    """
    
    driver_pattern = f"%{driver_param}%" if driver_param else None
    class_pattern = f"%{class_param}%" if class_param else None
    
    cur.execute(sql, (driver_pattern, driver_pattern, class_pattern, class_pattern))
    rows = cur.fetchall()
    
    print()
    print('=' * 70)
    print('  ОТЧЁТ: ВЫРУЧКА ПО ВОДИТЕЛЯМ И КЛАССАМ АВТО')
    print('=' * 70)
    if driver_param:
        print(f'  Параметр: водитель = {driver_param}')
    if class_param:
        print(f'  Параметр: класс = {class_param}')
    print('-' * 70)
    
    if not rows:
        print("  Данные не найдены")
        cur.close()
        conn.close()
        return
    
    col_widths = [4, 22, 12, 12, 10]
    headers = ['№', 'Водитель (x)', 'Класс (y)', 'Выручка (F)', 'Поездок']
    
    print_header(col_widths, headers)
    
    current_driver = None
    driver_total = 0
    driver_count = 0
    grand_total = 0
    grand_count = 0
    row_num = 1
    first_in_group = True
    group_total_shown = False
    
    for driver, class_name, revenue, rides in rows:
        if current_driver != driver:
            # Вывод итога по группе (в первой строке с новым x)
            if current_driver is not None and not group_total_shown:
                print_row(['', current_driver[:20], 'ИТОГО по группе:', f'{driver_total:.2f}', str(driver_count)], col_widths)
                print_separator(col_widths)
                group_total_shown = True
            
            if current_driver is not None:
                row_num = 1
            
            current_driver = driver
            driver_total = 0
            driver_count = 0
            first_in_group = True
            group_total_shown = False
        
        driver_display = driver if first_in_group else ''
        print_row([row_num if first_in_group else '', driver_display[:20], class_name, f'{revenue:.2f}', str(int(rides))], col_widths)
        
        driver_total += revenue
        driver_count += rides
        grand_total += revenue
        grand_count += rides
        row_num += 1
        first_in_group = False
    
    # Итог последней группы
    if current_driver is not None and not group_total_shown:
        print_row(['', current_driver[:20], 'ИТОГО по группе:', f'{driver_total:.2f}', str(driver_count)], col_widths)
        print_separator(col_widths)
    
    # Общий итог
    print_row(['', 'ВСЕГО', '', f'{grand_total:.2f}', str(grand_count)], col_widths)
    print_footer(col_widths)
    
    cur.close()
    conn.close()

def task2_pivot_table(class_param=None):
    """Задача 2: Сводная таблица (водители × классы) с матрицами T и nT"""
    conn = get_connection()
    cur = conn.cursor()
    
    sql = """
    SELECT 
        водитель,
        класс,
        выручка,
        количество_поездок
    FROM v_report_data
    WHERE (LOWER(класс) LIKE LOWER(%s) OR %s IS NULL)
    ORDER BY водитель, класс
    """
    class_pattern = f"%{class_param}%" if class_param else None
    cur.execute(sql, (class_pattern, class_pattern))
    rows = cur.fetchall()
    
    # Формирование матриц T (выручка) и nT (количество)
    data_T = {}
    data_nT = {}
    drivers_set = set()
    classes_set = set()
    
    for driver, class_name, revenue, rides in rows:
        if driver not in data_T:
            data_T[driver] = {}
            data_nT[driver] = {}
        data_T[driver][class_name] = revenue
        data_nT[driver][class_name] = rides
        drivers_set.add(driver)
        classes_set.add(class_name)
    
    drivers = sorted(drivers_set)[:15]
    classes = sorted(classes_set)
    
    print()
    print('=' * 70)
    print('  СВОДНАЯ ТАБЛИЦА: ВЫРУЧКА (T) И КОЛИЧЕСТВО ПОЕЗДОК (nT)')
    print('=' * 70)
    if class_param:
        print(f'  Параметр: класс = {class_param}')
    print('-' * 70)
    
    # Ширины колонок
    col_widths = [4, 22] + [10] * len(classes) + [10]
    headers = ['№', 'Водитель (x)'] + [c for c in classes] + ['Итого']
    
    print_header(col_widths, headers)
    
    # Вывод матрицы T (выручка)
    print()
    print("  [МАТРИЦА T: ВЫРУЧКА]")
    print_header(col_widths, headers)
    
    class_totals = defaultdict(float)
    
    for i, driver in enumerate(drivers, 1):
        row = [i, driver[:20]]
        driver_total = 0
        for j, class_name in enumerate(classes):
            val = data_T.get(driver, {}).get(class_name, 0)
            row.append(f'{val:.2f}')
            driver_total += val
            class_totals[class_name] += val
        row.append(f'{driver_total:.2f}')
        print_row(row, col_widths)
    
    # Итого по столбцам
    print_separator(col_widths)
    total_row = ['', 'ИТОГО по столбцам']
    for class_name in classes:
        total_row.append(f'{class_totals[class_name]:.2f}')
    total_row.append(f'{sum(class_totals.values()):.2f}')
    print_row(total_row, col_widths)
    print_footer(col_widths)
    
    # Вывод матрицы nT (количество поездок)
    print()
    print("  [МАТРИЦА nT: КОЛИЧЕСТВО ПОЕЗДОК]")
    print_header(col_widths, headers)
    
    class_totals_nT = defaultdict(float)
    
    for i, driver in enumerate(drivers, 1):
        row = [i, driver[:20]]
        driver_total = 0
        for class_name in classes:
            val = data_nT.get(driver, {}).get(class_name, 0)
            row.append(f'{int(val)}')
            driver_total += val
            class_totals_nT[class_name] += val
        row.append(f'{int(driver_total)}')
        print_row(row, col_widths)
    
    print_separator(col_widths)
    total_row_nT = ['', 'ИТОГО по столбцам']
    for class_name in classes:
        total_row_nT.append(f'{int(class_totals_nT[class_name])}')
    total_row_nT.append(f'{int(sum(class_totals_nT.values()))}')
    print_row(total_row_nT, col_widths)
    print_footer(col_widths)
    
    cur.close()
    conn.close()

def task3_chart():
    """Задача 3: График динамики выручки и количества поездок по месяцам"""
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
    revenues = [row[1] for row in rows]
    rides = [row[2] for row in rows]
    
    fig, ax1 = plt.subplots(figsize=(12, 5))
    
    ax1.set_xlabel('Дата')
    ax1.set_ylabel('Выручка (руб.)', color='blue')
    ax1.plot(months, revenues, color='blue', marker='o', linewidth=2, label='Выручка')
    ax1.tick_params(axis='y', labelcolor='blue')
    
    ax2 = ax1.twinx()
    ax2.set_ylabel('Количество поездок', color='red')
    ax2.plot(months, rides, color='red', marker='s', linewidth=2, label='Поездки')
    ax2.tick_params(axis='y', labelcolor='red')
    
    plt.title('Динамика выручки и количества поездок по месяцам')
    plt.xticks(rotation=45, ha='right')
    fig.tight_layout()
    plt.show()

def task4_chart(driver_param=None):
    """Задача 4: Круговая диаграмма распределения выручки по классам для водителя"""
    conn = get_connection()
    cur = conn.cursor()
    
    if driver_param:
        sql = """
        SELECT 
            А.класс,
            COALESCE(SUM(П.стоимость), 0) as выручка
        FROM ВОДИТЕЛИ В
        CROSS JOIN АВТОМОБИЛИ А
        LEFT JOIN ПОЕЗДКИ П ON П.водитель = В.код AND П.автомобиль = А.код
        WHERE В.фамилия || ' ' || В.имя LIKE %s
        GROUP BY А.класс
        ORDER BY выручка DESC
        """
        cur.execute(sql, (f"%{driver_param}%",))
        title = f'Распределение выручки по классам (водитель: {driver_param})'
    else:
        sql = """
        SELECT 
            А.класс,
            COALESCE(SUM(П.стоимость), 0) as выручка
        FROM АВТОМОБИЛИ А
        LEFT JOIN ПОЕЗДКИ П ON П.автомобиль = А.код
        GROUP BY А.класс
        ORDER BY выручка DESC
        """
        cur.execute(sql)
        title = 'Распределение выручки по классам (все водители)'
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    if not rows:
        print("Нет данных для построения диаграммы")
        return
    
    labels = [row[0] for row in rows]
    sizes = [row[1] for row in rows]
    
    # Фильтруем нулевые значения
    filtered = [(l, s) for l, s in zip(labels, sizes) if s > 0]
    if not filtered:
        print("Нет положительной выручки для отображения")
        return
    
    labels, sizes = zip(*filtered)
    
    plt.figure(figsize=(10, 8))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    plt.title(title)
    plt.axis('equal')
    plt.show()

def show_help():
    print("=" * 60)
    print("  ЛАБОРАТОРНАЯ РАБОТА №8 - TAXI")
    print("=" * 60)
    print()
    print("Использование:")
    print("  python taxi_report.py task1 [водитель] [класс]")
    print("  python taxi_report.py task2 [класс]")
    print("  python taxi_report.py task3")
    print("  python taxi_report.py task4 [водитель]")
    print()
    print("Примеры:")
    print("  python taxi_report.py task1")
    print("  python taxi_report.py task1 Волков")
    print("  python taxi_report.py task2")
    print("  python taxi_report.py task2 бизнес")
    print("  python taxi_report.py task3")
    print("  python taxi_report.py task4 Волков")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    if command == "task1":
        driver_param = sys.argv[2] if len(sys.argv) > 2 else None
        class_param = sys.argv[3] if len(sys.argv) > 3 else None
        task1_report(driver_param, class_param)
    elif command == "task2":
        class_param = sys.argv[2] if len(sys.argv) > 2 else None
        task2_pivot_table(class_param)
    elif command == "task3":
        task3_chart()
    elif command == "task4":
        driver_param = sys.argv[2] if len(sys.argv) > 2 else None
        task4_chart(driver_param)
    else:
        show_help()
