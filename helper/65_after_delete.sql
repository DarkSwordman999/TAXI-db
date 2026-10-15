-- Состояние ПОСЛЕ DELETE
\echo '=== СОСТОЯНИЕ ПОСЛЕ DELETE ==='
SELECT 'ВОДИТЕЛИ (код=30)' as Объект, COALESCE((SELECT taxi_id FROM ВОДИТЕЛИ WHERE код = 30), 'удалён') as Значение;
SELECT 'Поездки водителя 30' as Объект, COUNT(*)::text as Значение FROM ПОЕЗДКИ WHERE водитель = 30;
