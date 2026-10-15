\echo '=== ТОП-3 ВОДИТЕЛЯ ПО ВЫРУЧКЕ В КАЖДОМ ТАКСОПАРКЕ ==='

SELECT 
    Т.название AS таксопарк,
    top.водитель,
    top.выручка,
    top.место
FROM ТАКСОПАРКИ Т,
LATERAL (
    SELECT 
        'Водитель №' || П.водитель AS водитель,
        SUM(П.стоимость) AS выручка,
        ROW_NUMBER() OVER (ORDER BY SUM(П.стоимость) DESC) AS место
    FROM ПОЕЗДКИ П
    WHERE П.таксопарк = Т.код
    GROUP BY П.водитель
    ORDER BY выручка DESC
    LIMIT 3
) AS top
ORDER BY Т.название, top.место;
