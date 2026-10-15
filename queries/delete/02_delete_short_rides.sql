-- DELETE FROM TAB2 USING TAB3 WHERE выражение
-- Удаление поездок короче 2 км у таксопарка Flash Cab

BEGIN;

\echo '=== КОЛИЧЕСТВО ДО DELETE ==='
SELECT COUNT(*) FROM ПОЕЗДКИ П JOIN ТАКСОПАРКИ Т ON Т.код = П.таксопарк
WHERE Т.название = 'Flash Cab' AND П.расстояние_км < 2;

DELETE FROM ПОЕЗДКИ USING ТАКСОПАРКИ
WHERE ПОЕЗДКИ.таксопарк = ТАКСОПАРКИ.код
  AND ТАКСОПАРКИ.название = 'Flash Cab'
  AND ПОЕЗДКИ.расстояние_км < 2;

\echo '=== КОЛИЧЕСТВО ПОСЛЕ DELETE ==='
SELECT COUNT(*) FROM ПОЕЗДКИ П JOIN ТАКСОПАРКИ Т ON Т.код = П.таксопарк
WHERE Т.название = 'Flash Cab' AND П.расстояние_км < 2;

-- Демонстрация: изменения откатываются, чтобы повторный запуск
-- не портил базу. Чтобы сохранить их, замените ROLLBACK на COMMIT.
ROLLBACK;
