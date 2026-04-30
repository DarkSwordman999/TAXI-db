-- UPDATE TAB1 SET поле = значение WHERE ключ = значение_ключа
-- Изменение госномера автомобиля с кодом 1

\echo '=== ДО UPDATE ==='
SELECT * FROM АВТОМОБИЛИ WHERE код = 1;

UPDATE АВТОМОБИЛИ SET гос_номер = 'A888AA' WHERE код = 1;

\echo '=== ПОСЛЕ UPDATE ==='
SELECT * FROM АВТОМОБИЛИ WHERE код = 1;
