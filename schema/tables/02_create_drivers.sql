CREATE TABLE ВОДИТЕЛИ (
    код SERIAL PRIMARY KEY,
    фамилия VARCHAR(50) NOT NULL,
    имя VARCHAR(50) NOT NULL,
    отчество VARCHAR(50),
    телефон VARCHAR(20) NOT NULL,
    стаж_лет INTEGER,
    категория_прав VARCHAR(10),
    рейтинг DECIMAL(3,2)
);
