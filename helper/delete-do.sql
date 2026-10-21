-- ВЫПОЛНЕНИЕ DELETE (изменения сохраняются; вернуть исходные данные — setup/rebuild.sh)
\echo '=== ВЫПОЛНЯЕМ DELETE ==='
DELETE FROM ПОЕЗДКИ WHERE водитель = 30;
DELETE FROM ВОДИТЕЛИ WHERE код = 30;
\echo 'DELETE ВЫПОЛНЕН'
