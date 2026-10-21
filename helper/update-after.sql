-- Состояние ПОСЛЕ UPDATE
\echo '=== СОСТОЯНИЕ ПОСЛЕ UPDATE ==='
SELECT 'ТАКСОПАРКИ (код=1)' as Объект, название as Значение FROM ТАКСОПАРКИ WHERE код = 1
UNION ALL
SELECT 'ОПЛАТА (тип Unknown)', описание FROM ОПЛАТА WHERE тип = 'Unknown';
