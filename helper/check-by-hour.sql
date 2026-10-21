-- ./help.sh check-by-hour — средний чек по часам
SELECT
    EXTRACT(HOUR FROM дата) AS час,
    ROUND(AVG(стоимость), 2) AS средний_чек
FROM ПОЕЗДКИ
GROUP BY час
ORDER BY час;
