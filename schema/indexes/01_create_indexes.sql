-- Индексы для ускорения связей, фильтров и аналитических запросов.
CREATE INDEX IF NOT EXISTS idx_rides_date ON ПОЕЗДКИ (дата);
CREATE INDEX IF NOT EXISTS idx_rides_car ON ПОЕЗДКИ (автомобиль);
CREATE INDEX IF NOT EXISTS idx_rides_driver ON ПОЕЗДКИ (водитель);
CREATE INDEX IF NOT EXISTS idx_rides_client ON ПОЕЗДКИ (клиент);
CREATE INDEX IF NOT EXISTS idx_cars_class ON АВТОМОБИЛИ (класс);
CREATE INDEX IF NOT EXISTS idx_drivers_rating ON ВОДИТЕЛИ (рейтинг);
CREATE INDEX IF NOT EXISTS idx_clients_phone ON КЛИЕНТЫ (телефон);
