-- ./help.sh join-left — LEFT JOIN
SELECT
    Р.название AS район,
    COUNT(П.код_поездки) AS поездок
FROM РАЙОНЫ Р
LEFT JOIN ПОЕЗДКИ П ON Р.код = П.откуда
GROUP BY Р.код, Р.название
ORDER BY поездок ASC
LIMIT 10;
