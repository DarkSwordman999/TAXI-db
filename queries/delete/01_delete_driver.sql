-- DELETE FROM TAB1 WHERE ключ = значение_ключа
-- Удаление водителя с кодом 30

\echo '=== ДО DELETE ==='
SELECT * FROM ВОДИТЕЛИ WHERE код = 30;

DELETE FROM ВОДИТЕЛИ WHERE код = 30;

\echo '=== ПОСЛЕ DELETE ==='
SELECT * FROM ВОДИТЕЛИ WHERE код = 30;
