CREATE TABLE ТАРИФЫ (
    код SERIAL PRIMARY KEY,
    класс VARCHAR(20) NOT NULL UNIQUE,
    цена_за_км DECIMAL(10,2) NOT NULL CHECK (цена_за_км > 0),
    цена_за_час DECIMAL(10,2) NOT NULL CHECK (цена_за_час > 0),
    минимальная_стоимость DECIMAL(10,2) NOT NULL CHECK (минимальная_стоимость >= 0)
);
