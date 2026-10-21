-- ./help.sh avg-check — средний чек
SELECT
    ROUND(AVG(стоимость), 2) AS средний,
    MIN(стоимость) AS мин,
    MAX(стоимость) AS макс
FROM ПОЕЗДКИ;
