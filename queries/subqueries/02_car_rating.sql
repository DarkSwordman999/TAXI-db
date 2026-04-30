\echo '=== РЕЙТИНГ АВТОМОБИЛЕЙ ПО ВЫРУЧКЕ ==='

SELECT 
    А.марка || ' ' || А.модель AS автомобиль,
    (SELECT SUM(стоимость) FROM ПОЕЗДКИ WHERE автомобиль = А.код) AS выручка,
    (SELECT AVG(стоимость) FROM ПОЕЗДКИ) AS средняя_выручка,
    ROUND((SELECT SUM(стоимость) FROM ПОЕЗДКИ WHERE автомобиль = А.код) - 
          (SELECT AVG(стоимость) FROM ПОЕЗДКИ), 2) AS отклонение
FROM АВТОМОБИЛИ А
WHERE (SELECT COUNT(*) FROM ПОЕЗДКИ WHERE автомобиль = А.код) > 0
ORDER BY выручка DESC
LIMIT 10;
