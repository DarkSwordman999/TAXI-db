-- ./help.sh join-full — FULL JOIN
SELECT
    Т.название AS таксопарк,
    К.описание AS тип_клиента
FROM ТАКСОПАРКИ Т
FULL JOIN КЛИЕНТЫ К ON Т.код = К.код
LIMIT 10;
