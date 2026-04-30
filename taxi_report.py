#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
import sys
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

def print_footer(col_widths):
    print('└' + '┴'.join('─' * (w + 2) for w in col_widths) + '┘')

def task1_report(driver_param=None, class_param=None):
    """Отчёт о выручке по водителям и классам"""
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
        print(f'  Водитель: {driver_param}')
    if class_param:
        print(f'  Класс: {class_param}')
    print('-' * 70)
    
    if not rows:
        print("  Данные не найдены")
        cur.close()
        conn.close()
        return
    
    col_widths = [4, 20, 12, 10, 8]
    headers = ['№', 'Водитель', 'Класс', 'Выручка', 'Поездок']
    
    print_header(col_widths, headers)
    
    current_driver = None
    driver_total = 0
    driver_count = 0
    grand_total = 0
    grand_count = 0
    row_num = 1
    first_in_group = True
    
    for driver, class_name, revenue, rides in rows:
        if current_driver != driver:
            if current_driver is not None:
                print_row(['', current_driver[:18], 'ИТОГО:', f'{driver_total:.2f}', str(driver_count)], col_widths)
                print('├' + '┼'.join('─' * (w + 2) for w in col_widths) + '┤')
                row_num = 1
            
            current_driver = driver
            driver_total = 0
            driver_count = 0
            first_in_group = True
        
        driver_display = driver if first_in_group else ''
        print_row([row_num if first_in_group else '', driver_display[:18], class_name, f'{revenue:.2f}', str(int(rides))], col_widths)
        
        driver_total += revenue
        driver_count += rides
        grand_total += revenue
        grand_count += rides
        row_num += 1
        first_in_group = False
    
    if current_driver is not None:
        print_row(['', current_driver[:18], 'ИТОГО:', f'{driver_total:.2f}', str(driver_count)], col_widths)
        print('├' + '┼'.join('─' * (w + 2) for w in col_widths) + '┤')
    
    if grand_count > 0:
        print_row(['', 'ВСЕГО', '', f'{grand_total:.2f}', str(grand_count)], col_widths)
    print_footer(col_widths)
    
    cur.close()
    conn.close()

def task2_pivot_table(class_param=None):
    """Сводная таблица (водители × классы)"""
    conn = get_connection()
    cur = conn.cursor()
    
    sql = """
    SELECT 
        водитель,
        класс,
        выручка
    FROM v_report_data
    WHERE (LOWER(класс) LIKE LOWER(%s) OR %s IS NULL)
    ORDER BY водитель, класс
    """
    class_pattern = f"%{class_param}%" if class_param else None
    cur.execute(sql, (class_pattern, class_pattern))
    rows = cur.fetchall()
    
    data = {}
    drivers_set = set()
    classes_set = set()
    
    for driver, class_name, revenue in rows:
        if driver not in data:
            data[driver] = {}
        data[driver][class_name] = revenue
        drivers_set.add(driver)
        classes_set.add(class_name)
    
    drivers = sorted(drivers_set)[:15]
    classes = sorted(classes_set)
    
    print()
    print('=' * 70)
    print('  СВОДНАЯ ТАБЛИЦА: ВЫРУЧКА ВОДИТЕЛЕЙ ПО КЛАССАМ')
    print('=' * 70)
    if class_param:
        print(f'  Фильтр по классу: {class_param}')
    print('-' * 70)
    
    col_widths = [4, 20] + [10] * len(classes) + [10]
    headers = ['№', 'Водитель'] + classes + ['Итого']
    
    print_header(col_widths, headers)
    
    for i, driver in enumerate(drivers, 1):
        row = [i, driver[:18]]
        driver_total = 0
        for class_name in classes:
            val = data.get(driver, {}).get(class_name, 0)
            row.append(f'{val:.2f}' if val > 0 else '─')
            driver_total += val
        row.append(f'{driver_total:.2f}')
        print_row(row, col_widths)
    
    print_footer(col_widths)
    
    cur.close()
    conn.close()

def show_help():
    print("=" * 60)
    print("  ОТЧЁТЫ ПО БАЗЕ ДАННЫХ TAXI")
    print("=" * 60)
    print()
    print("Использование:")
    print("  python taxi_report.py task1 [водитель] [класс]")
    print("  python taxi_report.py task2 [класс]")
    print()
    print("Примеры:")
    print("  python taxi_report.py task1")
    print("  python taxi_report.py task1 Волков")
    print("  python taxi_report.py task2")
    print("  python taxi_report.py task2 бизнес")

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
    else:
        show_help()
