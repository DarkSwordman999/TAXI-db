CREATE TABLE АВТОМОБИЛИ (
    код SERIAL PRIMARY KEY,
    гос_номер VARCHAR(10) NOT NULL UNIQUE,
    марка VARCHAR(50) NOT NULL,
    модель VARCHAR(50) NOT NULL,
    год_выпуска INTEGER,
    цвет VARCHAR(30),
    класс VARCHAR(20)
);
