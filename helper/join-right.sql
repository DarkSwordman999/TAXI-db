-- ./help.sh join-right — RIGHT JOIN
SELECT
    К.описание AS тип_клиента,
    COUNT(П.код_поездки) AS поездок
FROM ПОЕЗДКИ П
RIGHT JOIN КЛИЕНТЫ К ON П.клиент = К.код
GROUP BY К.код, К.описание
ORDER BY поездок DESC
LIMIT 10;
