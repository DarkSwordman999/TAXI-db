INSERT INTO ПОЕЗДКИ (дата, автомобиль, водитель, клиент, расстояние_км, время_мин, стоимость)
SELECT 
    random_date('2024-01-01', '2024-12-31') + (random() * INTERVAL '23 hours'),
    (random() * 29 + 1)::INT,
    (random() * 29 + 1)::INT,
    (random() * 49 + 1)::INT,
    (random() * 50 + 1)::INT,
    (random() * 60 + 5)::INT,
    (random() * 40 + 100)::INT
FROM generate_series(1, 1000);
