-- Быстрое переименование таксопарка
-- Использование: psql -d taxi -v company_id=1 -v new_name='Новое название' -f helper/22_quick_update.sql
-- или: ./help.sh helper/22_quick_update.sql 1 (код таксопарка, название по умолчанию)

-- значения по умолчанию: код из arg1 (./help.sh файл.sql код) или 1
\if :{?company_id}
\elif :{?arg1}
    \set company_id :arg1
\else
    \set company_id 1
\endif
\if :{?new_name}
\else
    \set new_name 'Новое название'
\endif

BEGIN;

\echo '=== ДО UPDATE ==='
SELECT код, название FROM ТАКСОПАРКИ WHERE код = :company_id;

UPDATE ТАКСОПАРКИ SET название = :'new_name' WHERE код = :company_id;

\echo '=== ПОСЛЕ UPDATE ==='
SELECT код, название FROM ТАКСОПАРКИ WHERE код = :company_id;

-- Демонстрация: изменения откатываются, чтобы повторный запуск
-- не портил базу. Чтобы сохранить их, замените ROLLBACK на COMMIT.
ROLLBACK;
