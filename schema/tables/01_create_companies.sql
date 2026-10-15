-- Таксопарки Чикаго (поле company открытых данных города)
CREATE TABLE ТАКСОПАРКИ (
    код SERIAL PRIMARY KEY,
    название VARCHAR(100) NOT NULL
);

-- одно и то же название в разном регистре — один таксопарк
CREATE UNIQUE INDEX uq_companies_name ON ТАКСОПАРКИ (lower(название));
