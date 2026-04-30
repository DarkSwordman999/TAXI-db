-- ============================================================
-- ЛАБОРАТОРНАЯ РАБОТА №7 - TAXI
-- ЗАДАЧА 2: Распределение по двум признакам
-- Выручка по классам авто и сезонам
-- ============================================================

-- Функция 2.1: Скалярная функция - средняя выручка по классу
DROP FUNCTION IF EXISTS get_class_avg_revenue(VARCHAR);

CREATE OR REPLACE FUNCTION get_class_avg_revenue(p_class_name VARCHAR)
RETURNS NUMERIC(10,2) AS $$
BEGIN
    RETURN (
        SELECT COALESCE(AVG(П.стоимость), 0)
        FROM ПОЕЗДКИ П
        JOIN АВТОМОБИЛИ А ON А.код = П.автомобиль
        WHERE А.класс = p_class_name
    );
END;
$$ LANGUAGE PLpgSQL;

-- Функция 2.2: Табличная функция - выручка по классам и сезонам
DROP FUNCTION IF EXISTS revenue_by_class_and_season();

CREATE OR REPLACE FUNCTION revenue_by_class_and_season()
RETURNS TABLE(
    класс VARCHAR,
    сезон VARCHAR,
    выручка NUMERIC(10,2),
    количество_поездок BIGINT,
    порядок_сезона INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        А.класс,
        С.сезон,
        COALESCE(SUM(П.стоимость), 0),
        COUNT(П.код_поездки),
        MIN(С.порядок)
    FROM АВТОМОБИЛИ А
    LEFT JOIN ПОЕЗДКИ П ON А.код = П.автомобиль
    LEFT JOIN СЕЗОН С ON С.месяц = EXTRACT(MONTH FROM П.дата)
    GROUP BY А.класс, С.сезон
    ORDER BY А.класс, MIN(С.порядок);
END;
$$ LANGUAGE PLpgSQL;
