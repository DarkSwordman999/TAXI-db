-- ./help.sh add-driver taxi_id — добавить водителя
-- параметры: :'arg1' — taxi_id (help.sh задает их через \set, psql сам экранирует кавычки)
INSERT INTO ВОДИТЕЛИ (taxi_id) VALUES (:'arg1');

SELECT *
FROM ВОДИТЕЛИ
ORDER BY код DESC
LIMIT 1;
