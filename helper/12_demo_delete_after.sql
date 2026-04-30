-- Состояние ПОСЛЕ DELETE
SELECT 'ВОДИТЕЛИ (код=30)' as Таблица, COALESCE(фамилия || ' ' || имя, 'удалён') FROM ВОДИТЕЛИ WHERE код = 30
UNION ALL
SELECT 'Поездки с расстоянием < 2 км', COUNT(*)::text FROM ПОЕЗДКИ WHERE расстояние_км < 2;
