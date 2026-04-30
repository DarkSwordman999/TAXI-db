-- DELETE FROM TAB2 USING TAB3 WHERE выражение
-- Удаление поездок с расстоянием менее 2 км

\echo '=== КОЛИЧЕСТВО ДО DELETE ==='
SELECT COUNT(*) FROM ПОЕЗДКИ WHERE расстояние_км < 2;

DELETE FROM ПОЕЗДКИ USING АВТОМОБИЛИ 
WHERE ПОЕЗДКИ.автомобиль = АВТОМОБИЛИ.код 
  AND ПОЕЗДКИ.расстояние_км < 2;

\echo '=== КОЛИЧЕСТВО ПОСЛЕ DELETE ==='
SELECT COUNT(*) FROM ПОЕЗДКИ WHERE расстояние_км < 2;
