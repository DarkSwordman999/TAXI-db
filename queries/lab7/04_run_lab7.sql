\echo '============================================='
\echo 'ЛАБОРАТОРНАЯ РАБОТА №7 - TAXI'
\echo 'ПРОВЕРКА ФУНКЦИЙ'
\echo '============================================='

\echo ''
\echo '--- ЗАДАЧА 1.1: get_driver_revenue(1) ---'
SELECT get_driver_revenue(1);

\echo ''
\echo '--- ЗАДАЧА 1.2: drivers_above_revenue(10000) ---'
SELECT * FROM drivers_above_revenue(10000);

\echo ''
\echo '--- ЗАДАЧА 1.2 с параметром 8000 ---'
SELECT * FROM drivers_above_revenue(8000);

\echo ''
\echo '--- ЗАДАЧА 2.1: get_class_avg_revenue(''бизнес'') ---'
SELECT get_class_avg_revenue('бизнес');

\echo ''
\echo '--- ЗАДАЧА 2.2: revenue_by_class_and_season() ---'
SELECT * FROM revenue_by_class_and_season();

\echo ''
\echo '--- ЗАДАЧА 3.1: get_driver_revenue_by_class(1, ''бизнес'') ---'
SELECT get_driver_revenue_by_class(1, 'бизнес');

\echo ''
\echo '--- ЗАДАЧА 3.2: display_pivot_table() ---'
SELECT * FROM display_pivot_table();
