-- ./help.sh clients-rides — типы клиентов с числом поездок
SELECT
    К.код,
    К.тип,
    К.описание,
    COUNT(П.код_поездки) AS поездок
FROM КЛИЕНТЫ К
LEFT JOIN ПОЕЗДКИ П ON П.клиент = К.код
GROUP BY К.код
ORDER BY поездок DESC;
