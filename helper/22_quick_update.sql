-- Быстрое обновление госномера автомобиля
-- Использование: psql -d taxi_lab5 -v car_id=1 -v new_number='A999AA' -f helper/22_quick_update.sql

\echo '=== ДО UPDATE ==='
SELECT код, гос_номер, марка, модель FROM АВТОМОБИЛИ WHERE код = :car_id;

UPDATE АВТОМОБИЛИ SET гос_номер = :'new_number' WHERE код = :car_id;

\echo '=== ПОСЛЕ UPDATE ==='
SELECT код, гос_номер, марка, модель FROM АВТОМОБИЛИ WHERE код = :car_id;
