-- ./help.sh revenue-by-client — выручка по типам клиентов
SELECT
    О.описание AS способ_оплаты,
    COUNT(*) AS поездок,
    SUM(П.стоимость) AS выручка
FROM ОПЛАТА О
JOIN ПОЕЗДКИ П ON О.код = П.оплата
GROUP BY О.код, О.описание
ORDER BY выручка DESC;
