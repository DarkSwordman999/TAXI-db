-- Быстрое переименование таксопарка
-- Использование: psql -d taxi -v company_id=1 -v new_name='Новое название' -f helper/rename-demo.sql
-- или: ./help.sh rename-demo 1 'Новое название' (название можно не указывать)

-- значения по умолчанию: код из arg1, название из arg2, иначе код 1 и «Новое название»
\if :{?company_id}
\elif :{?arg1}
    \set company_id :arg1
\else
    \set company_id 1
\endif
\if :{?new_name}
\elif :{?arg2}
    \set new_name :arg2
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
