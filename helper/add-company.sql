-- ./help.sh add-company название — добавить таксопарк
-- параметры: :'arg1' — название (help.sh задает их через \set, psql сам экранирует кавычки)
INSERT INTO ТАКСОПАРКИ (название) VALUES (:'arg1');

SELECT *
FROM ТАКСОПАРКИ
ORDER BY код DESC
LIMIT 1;
