-- ЗАПРОС С ПАРАМЕТРОМ (arg1): таксопарки по части названия
-- Использование: psql -d taxi -v arg1='Cab' -f helper/15_demo_with_param.sql

\echo '=== ТАКСОПАРКИ, В НАЗВАНИИ КОТОРЫХ ЕСТЬ: ' :arg1 ' ==='
SELECT Т.код, Т.название, COUNT(П.код_поездки) AS поездок
FROM ТАКСОПАРКИ Т
LEFT JOIN ПОЕЗДКИ П ON П.таксопарк = Т.код
WHERE Т.название ILIKE CONCAT('%', :'arg1', '%')
GROUP BY Т.код, Т.название
ORDER BY поездок DESC;
