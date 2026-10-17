"""Правка записей: добавление, изменение, удаление, UPDATE/DELETE до и после, архивация."""

from tkinter import messagebox, simpledialog

from psycopg2 import sql as psql

from . import sql

# что ввести в окне выбора -> внутреннее имя
KINDS = {
    "company": "company", "таксопарк": "company",
    "driver": "driver", "водитель": "driver",
    "client": "client", "клиент": "client",
    "ride": "ride", "поездка": "ride",
}
PRIMARY_KEYS = {"ПОЕЗДКИ": "код_поездки", "СЕЗОН": "месяц"}


class EditingMixin:

    def _ask_kind(self, title, prompt):
        answer = simpledialog.askstring(title, prompt)
        if not answer:
            return None
        kind = KINDS.get(answer.lower().strip())
        if not kind:
            messagebox.showerror("Ошибка", "Введите: company, driver, client или ride")
        return kind

    def _change(self, query, params, title, status, refresh_names=False):
        self.execute_and_display(query, params, title=title, status=status, fetch=False)
        if refresh_names:
            self.load_autocomplete_data()

    # ------------------------- добавление -------------------------
    def add_record_window(self):
        kind = self._ask_kind("Добавление", "Что добавить? company / driver / client / ride")
        actions = {"company": self.add_company, "driver": self.add_driver,
                   "client": self.add_client, "ride": self.add_ride}
        if kind:
            actions[kind]()

    def add_company(self):
        data = self.ask_fields("Добавить таксопарк", [("name", "Название", "Новый таксопарк")])
        if data:
            self._change(sql.ADD_COMPANY, [data["name"]], "Добавление таксопарка", "Таксопарк добавлен", True)

    def add_driver(self):
        data = self.ask_fields("Добавить водителя", [("taxi_id", "taxi_id (до 16 символов)", "manual00000001")])
        if data:
            self._change(sql.ADD_DRIVER, [data["taxi_id"]], "Добавление водителя", "Водитель добавлен")

    def add_client(self):
        data = self.ask_fields("Добавить тип клиента", [
            ("type", "Тип (как в данных города)", "Voucher"),
            ("desc", "Описание", "Ваучер"),
        ])
        if data:
            self._change(sql.ADD_CLIENT, [data["type"], data["desc"]],
                         "Добавление типа клиента", "Тип клиента добавлен", True)

    def add_ride(self):
        fields = [
            ("driver", "Код водителя", "1"),
            ("client", "Код типа клиента", "1"),
            ("company", "Код таксопарка", "1"),
            ("from", "Код района посадки (1-77, можно пусто)", "32"),
            ("to", "Код района высадки (1-77, можно пусто)", "8"),
            ("km", "Расстояние км", "5"),
            ("min", "Время мин", "15"),
            ("cost", "Стоимость $", "15"),
            ("tips", "Чаевые $", "0"),
        ]
        data = self.ask_fields("Добавить поездку", fields)
        if data:
            self._change(sql.ADD_RIDE, [data[key] for key, _, _ in fields], "Добавление поездки", "Поездка добавлена")

    # ------------------------- изменение -------------------------
    def edit_record_window(self):
        actions = {
            "company_name": self.update_company_name,
            "client_description": self.update_client_description,
            "ride_tips": self.update_ride_tips,
            "ride_company": self.update_ride_company,
        }
        answer = simpledialog.askstring("Редактирование", "Что изменить? " + " / ".join(actions))
        if not answer:
            return
        action = actions.get(answer.lower().strip())
        if action:
            action()
        else:
            messagebox.showerror("Ошибка", "Варианты: " + ", ".join(actions))

    def update_company_name(self):
        data = self.ask_fields("Переименовать таксопарк", [("id", "Код таксопарка", "1"), ("name", "Новое название", "")])
        if data:
            self._change(sql.RENAME_COMPANY, [data["name"], data["id"]],
                         "Переименование таксопарка", "Таксопарк переименован", True)

    def update_client_description(self):
        data = self.ask_fields("Изменить описание типа клиента", [("id", "Код типа клиента", "1"), ("desc", "Новое описание", "")])
        if data:
            self._change(sql.UPDATE_CLIENT_DESC, [data["desc"], data["id"]],
                         "Изменение описания типа клиента", "Описание изменено", True)

    def update_ride_tips(self):
        data = self.ask_fields("Изменить чаевые поездки", [("id", "Код поездки", "1"), ("tips", "Чаевые $", "2.00")])
        if data:
            self._change(sql.UPDATE_RIDE_TIPS, [data["tips"], data["id"]], "Изменение чаевых", "Чаевые изменены")

    def update_ride_company(self):
        data = self.ask_fields("Сменить таксопарк поездки", [("id", "Код поездки", "1"), ("company", "Код таксопарка", "1")])
        if data:
            self._change(sql.UPDATE_RIDE_COMPANY, [data["company"], data["id"]],
                         "Смена таксопарка поездки", "Таксопарк поездки изменён")

    def edit_any_record(self):
        """Правка любого поля записи выбранной таблицы."""
        table = simpledialog.askstring("Полное редактирование", "Таблица: " + " / ".join(sql.TABLES))
        if not table:
            return
        table = table.strip().upper()
        if table not in sql.TABLES:
            messagebox.showerror("Ошибка", "Такой таблицы нет в списке GUI")
            return
        pk = PRIMARY_KEYS.get(table, "код")
        code = simpledialog.askinteger("Код записи", f"Введите {pk}")
        if not code:
            return
        select = psql.SQL("SELECT * FROM {} WHERE {} = %s").format(psql.Identifier(table), psql.Identifier(pk))
        rows, cols = self.fetch_rows(select, [code])
        if not rows:
            messagebox.showinfo("Редактирование", "Запись не найдена")
            return
        current = dict(zip(cols, rows[0]))
        editable = [c for c in cols if c != pk]
        data = self.ask_fields(f"Редактирование {table}",
                               [(c, c, "" if current[c] is None else str(current[c])) for c in editable])
        if not data:
            return
        assignments = [psql.SQL("{} = %s").format(psql.Identifier(c)) for c in editable]
        update = psql.SQL("UPDATE {} SET {} WHERE {} = %s").format(
            psql.Identifier(table), psql.SQL(", ").join(assignments), psql.Identifier(pk))
        params = [data[c] if data[c] != "" else None for c in editable] + [code]
        self.execute_and_display(update, params, title=f"Запись {table} обновлена", status="Полное редактирование", fetch=False)
        self.view_table(table)
        self.load_autocomplete_data()

    # ------------------------- удаление -------------------------
    def delete_record_window(self):
        kind = self._ask_kind("Удаление", "Что удалить? company / driver / client / ride")
        if not kind:
            return
        code = simpledialog.askinteger("Код", "Введите код записи")
        if not code:
            return
        if not messagebox.askyesno("Подтверждение", f"Удалить {kind} с кодом {code} вместе с его поездками?"):
            return
        if kind == "ride":
            self._change(sql.DELETE_RIDE, [code], "Удаление поездки", "Удалено")
        else:
            query, title = sql.DELETE_WITH_RIDES[kind]
            self._change(query, [code, code], title, "Удалено", refresh_names=True)

    # ------------------------- до и после -------------------------
    def update_before_after(self):
        data = self.ask_fields("UPDATE до/после", [("id", "Код поездки", "1"), ("tips", "Новые чаевые $", "3.00")])
        if not data:
            return
        ride = data["id"]
        before = self.execute(sql.RIDE_USER_VIEW, [ride], title="ДО UPDATE")
        update = self.execute(sql.UPDATE_RIDE_TIPS, [data["tips"], ride], title="UPDATE", fetch=False)
        after = self.execute(sql.RIDE_USER_VIEW, [ride], title="ПОСЛЕ UPDATE")
        self.display(before + "\n" + update + "\n" + after)
        self.set_status("UPDATE до/после")

    def delete_before_after(self):
        code = simpledialog.askinteger("DELETE до/после", "Код поездки для удаления")
        if not code:
            return
        if not messagebox.askyesno("Подтверждение", f"Удалить поездку код {code}?"):
            return
        before = self.execute(sql.RIDE_RAW, [code], title="ДО DELETE")
        deletion = self.execute(sql.DELETE_RIDE, [code], title="DELETE", fetch=False)
        after = self.execute(sql.RIDE_RAW, [code], title="ПОСЛЕ DELETE")
        self.display(before + "\n" + deletion + "\n" + after)
        self.set_status("DELETE до/после")

    def archive_old_rides(self):
        years = simpledialog.askinteger("Архивация", "Архивировать поездки старше N лет",
                                        initialvalue=3, minvalue=1, maxvalue=100)
        if not years:
            return
        if not messagebox.askyesno("Подтверждение", f"Перенести в архив поездки старше {years} лет?"):
            return
        self._change(sql.ARCHIVE_OLD_RIDES, [years, years], "Архивация старых поездок", "Архивация выполнена")
