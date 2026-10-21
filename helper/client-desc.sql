-- ./help.sh client-desc код описание — изменить описание типа клиента
-- параметры: :arg1 — код, :'arg2' — описание (help.sh задает их через \set, psql сам экранирует кавычки)
UPDATE КЛИЕНТЫ
SET описание = :'arg2'
WHERE код = :arg1;

SELECT *
FROM КЛИЕНТЫ
WHERE код = :arg1;
