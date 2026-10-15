-- Быстрое обновление госномера автомобиля
-- Использование: psql -d taxi -v car_id=1 -v new_number='А999АА' -f helper/22_quick_update.sql

BEGIN;

\echo '=== ДО UPDATE ==='
SELECT код, гос_номер, марка, модель FROM АВТОМОБИЛИ WHERE код = :car_id;

UPDATE АВТОМОБИЛИ SET гос_номер = :'new_number' WHERE код = :car_id;

\echo '=== ПОСЛЕ UPDATE ==='
SELECT код, гос_номер, марка, модель FROM АВТОМОБИЛИ WHERE код = :car_id;

-- Демонстрация: изменения откатываются, чтобы повторный запуск
-- не портил базу. Чтобы сохранить их, замените ROLLBACK на COMMIT.
ROLLBACK;
