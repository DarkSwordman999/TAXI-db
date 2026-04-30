CREATE OR REPLACE FUNCTION random_date(start_date DATE, end_date DATE) 
RETURNS DATE AS $$
BEGIN
    RETURN start_date + (random() * (end_date - start_date))::INT;
END;
$$ LANGUAGE plpgsql;
