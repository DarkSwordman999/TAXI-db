-- Быстрый поиск района по названию
-- Использование: psql -d taxi -v arg1='Park' -f helper/24_search_area.sql
-- или: ./help.sh helper/24_search_area.sql Park

SELECT код, название, широта, долгота
FROM РАЙОНЫ
WHERE название ILIKE CONCAT('%', :'arg1', '%')
ORDER BY название;
