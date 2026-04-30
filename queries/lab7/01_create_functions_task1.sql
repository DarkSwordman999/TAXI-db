-- ============================================================
-- ЛАБОРАТОРНАЯ РАБОТА №7 - TAXI
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
    фамилия VARCHAR,
    имя VARCHAR,
    выручка NUMERIC(10,2),
    стаж_лет INT,
    рейтинг NUMERIC(3,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        В.код,
        В.фамилия,
        В.имя,
        get_driver_revenue(В.код),
        В.стаж_лет,
        В.рейтинг
    FROM ВОДИТЕЛИ В
    WHERE get_driver_revenue(В.код) >= p_min_revenue
    ORDER BY выручка DESC;
END;
$$ LANGUAGE PLpgSQL;
