-- ./help.sh delete-driver код — удалить водителя вместе с поездками
-- параметры: :arg1 — код (help.sh задает их через \set, psql сам экранирует кавычки)
DELETE
FROM ПОЕЗДКИ
WHERE водитель = :arg1;

DELETE
FROM ВОДИТЕЛИ
WHERE код = :arg1;
