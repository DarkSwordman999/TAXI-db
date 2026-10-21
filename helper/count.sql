-- ./help.sh count — количество поездок
SELECT
    COUNT(*) AS поездок,
    MIN(дата)::date AS с,
    MAX(дата)::date AS по
FROM ПОЕЗДКИ;
