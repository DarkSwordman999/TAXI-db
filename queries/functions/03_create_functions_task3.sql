-- ============================================================
-- ФУНКЦИИ POSTGRESQL - TAXI
-- ЗАДАЧА 3: Сводная таблица (водители × способы оплаты)
-- ============================================================

DROP FUNCTION IF EXISTS display_pivot_table();
DROP FUNCTION IF EXISTS get_driver_revenue_by_client(INT, VARCHAR);
DROP FUNCTION IF EXISTS get_driver_revenue_by_payment(INT, VARCHAR);

-- выручка водителя с одним способом оплаты; p_payment_type — значение ОПЛАТА.тип (Cash, Credit Card, …)
CREATE OR REPLACE FUNCTION get_driver_revenue_by_payment(p_driver_code INT, p_payment_type VARCHAR)
RETURNS NUMERIC(10,2) AS $$
BEGIN
    RETURN (
        SELECT COALESCE(SUM(П.стоимость), 0)::NUMERIC(10,2)
        FROM ПОЕЗДКИ П
        JOIN ОПЛАТА О ON О.код = П.оплата
        WHERE П.водитель = p_driver_code
          AND О.тип = p_payment_type
    );
END;
$$ LANGUAGE PLpgSQL;

-- прежнее имя (до версии 2.0, когда таблица называлась КЛИЕНТЫ): оставлено, чтобы старые запросы работали
CREATE OR REPLACE FUNCTION get_driver_revenue_by_client(p_driver_code INT, p_client_type VARCHAR)
RETURNS NUMERIC(10,2) AS $$
    SELECT get_driver_revenue_by_payment(p_driver_code, p_client_type);
$$ LANGUAGE SQL;

-- 15 водителей с наибольшей выручкой: сколько они заработали каждым способом оплаты
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
        get_driver_revenue_by_payment(В.код, 'Credit Card')::NUMERIC,
        get_driver_revenue_by_payment(В.код, 'Cash')::NUMERIC,
        get_driver_revenue_by_payment(В.код, 'Mobile')::NUMERIC,
        get_driver_revenue_by_payment(В.код, 'Prcard')::NUMERIC
    FROM ВОДИТЕЛИ В
    ORDER BY get_driver_revenue(В.код) DESC
    LIMIT 15;
END;
$$ LANGUAGE PLpgSQL;
