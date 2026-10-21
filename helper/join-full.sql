-- ./help.sh join-full — FULL JOIN
SELECT
    Т.название AS таксопарк,
    О.описание AS способ_оплаты
FROM ТАКСОПАРКИ Т
FULL JOIN ОПЛАТА О ON Т.код = О.код
LIMIT 10;
