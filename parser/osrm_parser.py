#!/usr/bin/env python3
import csv
import os
import requests
import psycopg2
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2

# Получаем параметры из секретов GitHub
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5432'),
    'dbname': os.environ.get('DB_NAME', 'taxi_lab5'),
    'user': os.environ.get('DB_USER', 'uliavladimirovna'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'sslmode': os.environ.get('DB_SSLMODE', 'require')
}

# Точки маршрутов
LOCATIONS = [
    ("Красная площадь", 55.7539, 37.6208),
    ("Лужники", 55.7155, 37.5531),
    ("ВДНХ", 55.8265, 37.6415),
    ("Киевский вокзал", 55.7435, 37.5677),
    ("МГУ", 55.7020, 37.5400),
    ("Москва-Сити", 55.7482, 37.5377),
    ("Третьяковка", 55.7415, 37.6208),
    ("Парк Горького", 55.7311, 37.6084)
]

def calc_distance(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def save_to_postgresql(data):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Создаем таблицу если не существует
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ПОЕЗДКИ (
                код_поездки SERIAL PRIMARY KEY,
                дата TIMESTAMP,
                стоимость NUMERIC(10,2),
                водитель INTEGER,
                автомобиль INTEGER,
                клиент INTEGER,
                расстояние_км NUMERIC(8,1),
                время_мин INTEGER
            )
        """)
        
        cur.execute("""
            INSERT INTO ПОЕЗДКИ (дата, стоимость, водитель, автомобиль, клиент, расстояние_км, время_мин)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            data['timestamp'],
            data['price'],
            data['driver'],
            data['car'],
            data['client'],
            data['distance'],
            data['duration']
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"DB error: {e}")
        return False

def main():
    print("="*50)
    print("OSRM TAXI PARSER")
    print(f"DB: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}")
    print("="*50)
    
    # Создаем папку для CSV
    os.makedirs('data', exist_ok=True)
    data_file = 'data/rides.csv'
    file_exists = os.path.isfile(data_file)
    
    saved_db = 0
    saved_csv = 0
    
    with open(data_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'from_loc', 'to_loc', 'distance_km', 'duration_min', 'price_rub'])
        
        for i, (name1, lat1, lon1) in enumerate(LOCATIONS):
            for j, (name2, lat2, lon2) in enumerate(LOCATIONS):
                if i == j:
                    continue
                
                distance = calc_distance(lat1, lon1, lat2, lon2)
                duration = int(distance * 2.5)
                price = int(99 + distance * 25)
                timestamp = datetime.now()
                
                # CSV запись
                writer.writerow([
                    timestamp.isoformat(),
                    name1,
                    name2,
                    round(distance, 1),
                    duration,
                    price
                ])
                saved_csv += 1
                
                # PostgreSQL запись
                pg_data = {
                    'timestamp': timestamp,
                    'price': price,
                    'driver': (saved_db % 32) + 1,
                    'car': (saved_db % 30) + 1,
                    'client': (saved_db % 250) + 1,
                    'distance': round(distance, 1),
                    'duration': duration
                }
                
                if save_to_postgresql(pg_data):
                    saved_db += 1
                    print(f"[{saved_db}] {name1[:12]} → {name2[:12]}: {distance:.1f} km, {price} руб")
    
    print(f"\nCSV saved: {saved_csv}")
    print(f"PostgreSQL saved: {saved_db}")

if __name__ == "__main__":
    main()
