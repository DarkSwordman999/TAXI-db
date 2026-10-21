-- ./help.sh by-month — выручка по месяцам
SELECT
    TO_CHAR(DATE_TRUNC('month', дата), 'YYYY-MM') AS месяц,
    COUNT(*) AS поездок,
    SUM(стоимость) AS выручка
FROM ПОЕЗДКИ
GROUP BY 1
ORDER BY 1;
