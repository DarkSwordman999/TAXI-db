-- INSERT INTO TAB1 VALUES (...)
-- Добавление нового автомобиля

BEGIN;

\echo '=== ДО INSERT ==='
SELECT * FROM АВТОМОБИЛИ WHERE код = 31;

INSERT INTO АВТОМОБИЛИ VALUES (31, 'A999AA', 'Lada', 'Granta', 2023, 'Белый', 'эконом');

\echo '=== ПОСЛЕ INSERT ==='
SELECT * FROM АВТОМОБИЛИ WHERE код = 31;

-- Демонстрация: изменения откатываются, чтобы повторный запуск
-- не портил базу. Чтобы сохранить их, замените ROLLBACK на COMMIT.
ROLLBACK;
