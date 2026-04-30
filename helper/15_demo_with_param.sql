-- ЗАПРОС С ПАРАМЕТРОМ (arg1)
-- Использование: psql -d taxi_lab5 -v arg1='бизнес' -f helper/15_demo_with_param.sql

\echo '=== АВТОМОБИЛИ КЛАССА: ' :arg1 ' ==='
SELECT код, марка, модель, гос_номер, год_выпуска
FROM АВТОМОБИЛИ
WHERE класс LIKE CONCAT('%', :'arg1', '%')
ORDER BY код;
