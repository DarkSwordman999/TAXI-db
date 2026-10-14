CREATE TABLE СЕЗОН (
    месяц INTEGER PRIMARY KEY CHECK (месяц BETWEEN 1 AND 12),
    сезон VARCHAR(10) NOT NULL CHECK (сезон IN ('зима', 'весна', 'лето', 'осень')),
    порядок INTEGER NOT NULL CHECK (порядок BETWEEN 1 AND 4)
);
