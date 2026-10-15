-- Индексы для ускорения связей, фильтров и аналитических запросов.
CREATE INDEX IF NOT EXISTS idx_rides_date ON ПОЕЗДКИ (дата);
CREATE INDEX IF NOT EXISTS idx_rides_driver ON ПОЕЗДКИ (водитель);
CREATE INDEX IF NOT EXISTS idx_rides_client ON ПОЕЗДКИ (клиент);
CREATE INDEX IF NOT EXISTS idx_rides_company ON ПОЕЗДКИ (таксопарк);
CREATE INDEX IF NOT EXISTS idx_rides_from ON ПОЕЗДКИ (откуда);
CREATE INDEX IF NOT EXISTS idx_rides_to ON ПОЕЗДКИ (куда);
