-- Поездки такси Чикаго. Суммы — в долларах США, расстояние переведено из миль в км.
CREATE TABLE ПОЕЗДКИ (
    код_поездки SERIAL PRIMARY KEY,
    trip_id VARCHAR(16) NOT NULL UNIQUE,  -- ID поездки в данных города: защита от повторной загрузки
    дата TIMESTAMP NOT NULL,              -- начало поездки (город округляет до 15 минут)
    окончание TIMESTAMP,
    водитель INTEGER NOT NULL REFERENCES ВОДИТЕЛИ(код) ON DELETE RESTRICT,
    клиент INTEGER NOT NULL REFERENCES КЛИЕНТЫ(код) ON DELETE RESTRICT,
    таксопарк INTEGER NOT NULL REFERENCES ТАКСОПАРКИ(код) ON DELETE RESTRICT,
    -- район не указан, если поездка началась или закончилась за пределами города
    откуда INTEGER REFERENCES РАЙОНЫ(код),
    куда INTEGER REFERENCES РАЙОНЫ(код),
    расстояние_км NUMERIC(8,2) NOT NULL CHECK (расстояние_км > 0),
    время_мин INTEGER NOT NULL CHECK (время_мин > 0),
    стоимость NUMERIC(10,2) NOT NULL CHECK (стоимость > 0),          -- по счётчику
    чаевые NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (чаевые >= 0),
    сборы NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (сборы >= 0)        -- платные дороги и доплаты
);
