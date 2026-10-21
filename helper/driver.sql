-- ./help.sh driver код — информация о водителе
-- параметры: :arg1 — код (help.sh задает их через \set, psql сам экранирует кавычки)
SELECT
    В.код,
    В.taxi_id,
    COUNT(П.код_поездки) AS поездок,
    SUM(П.стоимость) AS выручка,
    MIN(П.дата)::date AS первая,
    MAX(П.дата)::date AS последняя
FROM ВОДИТЕЛИ В
LEFT JOIN ПОЕЗДКИ П ON П.водитель = В.код
WHERE В.код = :arg1
GROUP BY В.код;
