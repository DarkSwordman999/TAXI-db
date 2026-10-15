-- 77 районов Чикаго (community areas) с координатами центра
CREATE TABLE РАЙОНЫ (
    код INTEGER PRIMARY KEY CHECK (код BETWEEN 1 AND 77),
    название VARCHAR(50) NOT NULL UNIQUE,
    широта NUMERIC(9,6),
    долгота NUMERIC(9,6)
);
