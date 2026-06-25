CREATE TABLE ПОЕЗДКИ (
    код_поездки SERIAL PRIMARY KEY,
    дата TIMESTAMP NOT NULL,
    автомобиль INTEGER REFERENCES АВТОМОБИЛИ(код),
    водитель INTEGER REFERENCES ВОДИТЕЛИ(код),
    клиент INTEGER REFERENCES КЛИЕНТЫ(код),
    расстояние_км DECIMAL(10,2) NOT NULL CHECK (расстояние_км > 0),
    время_мин INTEGER NOT NULL CHECK (время_мин > 0),
    стоимость DECIMAL(10,2) NOT NULL CHECK (стоимость >= 0)
);
