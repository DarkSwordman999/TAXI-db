"""SQL-запросы GUI. Представления и функции GUI не создаёт: они берутся из queries/."""

TABLES = ["ТАКСОПАРКИ", "ВОДИТЕЛИ", "КЛИЕНТЫ", "РАЙОНЫ", "ПОЕЗДКИ", "СЕЗОН"]

# Проектные файлы, которые GUI выполняет вместо собственных CREATE VIEW / FUNCTION
VIEW_FILES = ["queries/views/01_create_rides_view.sql", "queries/views/02_create_rides_tech.sql"]
FUNCTION_FILES = [
    "queries/functions/01_create_functions_task1.sql",
    "queries/functions/02_create_functions_task2.sql",
    "queries/functions/03_create_functions_task3.sql",
]
PROJECT_VIEWS = ["v_rides_user", "v_rides_tech"]

# ------------------------- служебные -------------------------
PG_TRGM_EXISTS = "SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm'"
MISSING_VIEWS = "SELECT v FROM unnest(%s::text[]) AS v WHERE to_regclass(v) IS NULL"
CHECK_VIEWS = """
    SELECT 'v_rides_user' AS представление, COUNT(*) AS строк FROM v_rides_user
    UNION ALL SELECT 'v_rides_tech', COUNT(*) FROM v_rides_tech
"""

AUTOCOMPLETE = {
    "таксопарк": "SELECT название FROM ТАКСОПАРКИ ORDER BY название",
    "тип клиента": "SELECT описание FROM КЛИЕНТЫ ORDER BY описание",
    "район": "SELECT название FROM РАЙОНЫ ORDER BY название",
}

# ------------------------- просмотр -------------------------
DB_STATS = """
    SELECT 'ТАКСОПАРКИ' AS таблица, COUNT(*) AS записей FROM ТАКСОПАРКИ
    UNION ALL SELECT 'ВОДИТЕЛИ', COUNT(*) FROM ВОДИТЕЛИ
    UNION ALL SELECT 'КЛИЕНТЫ', COUNT(*) FROM КЛИЕНТЫ
    UNION ALL SELECT 'РАЙОНЫ', COUNT(*) FROM РАЙОНЫ
    UNION ALL SELECT 'ПОЕЗДКИ', COUNT(*) FROM ПОЕЗДКИ
    UNION ALL SELECT 'СЕЗОН', COUNT(*) FROM СЕЗОН
    ORDER BY таблица
"""

STRUCTURE = """
    SELECT table_name AS таблица, column_name AS столбец, data_type AS тип
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name IN ('ТАКСОПАРКИ','ВОДИТЕЛИ','КЛИЕНТЫ','РАЙОНЫ','ПОЕЗДКИ','СЕЗОН')
    ORDER BY table_name, ordinal_position
"""

# Поездки с расшифровкой кодов. Псевдонимы p, v, t, k, ro, rk используют фильтры поездок,
# поэтому здесь не v_rides_user: в нём нет taxi_id и типа оплаты для поиска.
# {cond} — условия фильтра (только с параметрами %s), последний параметр — LIMIT.
RIDES_FILTERED = """
    SELECT p.код_поездки, p.дата,
           'Водитель №' || v.код AS водитель,
           t.название AS таксопарк,
           k.описание AS оплата,
           ro.название AS откуда, rk.название AS куда,
           p.расстояние_км, p.время_мин, p.стоимость, p.чаевые
    FROM ПОЕЗДКИ p
    JOIN ВОДИТЕЛИ v ON v.код = p.водитель
    JOIN КЛИЕНТЫ k ON k.код = p.клиент
    JOIN ТАКСОПАРКИ t ON t.код = p.таксопарк
    LEFT JOIN РАЙОНЫ ro ON ro.код = p.откуда
    LEFT JOIN РАЙОНЫ rk ON rk.код = p.куда
    WHERE 1=1 {cond}
    ORDER BY p.дата DESC
    LIMIT %s
"""

TRIGRAM_SEARCH = """
    WITH q AS (
        SELECT %s::text AS term, %s::text AS like_term, %s::float AS threshold
    )
    SELECT * FROM (
        SELECT 'таксопарк' AS тип, t.код::text AS код, t.название AS найдено,
               ROUND(similarity(LOWER(t.название), q.term)::numeric, 3) AS схожесть
        FROM ТАКСОПАРКИ t CROSS JOIN q
        WHERE similarity(LOWER(t.название), q.term) >= q.threshold
           OR t.название ILIKE q.like_term

        UNION ALL

        SELECT 'район', r.код::text, r.название,
               ROUND(similarity(LOWER(r.название), q.term)::numeric, 3)
        FROM РАЙОНЫ r CROSS JOIN q
        WHERE similarity(LOWER(r.название), q.term) >= q.threshold
           OR r.название ILIKE q.like_term

        UNION ALL

        SELECT 'тип клиента', k.код::text, k.описание || ' (' || k.тип || ')',
               ROUND(GREATEST(similarity(LOWER(k.описание), q.term),
                              similarity(LOWER(k.тип), q.term))::numeric, 3)
        FROM КЛИЕНТЫ k CROSS JOIN q
        WHERE GREATEST(similarity(LOWER(k.описание), q.term),
                       similarity(LOWER(k.тип), q.term)) >= q.threshold
           OR k.описание ILIKE q.like_term
           OR k.тип ILIKE q.like_term

        UNION ALL

        SELECT 'водитель', v.код::text, 'Водитель №' || v.код || ' (' || v.taxi_id || ')',
               ROUND(similarity(LOWER(v.taxi_id), q.term)::numeric, 3)
        FROM ВОДИТЕЛИ v CROSS JOIN q
        WHERE v.taxi_id ILIKE q.like_term
           OR v.код::text = q.term
    ) found
    ORDER BY схожесть DESC, тип, найдено
    LIMIT %s
"""

DASHBOARD_VALUES = [
    ("Всего поездок", "SELECT COUNT(*) FROM ПОЕЗДКИ"),
    ("Общая выручка", "SELECT ROUND(COALESCE(SUM(стоимость),0), 2) FROM ПОЕЗДКИ"),
    ("Средний чек", "SELECT ROUND(COALESCE(AVG(стоимость),0), 2) FROM ПОЕЗДКИ"),
    ("Средняя дистанция", "SELECT ROUND(COALESCE(AVG(расстояние_км),0), 2) FROM ПОЕЗДКИ"),
    ("Период данных", "SELECT MIN(дата)::date || ' — ' || MAX(дата)::date FROM ПОЕЗДКИ"),
    ("Водителей (такси)", "SELECT COUNT(*) FROM ВОДИТЕЛИ"),
    ("Таксопарков", "SELECT COUNT(*) FROM ТАКСОПАРКИ"),
    ("Типов клиентов", "SELECT COUNT(*) FROM КЛИЕНТЫ"),
]

DASHBOARD_TABLES = [
    ("Топ-3 таксопарка по выручке", """
        SELECT t.название AS таксопарк, COUNT(*) AS поездок, ROUND(SUM(p.стоимость),2) AS выручка
        FROM ПОЕЗДКИ p JOIN ТАКСОПАРКИ t ON t.код = p.таксопарк
        GROUP BY t.название
        ORDER BY выручка DESC
        LIMIT 3
    """),
    ("Топ-5 водителей по выручке", """
        SELECT 'Водитель №' || v.код AS водитель,
               COUNT(p.код_поездки) AS поездок,
               ROUND(COALESCE(SUM(p.стоимость),0),2) AS выручка
        FROM ВОДИТЕЛИ v JOIN ПОЕЗДКИ p ON p.водитель = v.код
        GROUP BY v.код
        ORDER BY выручка DESC
        LIMIT 5
    """),
    ("Последние 5 поездок", """
        SELECT код_поездки, дата, таксопарк, водитель, стоимость
        FROM v_rides_user
        ORDER BY дата DESC
        LIMIT 5
    """),
]

# ------------------------- рейтинги и аналитика -------------------------
TOP_DRIVERS = """
    SELECT v.код, 'Водитель №' || v.код AS водитель, v.taxi_id,
           COUNT(p.код_поездки) AS поездок,
           ROUND(COALESCE(SUM(p.стоимость),0), 2) AS выручка,
           ROUND(COALESCE(AVG(p.стоимость),0), 2) AS средний_чек,
           ROUND(COALESCE(SUM(p.чаевые),0), 2) AS чаевые
    FROM ВОДИТЕЛИ v
    LEFT JOIN ПОЕЗДКИ p ON p.водитель = v.код
    GROUP BY v.код
    ORDER BY выручка DESC, поездок DESC
    LIMIT %s
"""

TOP_CLIENTS = """
    SELECT k.код, k.тип, k.описание,
           COUNT(p.код_поездки) AS поездок,
           ROUND(COALESCE(SUM(p.стоимость),0), 2) AS сумма,
           ROUND(COALESCE(AVG(p.стоимость),0), 2) AS средний_чек,
           ROUND(COALESCE(AVG(p.чаевые),0), 2) AS средние_чаевые
    FROM КЛИЕНТЫ k
    LEFT JOIN ПОЕЗДКИ p ON p.клиент = k.код
    GROUP BY k.код
    ORDER BY сумма DESC, поездок DESC
    LIMIT %s
"""

REVENUE_BY_COMPANY = """
    SELECT t.название AS таксопарк,
           COUNT(p.код_поездки) AS поездок,
           ROUND(SUM(p.стоимость), 2) AS выручка,
           ROUND(AVG(p.стоимость), 2) AS средний_чек,
           ROUND(AVG(p.расстояние_км), 2) AS среднее_расстояние,
           ROUND(AVG(p.время_мин), 2) AS среднее_время
    FROM ПОЕЗДКИ p
    JOIN ТАКСОПАРКИ t ON t.код = p.таксопарк
    GROUP BY t.название
    ORDER BY выручка DESC
"""

COMPANY_STATS = """
    SELECT t.код, t.название,
           COUNT(DISTINCT p.водитель) AS водителей,
           COUNT(p.код_поездки) AS поездок,
           ROUND(COALESCE(SUM(p.стоимость),0), 2) AS выручка,
           ROUND(COALESCE(AVG(p.расстояние_км),0), 2) AS средний_км
    FROM ТАКСОПАРКИ t
    LEFT JOIN ПОЕЗДКИ p ON p.таксопарк = t.код
    GROUP BY t.код, t.название
    ORDER BY выручка DESC, поездок DESC
    LIMIT %s
"""

SEASON_STATS = """
    SELECT s.сезон,
           COUNT(p.код_поездки) AS поездок,
           ROUND(SUM(p.стоимость), 2) AS выручка,
           ROUND(AVG(p.стоимость), 2) AS средний_чек,
           ROUND(AVG(p.расстояние_км), 2) AS средний_км
    FROM ПОЕЗДКИ p
    JOIN СЕЗОН s ON s.месяц = EXTRACT(MONTH FROM p.дата)::int
    GROUP BY s.сезон, s.порядок
    ORDER BY s.порядок
"""

FARE_DISTRIBUTION = """
    SELECT
        CASE
            WHEN стоимость < 10 THEN 'до $10'
            WHEN стоимость < 25 THEN '$10-24.99'
            WHEN стоимость < 50 THEN '$25-49.99'
            ELSE '$50+'
        END AS диапазон,
        COUNT(*) AS поездок,
        ROUND(AVG(стоимость), 2) AS средняя_стоимость
    FROM ПОЕЗДКИ
    GROUP BY диапазон
    ORDER BY MIN(стоимость)
"""

AVERAGE_RIDE = """
    SELECT COUNT(*) AS поездок,
           ROUND(AVG(расстояние_км), 2) AS среднее_расстояние_км,
           ROUND(AVG(время_мин), 2) AS среднее_время_мин,
           ROUND(AVG(стоимость), 2) AS средняя_стоимость,
           ROUND(SUM(стоимость), 2) AS общая_выручка
    FROM ПОЕЗДКИ
"""

PERIOD_REPORT = """
    SELECT DATE(p.дата) AS дата,
           COUNT(*) AS поездок,
           ROUND(SUM(p.стоимость),2) AS выручка,
           ROUND(AVG(p.стоимость),2) AS средний_чек,
           ROUND(SUM(p.расстояние_км),2) AS км_всего,
           ROUND(AVG(p.расстояние_км),2) AS средняя_дистанция
    FROM ПОЕЗДКИ p
    WHERE DATE(p.дата) BETWEEN %s::date AND %s::date
    GROUP BY DATE(p.дата)
    ORDER BY дата
"""

WEEKDAY_REPORT = """
    SELECT CASE EXTRACT(ISODOW FROM p.дата)
            WHEN 1 THEN 'Понедельник'
            WHEN 2 THEN 'Вторник'
            WHEN 3 THEN 'Среда'
            WHEN 4 THEN 'Четверг'
            WHEN 5 THEN 'Пятница'
            WHEN 6 THEN 'Суббота'
            WHEN 7 THEN 'Воскресенье'
           END AS день_недели,
           COUNT(*) AS поездок,
           ROUND(SUM(p.стоимость),2) AS выручка,
           ROUND(AVG(p.стоимость),2) AS средний_чек
    FROM ПОЕЗДКИ p
    GROUP BY EXTRACT(ISODOW FROM p.дата)
    ORDER BY EXTRACT(ISODOW FROM p.дата)
"""

HOUR_REPORT = """
    SELECT EXTRACT(HOUR FROM p.дата)::int AS час,
           COUNT(*) AS поездок,
           ROUND(SUM(p.стоимость),2) AS выручка,
           ROUND(AVG(p.стоимость),2) AS средний_чек
    FROM ПОЕЗДКИ p
    GROUP BY EXTRACT(HOUR FROM p.дата)
    ORDER BY час
"""

# ------------------------- контроль -------------------------
EXPENSIVE_RIDES = "SELECT * FROM v_rides_user ORDER BY стоимость DESC LIMIT %s"
LONG_RIDES = "SELECT * FROM v_rides_user ORDER BY расстояние_км DESC LIMIT %s"

INACTIVE_DRIVERS = """
    SELECT v.код, 'Водитель №' || v.код AS водитель, v.taxi_id
    FROM ВОДИТЕЛИ v
    LEFT JOIN ПОЕЗДКИ p ON p.водитель = v.код
    WHERE p.код_поездки IS NULL
    ORDER BY v.код
"""

INACTIVE_COMPANIES = """
    SELECT t.код, t.название
    FROM ТАКСОПАРКИ t
    LEFT JOIN ПОЕЗДКИ p ON p.таксопарк = t.код
    WHERE p.код_поездки IS NULL
    ORDER BY t.код
"""

DATA_QUALITY = """
    SELECT 'Поездки без района посадки (за городом)' AS проверка, COUNT(*) AS найдено FROM ПОЕЗДКИ WHERE откуда IS NULL
    UNION ALL SELECT 'Поездки без района высадки (за городом)', COUNT(*) FROM ПОЕЗДКИ WHERE куда IS NULL
    UNION ALL SELECT 'Окончание раньше начала', COUNT(*) FROM ПОЕЗДКИ WHERE окончание < дата
    UNION ALL SELECT 'Чаевые больше стоимости', COUNT(*) FROM ПОЕЗДКИ WHERE чаевые > стоимость
    UNION ALL SELECT 'Скорость выше 120 км/ч', COUNT(*) FROM ПОЕЗДКИ WHERE расстояние_км / (время_мин / 60.0) > 120
    UNION ALL SELECT 'Водители без поездок', COUNT(*) FROM ВОДИТЕЛИ v WHERE NOT EXISTS (SELECT 1 FROM ПОЕЗДКИ p WHERE p.водитель = v.код)
    UNION ALL SELECT 'Районы без поездок', COUNT(*) FROM РАЙОНЫ r WHERE NOT EXISTS (SELECT 1 FROM ПОЕЗДКИ p WHERE p.откуда = r.код OR p.куда = r.код)
"""

# ------------------------- графики -------------------------
CHART_MONTHLY = """
    SELECT DATE_TRUNC('month', дата)::date AS месяц, SUM(стоимость) AS выручка
    FROM ПОЕЗДКИ
    GROUP BY DATE_TRUNC('month', дата)
    ORDER BY месяц
"""

CHART_PAYMENT = """
    SELECT k.описание, COUNT(*) AS поездок
    FROM ПОЕЗДКИ p
    JOIN КЛИЕНТЫ k ON k.код = p.клиент
    GROUP BY k.описание
    ORDER BY поездок DESC
"""

CHART_DRIVERS = """
    SELECT 'Водитель №' || v.код AS водитель, ROUND(SUM(p.стоимость),2) AS выручка
    FROM ВОДИТЕЛИ v
    JOIN ПОЕЗДКИ p ON p.водитель = v.код
    GROUP BY v.код
    ORDER BY выручка DESC
    LIMIT 10
"""

CHART_WEEKDAY = """
    SELECT CASE EXTRACT(ISODOW FROM дата)
            WHEN 1 THEN 'Пн' WHEN 2 THEN 'Вт' WHEN 3 THEN 'Ср' WHEN 4 THEN 'Чт'
            WHEN 5 THEN 'Пт' WHEN 6 THEN 'Сб' WHEN 7 THEN 'Вс'
           END AS день,
           ROUND(SUM(стоимость),2) AS выручка
    FROM ПОЕЗДКИ
    GROUP BY EXTRACT(ISODOW FROM дата)
    ORDER BY EXTRACT(ISODOW FROM дата)
"""

# ------------------------- функции из queries/functions -------------------------
# get_driver_revenue, get_company_avg_revenue, get_driver_revenue_by_client создаёт
# ./help.sh rebuild (или кнопка «Создать функции»). Оценка стоимости — обычный запрос:
# средняя цена километра и минуты в таксопарке по его реальным поездкам.
FUNCTIONS_DEMO = """
    SELECT get_driver_revenue(%(driver)s::int) AS выручка_водителя,
           ROUND(get_company_avg_revenue(%(company)s), 2) AS средний_чек_таксопарка,
           get_driver_revenue_by_client(%(driver)s::int, %(client)s) AS выручка_водителя_по_оплате,
           (SELECT ROUND(AVG(p.стоимость / p.расстояние_км) * %(km)s::numeric * 0.5
                       + AVG(p.стоимость / p.время_мин) * %(minutes)s::int * 0.5, 2)
            FROM ПОЕЗДКИ p
            JOIN ТАКСОПАРКИ t ON t.код = p.таксопарк
            WHERE t.название = %(company)s AND p.расстояние_км >= 1) AS оценка_стоимости
"""

# ------------------------- правка записей -------------------------
ADD_COMPANY = "INSERT INTO ТАКСОПАРКИ (название) VALUES (%s)"
ADD_DRIVER = "INSERT INTO ВОДИТЕЛИ (taxi_id) VALUES (%s)"
ADD_CLIENT = "INSERT INTO КЛИЕНТЫ (тип, описание) VALUES (%s, %s)"
# введённые вручную поездки получают trip_id с префиксом manual
ADD_RIDE = """
    INSERT INTO ПОЕЗДКИ (trip_id, дата, водитель, клиент, таксопарк, откуда, куда,
                         расстояние_км, время_мин, стоимость, чаевые)
    VALUES ('manual' || LPAD((SELECT COUNT(*) + 1 FROM ПОЕЗДКИ)::text, 10, '0'), NOW(),
            %s::int, %s::int, %s::int, NULLIF(%s,'')::int, NULLIF(%s,'')::int,
            %s::numeric, %s::int, %s::numeric, %s::numeric)
"""

RENAME_COMPANY = "UPDATE ТАКСОПАРКИ SET название=%s WHERE код=%s::int"
UPDATE_CLIENT_DESC = "UPDATE КЛИЕНТЫ SET описание=%s WHERE код=%s::int"
UPDATE_RIDE_TIPS = "UPDATE ПОЕЗДКИ SET чаевые=%s::numeric WHERE код_поездки=%s::int"
UPDATE_RIDE_COMPANY = "UPDATE ПОЕЗДКИ SET таксопарк=%s::int WHERE код_поездки=%s::int"

DELETE_RIDE = "DELETE FROM ПОЕЗДКИ WHERE код_поездки=%s"
# справочник удаляется вместе с его поездками
DELETE_WITH_RIDES = {
    "client": ("DELETE FROM ПОЕЗДКИ WHERE клиент=%s; DELETE FROM КЛИЕНТЫ WHERE код=%s", "Удаление типа клиента"),
    "driver": ("DELETE FROM ПОЕЗДКИ WHERE водитель=%s; DELETE FROM ВОДИТЕЛИ WHERE код=%s", "Удаление водителя"),
    "company": ("DELETE FROM ПОЕЗДКИ WHERE таксопарк=%s; DELETE FROM ТАКСОПАРКИ WHERE код=%s", "Удаление таксопарка"),
}

RIDE_USER_VIEW = "SELECT * FROM v_rides_user WHERE код_поездки=%s::int"
RIDE_RAW = "SELECT * FROM ПОЕЗДКИ WHERE код_поездки=%s"

ARCHIVE_OLD_RIDES = """
    CREATE TABLE IF NOT EXISTS ПОЕЗДКИ_АРХИВ (LIKE ПОЕЗДКИ INCLUDING ALL);

    INSERT INTO ПОЕЗДКИ_АРХИВ
    SELECT * FROM ПОЕЗДКИ
    WHERE дата < CURRENT_DATE - make_interval(years => %s::int)
    ON CONFLICT (код_поездки) DO NOTHING;

    DELETE FROM ПОЕЗДКИ
    WHERE дата < CURRENT_DATE - make_interval(years => %s::int);
"""
