# База данных TAXI

## О проекте

Реляционная база данных для учёта работы службы такси. Проект выполнен в рамках курса по базам данных. Содержит полный цикл работы с БД: от создания таблиц до сложных аналитических запросов и функций.

## Технологии

- **PostgreSQL 16** - основная СУБД
- **Bash** - скрипты для автоматизации
- **Git** - контроль версий
- **Python** - отчёты и визуализация (psycopg2, matplotlib)

## Структура базы данных

### Таблицы

| Таблица | Описание | Количество записей |
|---------|----------|-------------------|
| АВТОМОБИЛИ | Марка, модель, класс, госномер | 30 |
| ВОДИТЕЛИ | ФИО, телефон, стаж, рейтинг | 32 |
| КЛИЕНТЫ | ФИО, телефон | 250 |
| ПОЕЗДКИ | Дата, стоимость, связи с авто/водителем/клиентом | 1060 |
| ТАРИФЫ | Цена за км и минуту по классам | 4 |
| СЕЗОН | Соответствие месяца сезону | 12 |

### Классы автомобилей

| Класс | Описание |
|-------|----------|
| эконом | Эконом-класс |
| комфорт | Комфорт-класс |
| бизнес | Бизнес-класс |

## Лабораторная работа №5-6

### Основные задачи

| Команда | Описание |
|---------|----------|
| `./h task1` | Выручка по сезонам |
| `./h task2` | Выручка по сезонам и классам авто |
| `./h task3` | Выручка по дням недели и водителям |
| `./h task4 N` | Выручка по водителям за день N |

### Просмотр данных

| Команда | Описание |
|---------|----------|
| `./h 01` | Все автомобили |
| `./h 02` | Все водители |
| `./h 03` | Клиенты (первые 10) |
| `./h 04` | Количество поездок |
| `./h 05` | Примеры поездок |

### Аналитика

| Команда | Описание |
|---------|----------|
| `./h 17` | Топ-10 авто по выручке |
| `./h 18` | Топ-10 водителей по выручке |
| `./h 19` | Выручка по месяцам |
| `./h 20` | Средний чек |
| `./h 21` | Поездки по часам |
| `./h 22` | Статистика по классам |
| `./h 25` | Выручка по дням недели |

### Запросы с параметрами

| Команда | Описание |
|---------|----------|
| `./h 31 класс` | Авто по классу |
| `./h 32 код` | Информация о водителе |
| `./h 34 сумма` | Поездки дороже суммы |
| `./h 40 код номер` | Обновить госномер авто |
| `./h 41 код телефон` | Обновить телефон водителя |
| `./h 43 марка модель класс` | Добавить авто |
| `./h 44 фамилия имя телефон` | Добавить водителя |

## Лабораторная работа №7 - Функции PostgreSQL

### Команды для работы с функциями

| Команда | Описание |
|---------|----------|
| `./h 200` | Создать все функции |
| `./h 201 порог` | Водители с выручкой выше порога |
| `./h 202` | Выручка по классам и сезонам |
| `./h 203` | Сводная таблица (водители × классы) |
| `./h 204` | Выполнить всё |

### Функции

| Функция | Тип | Описание |
|---------|-----|----------|
| `get_driver_revenue(INT)` | скалярная | Выручка водителя |
| `drivers_above_revenue(NUMERIC)` | табличная | Водители с выручкой выше порога |
| `revenue_by_class_and_season()` | табличная | Выручка по классам и сезонам |
| `display_pivot_table()` | табличная | Сводная таблица |

### Примеры запуска

```bash
# Создать функции
./h 200

# Водители с выручкой выше 10000 руб.
./h 201 10000

# Выручка по классам и сезонам
./h 202

# Сводная таблица
./h 203

# Выполнить всё
./h 204

#### Структура проекта
TAXI/
├── README.md
├── control
│   ├── deletes
│   ├── inserts
│   │   ├── add_control_rides.sql
│   │   └── add_expensive_rides.sql
│   └── updates
├── data
│   ├── cars
│   │   └── 01_insert_cars.sql
│   ├── clients
│   │   └── 01_insert_clients.sql
│   ├── drivers
│   │   └── 01_insert_drivers.sql
│   ├── insert_200_clients.sql
│   ├── insert_200_clients_fixed.sql
│   ├── season
│   │   └── 01_insert_season.sql
│   └── tariffs
│       └── 01_insert_tariffs.sql
├── functions
│   └── random_date
│       └── 01_create_function.sql
├── generation
│   └── generate_1000_rides.sql
├── h
├── h1
├── helper
│   ├── 01_show_all_cars.sql
│   ├── 02_show_all_drivers.sql
│   ├── 03_show_all_clients.sql
│   ├── 04_show_rides_count.sql
│   ├── 05_show_rides_sample.sql
│   ├── 06_demo_inner_join.sql
│   ├── 07_demo_left_join.sql
│   ├── 08_demo_cross_join.sql
│   ├── 09_demo_update_before.sql
│   ├── 10_demo_update_after.sql
│   ├── 11_demo_delete_before.sql
│   ├── 12_demo_delete_after.sql
│   ├── 13_demo_insert_before.sql
│   ├── 14_demo_insert_after.sql
│   ├── 15_demo_with_param.sql
│   ├── 16_show_table_structure.sql
│   ├── 17_top_10_cars_by_revenue.sql
│   ├── 18_top_10_drivers_by_revenue.sql
│   ├── 19_revenue_by_month.sql
│   ├── 20_average_receipt.sql
│   ├── 21_rides_by_hour.sql
│   ├── 22_quick_update.sql
│   ├── 23_quick_delete.sql
│   ├── 24_search_car.sql
│   ├── 25_stats_by_class.sql
│   ├── 60_before_update.sql
│   ├── 61_do_update.sql
│   ├── 62_after_update.sql
│   ├── 63_before_delete.sql
│   ├── 64_do_delete.sql
│   └── 65_after_delete.sql
├── queries
│   ├── delete
│   │   ├── 01_delete_driver.sql
│   │   └── 02_delete_short_rides.sql
│   ├── insert
│   │   └── 01_insert_car.sql
│   ├── join
│   ├── lab7
│   │   ├── 01_create_functions_task1.sql
│   │   ├── 02_create_functions_task2.sql
│   │   ├── 03_create_functions_task3_fixed.sql
│   │   └── 04_run_lab7.sql
│   ├── select
│   ├── subqueries
│   │   ├── 01_price_deviation.sql
│   │   ├── 02_car_rating.sql
│   │   ├── 03_rides_above_avg.sql
│   │   ├── 04_class_stats.sql
│   │   ├── 05_top_drivers_lateral.sql
│   │   ├── 06_rides_above_avg_param.sql
│   │   ├── 07_good_drivers_exists.sql
│   │   └── 08_best_drivers_all.sql
│   ├── tasks
│   │   ├── 01_revenue_by_season.sql
│   │   ├── 02_revenue_by_season_and_class.sql
│   │   ├── 03_revenue_by_day_and_driver.sql
│   │   └── 04_revenue_by_driver_for_day.sql
│   ├── update
│   │   ├── 01_update_car_number.sql
│   │   ├── 02_update_driver_rating.sql
│   │   └── 03_update_in.sql
│   └── views
│       ├── 01_create_rides_view.sql
│       ├── 02_create_rides_tech.sql
│       └── 03_check_views.sql
├── s
├── schema
│   └── tables
│       ├── 01_create_cars.sql
│       ├── 02_create_drivers.sql
│       ├── 03_create_clients.sql
│       ├── 04_create_tariffs.sql
│       ├── 05_create_rides.sql
│       └── 06_create_season.sql
└── statistics
    ├── counts
    ├── lists
    └── samples
