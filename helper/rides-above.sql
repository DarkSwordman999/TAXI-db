-- ./help.sh rides-above сумма — поездки дороже суммы
-- параметры: :arg1 — сумма (help.sh задает их через \set, psql сам экранирует кавычки)
SELECT *
FROM ПОЕЗДКИ
WHERE стоимость > :arg1
ORDER BY стоимость DESC
LIMIT 10;
