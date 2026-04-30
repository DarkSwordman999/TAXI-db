-- ВЫПОЛНЕНИЕ UPDATE
\echo '=== ВЫПОЛНЯЕМ UPDATE ==='
UPDATE АВТОМОБИЛИ SET гос_номер = 'A999AA' WHERE код = 1;
UPDATE ВОДИТЕЛИ SET телефон = '+79999999999' WHERE код = 1;
\echo 'UPDATE ВЫПОЛНЕН'
