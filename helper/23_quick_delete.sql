-- Быстрое удаление водителя
-- Использование: psql -d taxi -v driver_id=30 -f helper/23_quick_delete.sql
-- или: ./help.sh helper/23_quick_delete.sql 30

-- значение по умолчанию: код из arg1 (./help.sh файл.sql код) или 1
\if :{?driver_id}
\elif :{?arg1}
    \set driver_id :arg1
\else
    \set driver_id 1
\endif

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
