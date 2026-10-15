-- Быстрое удаление водителя
-- Использование: psql -d taxi_lab5 -v driver_id=30 -f helper/23_quick_delete.sql

BEGIN;

\echo '=== ДО DELETE ==='
SELECT код, taxi_id FROM ВОДИТЕЛИ WHERE код = :driver_id;
SELECT COUNT(*) AS поездок_водителя FROM ПОЕЗДКИ WHERE водитель = :driver_id;

DELETE FROM ПОЕЗДКИ WHERE водитель = :driver_id;
DELETE FROM ВОДИТЕЛИ WHERE код = :driver_id;

\echo '=== ПОСЛЕ DELETE ==='
SELECT код, taxi_id FROM ВОДИТЕЛИ WHERE код = :driver_id;
SELECT COUNT(*) AS поездок_водителя FROM ПОЕЗДКИ WHERE водитель = :driver_id;

-- Демонстрация: изменения откатываются, чтобы повторный запуск
-- не портил базу. Чтобы сохранить их, замените ROLLBACK на COMMIT.
ROLLBACK;
