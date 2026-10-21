-- Состояние ДО DELETE
\echo '=== СОСТОЯНИЕ ДО DELETE ==='
SELECT 'ВОДИТЕЛИ (код=30)' as Объект, taxi_id as Значение FROM ВОДИТЕЛИ WHERE код = 30;
SELECT 'Поездки водителя 30' as Объект, COUNT(*)::text as Значение FROM ПОЕЗДКИ WHERE водитель = 30;
