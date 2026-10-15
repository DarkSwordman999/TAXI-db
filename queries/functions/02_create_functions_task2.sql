-- ============================================================
-- ФУНКЦИИ POSTGRESQL - TAXI
-- ЗАДАЧА 2: Распределение по двум признакам
-- Выручка по таксопаркам и сезонам
-- ============================================================

-- Функция 2.1: Скалярная функция - средняя стоимость поездки в таксопарке
DROP FUNCTION IF EXISTS get_company_avg_revenue(VARCHAR);

CREATE OR REPLACE FUNCTION get_company_avg_revenue(p_company_name VARCHAR)
RETURNS NUMERIC(10,2) AS $$
BEGIN
    RETURN (
        SELECT COALESCE(AVG(П.стоимость), 0)
        FROM ПОЕЗДКИ П
        JOIN ТАКСОПАРКИ Т ON Т.код = П.таксопарк
        WHERE Т.название = p_company_name
    );
END;
$$ LANGUAGE PLpgSQL;

-- Функция 2.2: Табличная функция - выручка по таксопаркам и сезонам
DROP FUNCTION IF EXISTS revenue_by_company_and_season();

CREATE OR REPLACE FUNCTION revenue_by_company_and_season()
RETURNS TABLE(
    таксопарк VARCHAR,
    сезон VARCHAR,
    выручка NUMERIC(12,2),
    количество_поездок BIGINT,
    порядок_сезона INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        Т.название,
        С.сезон,
        COALESCE(SUM(П.стоимость), 0)::NUMERIC(12,2),
        COUNT(П.код_поездки),
        MIN(С.порядок)
    FROM ТАКСОПАРКИ Т
    LEFT JOIN ПОЕЗДКИ П ON Т.код = П.таксопарк
    LEFT JOIN СЕЗОН С ON С.месяц = EXTRACT(MONTH FROM П.дата)
    GROUP BY Т.название, С.сезон
    ORDER BY Т.название, MIN(С.порядок);
END;
$$ LANGUAGE PLpgSQL;
