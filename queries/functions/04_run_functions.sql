\echo '============================================='
\echo 'ФУНКЦИИ POSTGRESQL - TAXI'
\echo 'ПРОВЕРКА ФУНКЦИЙ'
\echo '============================================='

\echo ''
\echo '--- ЗАДАЧА 1.1: get_driver_revenue(1) ---'
SELECT get_driver_revenue(1);

\echo ''
\echo '--- ЗАДАЧА 1.2: drivers_above_revenue(10000) ---'
SELECT * FROM drivers_above_revenue(10000) LIMIT 20;

\echo ''
\echo '--- ЗАДАЧА 1.2 с параметром 8000 ---'
SELECT * FROM drivers_above_revenue(8000) LIMIT 20;

\echo ''
\echo '--- ЗАДАЧА 2.1: get_company_avg_revenue(''Flash Cab'') ---'
SELECT get_company_avg_revenue('Flash Cab');

\echo ''
\echo '--- ЗАДАЧА 2.2: revenue_by_company_and_season() ---'
SELECT * FROM revenue_by_company_and_season();

\echo ''
\echo '--- ЗАДАЧА 3.1: get_driver_revenue_by_payment(1, ''Credit Card'') ---'
SELECT get_driver_revenue_by_payment(1, 'Credit Card');

\echo ''
\echo '--- ЗАДАЧА 3.2: display_pivot_table() ---'
SELECT * FROM display_pivot_table();
