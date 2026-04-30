\echo '=== ТОП-3 ВОДИТЕЛЯ ПО ВЫРУЧКЕ В КАЖДОМ КЛАССЕ ==='

SELECT 
    класс,
    водитель,
    выручка,
    место
FROM (
    SELECT DISTINCT А.класс 
    FROM АВТОМОБИЛИ А
    WHERE А.класс IS NOT NULL
) AS классы,
LATERAL (
    SELECT 
        В.фамилия || ' ' || В.имя AS водитель,
        SUM(П.стоимость) AS выручка,
        ROW_NUMBER() OVER (ORDER BY SUM(П.стоимость) DESC) AS место
    FROM ВОДИТЕЛИ В
    JOIN ПОЕЗДКИ П ON П.водитель = В.код
    JOIN АВТОМОБИЛИ А ON А.код = П.автомобиль
    WHERE А.класс = классы.класс
    GROUP BY В.фамилия, В.имя
    ORDER BY выручка DESC
    LIMIT 3
) AS top
ORDER BY класс, место;
