-- ./help.sh hour-share — распределение поездок по часам
SELECT
    EXTRACT(HOUR FROM дата) AS час,
    COUNT(*) AS поездок,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS процент
FROM ПОЕЗДКИ
GROUP BY час
ORDER BY час;
