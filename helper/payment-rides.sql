-- ./help.sh payment-rides (прежнее имя clients-rides) — способы оплаты с числом поездок
SELECT
    О.код,
    О.тип,
    О.описание,
    COUNT(П.код_поездки) AS поездок
FROM ОПЛАТА О
LEFT JOIN ПОЕЗДКИ П ON П.оплата = О.код
GROUP BY О.код
ORDER BY поездок DESC;
