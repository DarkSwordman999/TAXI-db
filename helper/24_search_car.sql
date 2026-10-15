-- Быстрый поиск района по названию
-- Использование: psql -d taxi -v mark='Park' -f helper/24_search_car.sql

SELECT код, название, широта, долгота
FROM РАЙОНЫ
WHERE название ILIKE CONCAT('%', :'mark', '%')
ORDER BY название;
