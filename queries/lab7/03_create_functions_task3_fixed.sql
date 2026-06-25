-- ============================================================
-- ЛАБОРАТОРНАЯ РАБОТА №7 - TAXI
-- ЗАДАЧА 3: Сводная таблица (водители × классы авто)
-- ============================================================

DROP FUNCTION IF EXISTS get_driver_revenue_by_class(INT, VARCHAR);
DROP FUNCTION IF EXISTS display_pivot_table();

CREATE OR REPLACE FUNCTION get_driver_revenue_by_class(p_driver_code INT, p_class_name VARCHAR)
RETURNS NUMERIC(10,2) AS $$
BEGIN
    RETURN (
        SELECT COALESCE(SUM(П.стоимость), 0)::NUMERIC(10,2)
        FROM ПОЕЗДКИ П
        JOIN АВТОМОБИЛИ А ON А.код = П.автомобиль
        WHERE П.водитель = p_driver_code
          AND А.класс = p_class_name
    );
END;
$$ LANGUAGE PLpgSQL;

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
        get_driver_revenue_by_class(В.код, 'эконом')::NUMERIC,
        get_driver_revenue_by_class(В.код, 'комфорт')::NUMERIC,
        get_driver_revenue_by_class(В.код, 'бизнес')::NUMERIC
    FROM ВОДИТЕЛИ В
    WHERE get_driver_revenue(В.код) > 0
    ORDER BY В.фамилия
    LIMIT 15;
END;
$$ LANGUAGE PLpgSQL;
