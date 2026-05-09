#!/usr/bin/env python3
import requests
import csv
import os
import psycopg2
from datetime import datetime
import uuid

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5432'),
    'dbname': os.environ.get('DB_NAME', 'taxi_lab5'),
    'user': os.environ.get('DB_USER', 'uliavladimirovna'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'sslmode': os.environ.get('DB_SSLMODE', 'require')
}

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

OSRM_URL = "http://router.project-osrm.org/route/v1/driving/"

def parse_osrm_route(start_lat, start_lon, end_lat, end_lon):
    coordinates = f"{start_lon},{start_lat};{end_lon},{end_lat}"
    url = f"{OSRM_URL}{coordinates}?overview=false"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 'Ok' and data.get('routes'):
                route = data['routes'][0]
                distance_km = round(route.get('distance', 0) / 1000, 1)
                duration_min = int(route.get('duration', 0) / 60)
                return distance_km, duration_min
        return None, None
    except:
        return None, None

def main():
    print("OSRM REAL ROUTE PARSER (APPEND MODE)")
    os.makedirs('data', exist_ok=True)
    csv_file = 'data/rides.csv'
    file_exists = os.path.isfile(csv_file) and os.path.getsize(csv_file) > 0
    
    with open(csv_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['run_id', 'timestamp', 'from_loc', 'to_loc', 'distance_km', 'duration_min', 'price_rub'])
        
        run_id = str(uuid.uuid4())[:8]
        saved = 0
        timestamp = datetime.now()
        
        for i, (from_name, from_lat, from_lon) in enumerate(LOCATIONS):
            for j, (to_name, to_lat, to_lon) in enumerate(LOCATIONS):
                if i == j:
                    continue
                distance, duration = parse_osrm_route(from_lat, from_lon, to_lat, to_lon)
                if distance:
                    price = int(99 + distance * 25)
                    saved += 1
                    writer.writerow([run_id, timestamp.isoformat(), from_name, to_name, distance, duration, price])
                    
                    try:
                        conn = psycopg2.connect(**DB_CONFIG)
                        cur = conn.cursor()
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS ПОЕЗДКИ (
                                код_поездки SERIAL PRIMARY KEY,
                                дата TIMESTAMP,
                                стоимость NUMERIC,
                                водитель INTEGER,
                                автомобиль INTEGER,
                                клиент INTEGER,
                                расстояние_км NUMERIC,
                                время_мин INTEGER
                            )
                        """)
                        cur.execute("""
                            INSERT INTO ПОЕЗДКИ (дата, стоимость, водитель, автомобиль, клиент, расстояние_км, время_мин)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (timestamp, price, saved % 32 + 1, saved % 30 + 1, saved % 250 + 1, distance, duration))
                        conn.commit()
                        cur.close()
                        conn.close()
                        print(f"[{saved}] {from_name} → {to_name}: {distance} км, {price} руб")
                    except Exception as e:
                        print(f"DB error: {e}")
    
    print(f"\n CSV дописан: {csv_file} (+{saved} записей, run_id={run_id})")
    print(f" PostgreSQL добавлено: {saved} записей")

if __name__ == "__main__":
    main()
