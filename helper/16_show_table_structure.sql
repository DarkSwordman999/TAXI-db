\echo '=== TABLE CARS ==='
SELECT column_name, data_type, character_maximum_length, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name ILIKE '%АВТОМОБИЛИ%'
ORDER BY ordinal_position;

\echo '=== TABLE DRIVERS ==='
SELECT column_name, data_type, character_maximum_length, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name ILIKE '%ВОДИТЕЛИ%'
ORDER BY ordinal_position;

\echo '=== TABLE RIDES ==='
SELECT column_name, data_type, character_maximum_length, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name ILIKE '%ПОЕЗДКИ%'
ORDER BY ordinal_position;

\echo '=== TABLE CLIENTS ==='
SELECT column_name, data_type, character_maximum_length, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name ILIKE '%КЛИЕНТЫ%'
ORDER BY ordinal_position;
