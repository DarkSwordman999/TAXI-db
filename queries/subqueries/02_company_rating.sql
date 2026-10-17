\echo '=== РЕЙТИНГ ТАКСОПАРКОВ ПО ВЫРУЧКЕ ==='

SELECT 
    Т.название AS таксопарк,
    (SELECT SUM(стоимость) FROM ПОЕЗДКИ WHERE таксопарк = Т.код) AS выручка,
    ROUND((SELECT SUM(стоимость) FROM ПОЕЗДКИ) /
          (SELECT COUNT(*) FROM ТАКСОПАРКИ), 2) AS средняя_по_таксопаркам,
    ROUND((SELECT SUM(стоимость) FROM ПОЕЗДКИ WHERE таксопарк = Т.код) -
          (SELECT SUM(стоимость) FROM ПОЕЗДКИ) / (SELECT COUNT(*) FROM ТАКСОПАРКИ), 2) AS отклонение
FROM ТАКСОПАРКИ Т
WHERE (SELECT COUNT(*) FROM ПОЕЗДКИ WHERE таксопарк = Т.код) > 0
ORDER BY выручка DESC
LIMIT 10;
