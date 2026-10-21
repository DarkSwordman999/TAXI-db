-- ./help.sh set-tips поездка сумма — изменить чаевые поездки
-- параметры: :arg1 — поездка, :arg2 — сумма (help.sh задает их через \set, psql сам экранирует кавычки)
UPDATE ПОЕЗДКИ
SET чаевые = :arg2
WHERE код_поездки = :arg1;

SELECT *
FROM v_rides_user
WHERE код_поездки = :arg1;
