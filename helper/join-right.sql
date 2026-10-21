-- ./help.sh join-right — RIGHT JOIN
SELECT
    О.описание AS способ_оплаты,
    COUNT(П.код_поездки) AS поездок
FROM ПОЕЗДКИ П
RIGHT JOIN ОПЛАТА О ON П.оплата = О.код
GROUP BY О.код, О.описание
ORDER BY поездок DESC
LIMIT 10;
