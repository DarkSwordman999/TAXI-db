-- Поездки по часам дня
SELECT 
    EXTRACT(HOUR FROM ПОЕЗДКИ.дата) AS час,
    COUNT(*) AS количество_поездок,
    SUM(стоимость) AS выручка
FROM ПОЕЗДКИ
GROUP BY час
ORDER BY час;
