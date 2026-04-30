-- Быстрый поиск автомобиля по марке
-- Использование: psql -d taxi_lab5 -v mark='Hyundai' -f helper/24_search_car.sql

SELECT код, марка, модель, гос_номер, класс
FROM АВТОМОБИЛИ
WHERE марка LIKE CONCAT('%', :'mark', '%')
ORDER BY марка, модель;
