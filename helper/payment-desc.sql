-- ./help.sh payment-desc код описание (прежнее имя client-desc) — изменить описание способа оплаты
-- параметры: :arg1 — код, :'arg2' — описание (help.sh задает их через \set, psql сам экранирует кавычки)
UPDATE ОПЛАТА
SET описание = :'arg2'
WHERE код = :arg1;

SELECT *
FROM ОПЛАТА
WHERE код = :arg1;
