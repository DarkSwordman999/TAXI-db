-- DELETE FROM TAB1 WHERE ключ = значение_ключа
-- Удаление водителя с кодом 30

BEGIN;

\echo '=== ДО DELETE ==='
SELECT * FROM ВОДИТЕЛИ WHERE код = 30;
SELECT COUNT(*) AS поездок_водителя FROM ПОЕЗДКИ WHERE водитель = 30;

DELETE FROM ПОЕЗДКИ WHERE водитель = 30;
DELETE FROM ВОДИТЕЛИ WHERE код = 30;

\echo '=== ПОСЛЕ DELETE ==='
SELECT * FROM ВОДИТЕЛИ WHERE код = 30;
SELECT COUNT(*) AS поездок_водителя FROM ПОЕЗДКИ WHERE водитель = 30;

-- Демонстрация: изменения откатываются, чтобы повторный запуск
-- не портил базу. Чтобы сохранить их, замените ROLLBACK на COMMIT.
ROLLBACK;
