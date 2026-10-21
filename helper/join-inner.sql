-- ./help.sh join-inner — INNER JOIN
SELECT
    П.код_поездки,
    Т.название AS таксопарк,
    'Водитель №' || В.код AS водитель,
    П.стоимость
FROM ПОЕЗДКИ П
INNER JOIN ТАКСОПАРКИ Т ON П.таксопарк = Т.код
INNER JOIN ВОДИТЕЛИ В ON П.водитель = В.код
LIMIT 10;
