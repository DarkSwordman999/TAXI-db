-- ./help.sh by-weekday — выручка по дням недели
SELECT
    EXTRACT(ISODOW FROM дата) AS день,
    COUNT(*) AS поездок,
    SUM(стоимость) AS выручка
FROM ПОЕЗДКИ
GROUP BY день
ORDER BY день;
