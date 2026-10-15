-- Быстрое переименование таксопарка
-- Использование: psql -d taxi -v company_id=1 -v new_name='Новое название' -f helper/22_quick_update.sql

BEGIN;

\echo '=== ДО UPDATE ==='
SELECT код, название FROM ТАКСОПАРКИ WHERE код = :company_id;

UPDATE ТАКСОПАРКИ SET название = :'new_name' WHERE код = :company_id;

\echo '=== ПОСЛЕ UPDATE ==='
SELECT код, название FROM ТАКСОПАРКИ WHERE код = :company_id;

-- Демонстрация: изменения откатываются, чтобы повторный запуск
-- не портил базу. Чтобы сохранить их, замените ROLLBACK на COMMIT.
ROLLBACK;
