-- Быстрое удаление водителя
-- Использование: psql -d taxi_lab5 -v driver_id=30 -f helper/23_quick_delete.sql

\echo '=== ДО DELETE ==='
SELECT код, фамилия, имя FROM ВОДИТЕЛИ WHERE код = :driver_id;

DELETE FROM ВОДИТЕЛИ WHERE код = :driver_id;

\echo '=== ПОСЛЕ DELETE ==='
SELECT код, фамилия, имя FROM ВОДИТЕЛИ WHERE код = :driver_id;
