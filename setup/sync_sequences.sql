-- Синхронизация SERIAL-последовательностей после вставок с явными кодами.
SELECT setval(pg_get_serial_sequence('АВТОМОБИЛИ', 'код'), COALESCE((SELECT MAX(код) FROM АВТОМОБИЛИ), 1), true);
SELECT setval(pg_get_serial_sequence('ВОДИТЕЛИ', 'код'), COALESCE((SELECT MAX(код) FROM ВОДИТЕЛИ), 1), true);
SELECT setval(pg_get_serial_sequence('КЛИЕНТЫ', 'код'), COALESCE((SELECT MAX(код) FROM КЛИЕНТЫ), 1), true);
SELECT setval(pg_get_serial_sequence('ТАРИФЫ', 'код'), COALESCE((SELECT MAX(код) FROM ТАРИФЫ), 1), true);
SELECT setval(pg_get_serial_sequence('ПОЕЗДКИ', 'код_поездки'), COALESCE((SELECT MAX(код_поездки) FROM ПОЕЗДКИ), 1), true);
