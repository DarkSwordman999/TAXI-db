CREATE TABLE ПОЕЗДКИ (
    код_поездки SERIAL PRIMARY KEY,
    дата TIMESTAMP NOT NULL,
    -- поездка не существует без машины, водителя и клиента;
    -- удалить их, пока на них ссылаются поездки, нельзя
    автомобиль INTEGER NOT NULL REFERENCES АВТОМОБИЛИ(код) ON DELETE RESTRICT,
    водитель INTEGER NOT NULL REFERENCES ВОДИТЕЛИ(код) ON DELETE RESTRICT,
    клиент INTEGER NOT NULL REFERENCES КЛИЕНТЫ(код) ON DELETE RESTRICT,
    расстояние_км DECIMAL(10,2) NOT NULL CHECK (расстояние_км > 0),
    время_мин INTEGER NOT NULL CHECK (время_мин > 0),
    стоимость DECIMAL(10,2) NOT NULL CHECK (стоимость >= 0)
);
