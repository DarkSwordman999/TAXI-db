-- Полная пересборка базы TAXI: схема, справочники, представления и функции.
-- Поездки загружает parser/load_rides.py; обе части вместе запускает setup/rebuild.sh.
-- Запуск только схемы: psql -d taxi -f setup/rebuild_database.sql

\echo '=== TAXI: очистка старых объектов ==='
DROP VIEW IF EXISTS v_rides_tech;
DROP VIEW IF EXISTS v_rides_user;
DROP VIEW IF EXISTS taxi_client_report;
DROP VIEW IF EXISTS taxi_driver_report;
DROP VIEW IF EXISTS taxi_full_rides;

DROP FUNCTION IF EXISTS display_pivot_table();
DROP FUNCTION IF EXISTS revenue_by_class_and_season();
DROP FUNCTION IF EXISTS revenue_by_company_and_season();
DROP FUNCTION IF EXISTS get_class_avg_revenue(VARCHAR);
DROP FUNCTION IF EXISTS get_company_avg_revenue(VARCHAR);
DROP FUNCTION IF EXISTS drivers_above_revenue(NUMERIC);
DROP FUNCTION IF EXISTS get_driver_revenue_by_class(INT, VARCHAR);
DROP FUNCTION IF EXISTS get_driver_revenue_by_client(INT, VARCHAR);
DROP FUNCTION IF EXISTS get_driver_revenue(INT);
DROP FUNCTION IF EXISTS random_date(DATE, DATE);

-- включая таблицы прежней схемы (АВТОМОБИЛИ, ТАРИФЫ)
DROP TABLE IF EXISTS ПОЕЗДКИ_АРХИВ;
DROP TABLE IF EXISTS ПОЕЗДКИ;
DROP TABLE IF EXISTS СЕЗОН;
DROP TABLE IF EXISTS КЛИЕНТЫ;
DROP TABLE IF EXISTS ВОДИТЕЛИ;
DROP TABLE IF EXISTS АВТОМОБИЛИ;
DROP TABLE IF EXISTS ТАРИФЫ;
DROP TABLE IF EXISTS ТАКСОПАРКИ;
DROP TABLE IF EXISTS РАЙОНЫ;

\echo '=== TAXI: создание таблиц ==='
\ir ../schema/tables/01_create_companies.sql
\ir ../schema/tables/02_create_drivers.sql
\ir ../schema/tables/03_create_clients.sql
\ir ../schema/tables/04_create_areas.sql
\ir ../schema/tables/05_create_rides.sql
\ir ../schema/tables/06_create_season.sql
\ir ../schema/indexes/01_create_indexes.sql

\echo '=== TAXI: загрузка справочников ==='
\ir ../data/season/01_insert_season.sql
\copy РАЙОНЫ (код, название, широта, долгота) FROM 'data/chicago/community_areas.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')

\echo '=== TAXI: создание представлений и функций ==='
\ir ../queries/views/01_create_rides_view.sql
\ir ../queries/views/02_create_rides_tech.sql
\ir ../queries/functions/01_create_functions_task1.sql
\ir ../queries/functions/02_create_functions_task2.sql
\ir ../queries/functions/03_create_functions_task3.sql

\echo '=== TAXI: схема готова, поездки загружает parser/load_rides.py ==='
