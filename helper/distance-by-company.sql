-- ./help.sh distance-by-company — средний пробег по таксопаркам
SELECT
    Т.название AS таксопарк,
    ROUND(AVG(П.расстояние_км), 2) AS средний_пробег_км
FROM ПОЕЗДКИ П
JOIN ТАКСОПАРКИ Т ON П.таксопарк = Т.код
GROUP BY Т.название
ORDER BY средний_пробег_км DESC;
