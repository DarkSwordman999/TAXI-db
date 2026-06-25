-- Полная пересборка учебной базы TAXI.
-- Запуск: psql -d taxi_lab5 -f setup/rebuild_database.sql

\echo '=== TAXI: очистка старых объектов ==='
DROP VIEW IF EXISTS v_rides_tech;
DROP VIEW IF EXISTS v_rides_user;
DROP VIEW IF EXISTS taxi_client_report;
DROP VIEW IF EXISTS taxi_driver_report;
DROP VIEW IF EXISTS taxi_full_rides;

DROP FUNCTION IF EXISTS display_pivot_table();
DROP FUNCTION IF EXISTS revenue_by_class_and_season();
DROP FUNCTION IF EXISTS get_class_avg_revenue(VARCHAR);
DROP FUNCTION IF EXISTS drivers_above_revenue(NUMERIC);
DROP FUNCTION IF EXISTS get_driver_revenue_by_class(INT, VARCHAR);
DROP FUNCTION IF EXISTS get_driver_revenue(INT);
DROP FUNCTION IF EXISTS random_date(DATE, DATE);

DROP TABLE IF EXISTS ПОЕЗДКИ_АРХИВ;
DROP TABLE IF EXISTS ПОЕЗДКИ;
DROP TABLE IF EXISTS СЕЗОН;
DROP TABLE IF EXISTS ТАРИФЫ;
DROP TABLE IF EXISTS КЛИЕНТЫ;
DROP TABLE IF EXISTS ВОДИТЕЛИ;
DROP TABLE IF EXISTS АВТОМОБИЛИ;

\echo '=== TAXI: создание таблиц ==='
\ir ../schema/tables/01_create_cars.sql
\ir ../schema/tables/02_create_drivers.sql
\ir ../schema/tables/03_create_clients.sql
\ir ../schema/tables/04_create_tariffs.sql
\ir ../schema/tables/05_create_rides.sql
\ir ../schema/tables/06_create_season.sql
\ir ../schema/indexes/01_create_indexes.sql

\echo '=== TAXI: загрузка справочников ==='
\ir ../data/cars/01_insert_cars.sql
\ir ../data/drivers/01_insert_drivers.sql
\ir ../data/clients/01_insert_clients.sql
\ir ../data/insert_200_clients_fixed.sql
\ir ../data/tariffs/01_insert_tariffs.sql
\ir ../data/season/01_insert_season.sql

\echo '=== TAXI: генерация поездок ==='
\ir ../functions/random_date/01_create_function.sql
\ir ../generation/generate_1000_rides.sql
\ir ../control/inserts/add_control_rides.sql
\ir ../control/inserts/add_expensive_rides.sql
\ir sync_sequences.sql

\echo '=== TAXI: создание представлений и функций ==='
\ir ../queries/views/01_create_rides_view.sql
\ir ../queries/views/02_create_rides_tech.sql
\ir ../queries/lab7/01_create_functions_task1.sql
\ir ../queries/lab7/02_create_functions_task2.sql
\ir ../queries/lab7/03_create_functions_task3_fixed.sql

\echo '=== TAXI: итоговые счетчики ==='
SELECT 'АВТОМОБИЛИ' AS таблица, COUNT(*) AS строк FROM АВТОМОБИЛИ
UNION ALL SELECT 'ВОДИТЕЛИ', COUNT(*) FROM ВОДИТЕЛИ
UNION ALL SELECT 'КЛИЕНТЫ', COUNT(*) FROM КЛИЕНТЫ
UNION ALL SELECT 'ТАРИФЫ', COUNT(*) FROM ТАРИФЫ
UNION ALL SELECT 'СЕЗОН', COUNT(*) FROM СЕЗОН
UNION ALL SELECT 'ПОЕЗДКИ', COUNT(*) FROM ПОЕЗДКИ
ORDER BY таблица;
