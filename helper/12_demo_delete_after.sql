-- Состояние ПОСЛЕ DELETE
SELECT 'ВОДИТЕЛИ (код=30)' as Таблица, COALESCE((SELECT taxi_id FROM ВОДИТЕЛИ WHERE код = 30), 'удалён')
UNION ALL
SELECT 'Поездки с расстоянием < 2 км', COUNT(*)::text FROM ПОЕЗДКИ WHERE расстояние_км < 2;
