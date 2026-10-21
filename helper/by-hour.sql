-- ./help.sh by-hour — поездки по часам
SELECT
    EXTRACT(HOUR FROM дата) AS час,
    COUNT(*) AS поездок,
    SUM(стоимость) AS выручка
FROM ПОЕЗДКИ
GROUP BY час
ORDER BY час;
