-- ./help.sh revenue-by-client — выручка по типам клиентов
SELECT
    К.описание AS тип_клиента,
    COUNT(*) AS поездок,
    SUM(П.стоимость) AS выручка
FROM КЛИЕНТЫ К
JOIN ПОЕЗДКИ П ON К.код = П.клиент
GROUP BY К.код, К.описание
ORDER BY выручка DESC;
