-- ============================================================
-- ФУНКЦИИ POSTGRESQL - TAXI
-- ЗАДАЧА 1: Распределение по одному признаку
-- Выручка водителей с порогом
-- ============================================================

-- Функция 1.1: Скалярная функция - выручка водителя
DROP FUNCTION IF EXISTS get_driver_revenue(INT);

CREATE OR REPLACE FUNCTION get_driver_revenue(p_driver_code INT)
RETURNS NUMERIC(10,2) AS $$
BEGIN
    RETURN (
        SELECT COALESCE(SUM(стоимость), 0)
        FROM ПОЕЗДКИ
        WHERE водитель = p_driver_code
    );
END;
$$ LANGUAGE PLpgSQL;

-- Функция 1.2: Табличная функция - водители с выручкой выше порога
DROP FUNCTION IF EXISTS drivers_above_revenue(NUMERIC);

CREATE OR REPLACE FUNCTION drivers_above_revenue(p_min_revenue NUMERIC DEFAULT 10000)
RETURNS TABLE(
    водитель_код INT,
    водитель TEXT,
    поездок BIGINT,
    выручка NUMERIC(10,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        Р.код,
        'Водитель №' || Р.код,
        (SELECT COUNT(*) FROM ПОЕЗДКИ WHERE ПОЕЗДКИ.водитель = Р.код),
        Р.сумма
    FROM (
        -- выручка считается один раз на водителя, а не в SELECT и WHERE отдельно
        SELECT В.код, get_driver_revenue(В.код) AS сумма
        FROM ВОДИТЕЛИ В
    ) Р
    WHERE Р.сумма >= p_min_revenue
    ORDER BY Р.сумма DESC;
END;
$$ LANGUAGE PLpgSQL;
