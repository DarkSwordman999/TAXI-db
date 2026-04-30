CREATE TABLE ТАРИФЫ (
    код SERIAL PRIMARY KEY,
    класс VARCHAR(20) NOT NULL UNIQUE,
    цена_за_км DECIMAL(10,2) NOT NULL,
    цена_за_час DECIMAL(10,2) NOT NULL,
    минимальная_стоимость DECIMAL(10,2) NOT NULL
);
