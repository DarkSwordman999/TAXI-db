CREATE TABLE ВОДИТЕЛИ (
    код SERIAL PRIMARY KEY,
    фамилия VARCHAR(50) NOT NULL,
    имя VARCHAR(50) NOT NULL,
    отчество VARCHAR(50),
    телефон VARCHAR(20) NOT NULL,
    стаж_лет INTEGER CHECK (стаж_лет >= 0),
    категория_прав VARCHAR(10),
    рейтинг DECIMAL(3,2) CHECK (рейтинг BETWEEN 0 AND 5)
);
