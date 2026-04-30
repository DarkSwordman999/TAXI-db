\echo '=== ОРИГИНАЛЬНАЯ ТАБЛИЦА ПОЕЗДКИ (первые 5 записей) ==='
SELECT * 
FROM ПОЕЗДКИ LIMIT 5;

\echo ''
\echo '=== ПОЛЬЗОВАТЕЛЬСКОЕ ПРЕДСТАВЛЕНИЕ (первые 5 записей) ==='
SELECT * FROM v_rides_user LIMIT 5;

\echo ''
\echo '=== ТЕХНОЛОГИЧЕСКОЕ ПРЕДСТАВЛЕНИЕ (первые 5 записей) ==='
SELECT * FROM v_rides_tech LIMIT 5;
