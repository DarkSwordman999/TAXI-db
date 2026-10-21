-- Состояние ПОСЛЕ UPDATE
\echo '=== СОСТОЯНИЕ ПОСЛЕ UPDATE ==='
SELECT 'ТАКСОПАРКИ (код=1)' as Объект, название as Значение FROM ТАКСОПАРКИ WHERE код = 1
UNION ALL
SELECT 'КЛИЕНТЫ (тип Unknown)', описание FROM КЛИЕНТЫ WHERE тип = 'Unknown';
