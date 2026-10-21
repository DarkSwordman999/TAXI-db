-- ./help.sh driver-load — загруженность водителей
SELECT
    'Водитель №' || В.код AS водитель,
    COUNT(П.код_поездки) AS поездок,
    ROUND(SUM(П.время_мин) / 60.0, 1) AS часов_в_пути
FROM ВОДИТЕЛИ В
JOIN ПОЕЗДКИ П ON В.код = П.водитель
GROUP BY В.код
ORDER BY поездок DESC
LIMIT 10;
