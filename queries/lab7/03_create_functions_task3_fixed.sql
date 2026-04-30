-- ============================================================
-- ЛАБОРАТОРНАЯ РАБОТА №7 - TAXI
-- ЗАДАЧА 3: Сводная таблица (водители × классы авто)
-- ============================================================

DROP FUNCTION IF EXISTS display_pivot_table();

CREATE OR REPLACE FUNCTION display_pivot_table()
RETURNS TABLE(
    водитель TEXT,
    эконом NUMERIC,
    комфорт NUMERIC,
    бизнес NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (В.фамилия || ' ' || В.имя)::TEXT,
        COALESCE(SUM(П.стоимость) FILTER (WHERE А.класс = 'эконом'), 0)::NUMERIC,
        COALESCE(SUM(П.стоимость) FILTER (WHERE А.класс = 'комфорт'), 0)::NUMERIC,
        COALESCE(SUM(П.стоимость) FILTER (WHERE А.класс = 'бизнес'), 0)::NUMERIC
    FROM ВОДИТЕЛИ В
    LEFT JOIN ПОЕЗДКИ П ON П.водитель = В.код
    LEFT JOIN АВТОМОБИЛИ А ON А.код = П.автомобиль
    GROUP BY В.фамилия, В.имя
    HAVING COALESCE(SUM(П.стоимость), 0) > 0
    ORDER BY В.фамилия
    LIMIT 15;
END;
$$ LANGUAGE PLpgSQL;
