"""Аналитика: рейтинги, отчёты, проверки данных и графики."""

from tkinter import messagebox

from . import sql


class AnalyticsMixin:

    def _report(self, query, title, status=None, with_limit=False):
        params = [self.get_limit()] if with_limit else None
        self.execute_and_display(query, params, title=title, status=status or title)

    # ------------------------- рейтинги и отчёты -------------------------
    def top_drivers(self):
        self._report(sql.TOP_DRIVERS, "Топ водителей", with_limit=True)

    def top_clients(self):
        self._report(sql.TOP_CLIENTS, "Типы клиентов (способы оплаты)", "Типы клиентов", with_limit=True)

    def revenue_by_company(self):
        self._report(sql.REVENUE_BY_COMPANY, "Доход по таксопаркам")

    def company_stats(self):
        self._report(sql.COMPANY_STATS, "Статистика таксопарков", with_limit=True)

    def season_stats(self):
        self._report(sql.SEASON_STATS, "Статистика по сезонам", "Сезоны")

    def fare_distribution(self):
        self._report(sql.FARE_DISTRIBUTION, "Распределение стоимости поездок", "Распределение стоимости")

    def average_ride_report(self):
        self._report(sql.AVERAGE_RIDE, "Средние показатели поездок", "Средняя поездка")

    def weekday_report(self):
        self._report(sql.WEEKDAY_REPORT, "Аналитика по дням недели", "Дни недели")

    def hour_report(self):
        self._report(sql.HOUR_REPORT, "Аналитика по часам суток", "Часы суток")

    def period_report(self):
        data = self.ask_fields("Отчёт за период", [
            ("date_from", "Дата начала YYYY-MM-DD", "2026-01-01"),
            ("date_to", "Дата конца YYYY-MM-DD", "2026-12-31"),
        ])
        if data:
            self.execute_and_display(sql.PERIOD_REPORT, [data["date_from"], data["date_to"]],
                                     title="Отчёт по датам за период", status="Отчёт за период")

    # ------------------------- контроль -------------------------
    def expensive_rides(self):
        self._report(sql.EXPENSIVE_RIDES, "Самые дорогие поездки", "Дорогие поездки", with_limit=True)

    def long_rides(self):
        self._report(sql.LONG_RIDES, "Самые длинные поездки", "Длинные поездки", with_limit=True)

    def inactive_drivers(self):
        self._report(sql.INACTIVE_DRIVERS, "Водители без поездок", "Неактивные водители")

    def inactive_companies(self):
        self._report(sql.INACTIVE_COMPANIES, "Таксопарки без поездок")

    def data_quality_check(self):
        self._report(sql.DATA_QUALITY, "Проверка качества данных", "Проверка связей")

    # ------------------------- графики -------------------------
    def _chart_rows(self, query):
        rows, _ = self.fetch_rows(query)
        if not rows and self.conn:
            messagebox.showinfo("Нет данных", "Нет данных для графика")
        return rows

    def chart_monthly_revenue(self):
        rows = self._chart_rows(sql.CHART_MONTHLY)
        if rows:
            self.open_line_chart([r[0] for r in rows], [float(r[1]) for r in rows],
                                 "Динамика выручки по месяцам", "Месяц", "Выручка, $")

    def chart_payment_pie(self):
        rows = self._chart_rows(sql.CHART_PAYMENT)
        if rows:
            self.open_pie_chart([r[0] for r in rows], [int(r[1]) for r in rows],
                                "Доля поездок по способам оплаты")

    def chart_driver_revenue(self):
        rows = self._chart_rows(sql.CHART_DRIVERS)
        if rows:
            self.open_bar_chart([r[0] for r in rows], [float(r[1] or 0) for r in rows],
                                "Топ-10 водителей по выручке", "Водитель", "Выручка, $")

    def chart_weekday_revenue(self):
        rows = self._chart_rows(sql.CHART_WEEKDAY)
        if rows:
            self.open_bar_chart([r[0] for r in rows], [float(r[1] or 0) for r in rows],
                                "Выручка по дням недели", "День недели", "Выручка, $")
