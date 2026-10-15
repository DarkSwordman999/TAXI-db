-- ============================================================
-- ФУНКЦИИ POSTGRESQL - TAXI
-- ЗАДАЧА 3: Сводная таблица (водители × способы оплаты клиентов)
-- ============================================================

DROP FUNCTION IF EXISTS get_driver_revenue_by_client(INT, VARCHAR);
DROP FUNCTION IF EXISTS display_pivot_table();

CREATE OR REPLACE FUNCTION get_driver_revenue_by_client(p_driver_code INT, p_client_type VARCHAR)
RETURNS NUMERIC(10,2) AS $$
BEGIN
    RETURN (
        SELECT COALESCE(SUM(П.стоимость), 0)::NUMERIC(10,2)
        FROM ПОЕЗДКИ П
        JOIN КЛИЕНТЫ К ON К.код = П.клиент
        WHERE П.водитель = p_driver_code
          AND К.тип = p_client_type
    );
END;
$$ LANGUAGE PLpgSQL;

-- 15 водителей с наибольшей выручкой: сколько они заработали с каждым типом клиентов
CREATE OR REPLACE FUNCTION display_pivot_table()
RETURNS TABLE(
    водитель TEXT,
    карта NUMERIC,
    наличные NUMERIC,
    приложение NUMERIC,
    предоплата NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'Водитель №' || В.код,
        get_driver_revenue_by_client(В.код, 'Credit Card')::NUMERIC,
        get_driver_revenue_by_client(В.код, 'Cash')::NUMERIC,
        get_driver_revenue_by_client(В.код, 'Mobile')::NUMERIC,
        get_driver_revenue_by_client(В.код, 'Prcard')::NUMERIC
    FROM ВОДИТЕЛИ В
    ORDER BY get_driver_revenue(В.код) DESC
    LIMIT 15;
END;
$$ LANGUAGE PLpgSQL;
