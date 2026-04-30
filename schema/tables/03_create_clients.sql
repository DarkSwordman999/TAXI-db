CREATE TABLE КЛИЕНТЫ (
    код SERIAL PRIMARY KEY,
    фамилия VARCHAR(50),
    имя VARCHAR(50) NOT NULL,
    телефон VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(100),
    дата_регистрации DATE
);
