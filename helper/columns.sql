-- Структура всех таблиц базы
SELECT table_name AS таблица, column_name AS колонка, data_type AS тип,
       character_maximum_length AS длина, is_nullable AS null_допустим, column_default AS по_умолчанию
FROM information_schema.columns 
WHERE table_schema = 'public'
  AND table_name IN ('ТАКСОПАРКИ', 'ВОДИТЕЛИ', 'ОПЛАТА', 'РАЙОНЫ', 'ПОЕЗДКИ', 'СЕЗОН')
ORDER BY table_name, ordinal_position;
