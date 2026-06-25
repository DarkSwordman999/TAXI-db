-- Быстрое удаление водителя
-- Использование: psql -d taxi_lab5 -v driver_id=30 -f helper/23_quick_delete.sql

\echo '=== ДО DELETE ==='
SELECT код, фамилия, имя FROM ВОДИТЕЛИ WHERE код = :driver_id;
SELECT COUNT(*) AS поездок_водителя FROM ПОЕЗДКИ WHERE водитель = :driver_id;

BEGIN;
DELETE FROM ПОЕЗДКИ WHERE водитель = :driver_id;
DELETE FROM ВОДИТЕЛИ WHERE код = :driver_id;
COMMIT;

\echo '=== ПОСЛЕ DELETE ==='
SELECT код, фамилия, имя FROM ВОДИТЕЛИ WHERE код = :driver_id;
SELECT COUNT(*) AS поездок_водителя FROM ПОЕЗДКИ WHERE водитель = :driver_id;
