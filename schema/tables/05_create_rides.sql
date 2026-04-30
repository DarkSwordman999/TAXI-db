CREATE TABLE ПОЕЗДКИ (
    код_поездки SERIAL PRIMARY KEY,
    дата TIMESTAMP NOT NULL,
    автомобиль INTEGER REFERENCES АВТОМОБИЛИ(код),
    водитель INTEGER REFERENCES ВОДИТЕЛИ(код),
    клиент INTEGER REFERENCES КЛИЕНТЫ(код),
    расстояние_км DECIMAL(10,2) NOT NULL,
    время_мин INTEGER NOT NULL,
    стоимость DECIMAL(10,2) NOT NULL
);
