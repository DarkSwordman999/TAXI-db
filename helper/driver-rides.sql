-- ./help.sh driver-rides код — последние поездки водителя
-- параметры: :arg1 — код (help.sh задает их через \set, psql сам экранирует кавычки)
SELECT *
FROM v_rides_user
WHERE водитель = 'Водитель №' || :arg1
ORDER BY дата DESC
LIMIT 10;
