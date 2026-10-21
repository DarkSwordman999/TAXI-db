-- ./help.sh rename-company код название — переименовать таксопарк
-- параметры: :arg1 — код, :'arg2' — название (help.sh задает их через \set, psql сам экранирует кавычки)
UPDATE ТАКСОПАРКИ
SET название = :'arg2'
WHERE код = :arg1;

SELECT *
FROM ТАКСОПАРКИ
WHERE код = :arg1;
