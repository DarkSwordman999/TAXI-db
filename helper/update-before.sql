-- Состояние ДО UPDATE
\echo '=== СОСТОЯНИЕ ДО UPDATE ==='
SELECT 'ТАКСОПАРКИ (код=1)' as Объект, название as Значение FROM ТАКСОПАРКИ WHERE код = 1
UNION ALL
SELECT 'ОПЛАТА (тип Unknown)', описание FROM ОПЛАТА WHERE тип = 'Unknown';
