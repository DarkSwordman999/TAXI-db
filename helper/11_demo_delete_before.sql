-- Состояние ДО DELETE
SELECT 'ВОДИТЕЛИ (код=30)' as Таблица, фамилия || ' ' || имя FROM ВОДИТЕЛИ WHERE код = 30
UNION ALL
SELECT 'Поездки с расстоянием < 2 км', COUNT(*)::text FROM ПОЕЗДКИ WHERE расстояние_км < 2;
