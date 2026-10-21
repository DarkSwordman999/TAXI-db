-- ./help.sh set-ride-company поездка парк — сменить таксопарк поездки (коды)
-- параметры: :arg1 — поездка, :arg2 — парк (help.sh задает их через \set, psql сам экранирует кавычки)
UPDATE ПОЕЗДКИ
SET таксопарк = :arg2
WHERE код_поездки = :arg1;

SELECT *
FROM v_rides_user
WHERE код_поездки = :arg1;
