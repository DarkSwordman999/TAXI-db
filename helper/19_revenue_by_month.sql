-- Выручка по месяцам
SELECT 
    EXTRACT(MONTH FROM ПОЕЗДКИ.дата) AS месяц,
    SUM(ПОЕЗДКИ.стоимость) AS выручка
FROM ПОЕЗДКИ
GROUP BY месяц
ORDER BY месяц;
