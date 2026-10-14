CREATE TABLE АВТОМОБИЛИ (
    код SERIAL PRIMARY KEY,
    гос_номер VARCHAR(10) NOT NULL UNIQUE,
    марка VARCHAR(50) NOT NULL,
    модель VARCHAR(50) NOT NULL,
    год_выпуска INTEGER CHECK (год_выпуска BETWEEN 1990 AND 2035),
    цвет VARCHAR(30),
    -- допустимые классы задаёт таблица ТАРИФЫ: внешний ключ добавляется
    -- в 04_create_tariffs.sql, после создания ТАРИФЫ
    класс VARCHAR(20)
);
