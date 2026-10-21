-- Перевод базы версии 1.x на схему 2.0 без пересборки: данные сохраняются.
-- Таблица КЛИЕНТЫ → ОПЛАТА, поле ПОЕЗДКИ.клиент → оплата, индекс и ограничения — под новые имена;
-- представления и функции пересоздаются (get_driver_revenue_by_client остается синонимом).
--
-- Запуск из корня проекта: psql -d taxi -f setup/migrate_to_v2.sql
-- Повторный запуск безопасен: уже переведенная база не меняется.

\set ON_ERROR_STOP 1

SELECT to_regclass('КЛИЕНТЫ') IS NOT NULL AS need_migration \gset
\if :need_migration
    \echo '=== TAXI: перевод на схему 2.0 ==='
    BEGIN;
    -- представления ссылаются на старые имена: пересоздаются ниже
    DROP VIEW IF EXISTS v_rides_tech;
    DROP VIEW IF EXISTS v_rides_user;

    ALTER TABLE КЛИЕНТЫ RENAME TO ОПЛАТА;
    ALTER TABLE ПОЕЗДКИ RENAME COLUMN клиент TO оплата;
    ALTER INDEX IF EXISTS idx_rides_client RENAME TO idx_rides_payment;
    ALTER SEQUENCE IF EXISTS "КЛИЕНТЫ_код_seq" RENAME TO "ОПЛАТА_код_seq";

    -- ограничения названы по старым именам (КЛИЕНТЫ_pkey, ПОЕЗДКИ_клиент_fkey, …):
    -- переименовываются так, как их назвала бы чистая сборка
    DO $$
    DECLARE r RECORD;
    BEGIN
        FOR r IN
            SELECT conrelid::regclass AS tbl, conname,
                   replace(replace(conname, 'КЛИЕНТЫ', 'ОПЛАТА'), '_клиент_', '_оплата_') AS new_name
            FROM pg_constraint
            WHERE conrelid IN ('ОПЛАТА'::regclass, 'ПОЕЗДКИ'::regclass)
              AND (conname LIKE '%КЛИЕНТЫ%' OR conname LIKE '%\_клиент\_%')
        LOOP
            EXECUTE format('ALTER TABLE %s RENAME CONSTRAINT %I TO %I', r.tbl, r.conname, r.new_name);
        END LOOP;
    END $$;
    COMMIT;
\else
    \echo '=== TAXI: база уже на схеме 2.0, таблицы не меняются ==='
\endif

\echo '=== TAXI: пересоздание представлений и функций ==='
\ir ../queries/views/01_create_rides_view.sql
\ir ../queries/views/02_create_rides_tech.sql
\ir ../queries/functions/03_create_functions_task3.sql

\echo '=== TAXI: готово ==='
SELECT (SELECT count(*) FROM ОПЛАТА) AS способов_оплаты,
       (SELECT count(*) FROM ПОЕЗДКИ) AS поездок;
