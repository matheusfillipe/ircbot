#########################################################################
#  Matheus Fillipe -- 13, December of 2020                              #
#                                                                       #
#########################################################################
#  Description: A very simple and inefficient wrapper around basic      #
#  sqlite queries that are normally used. Don't use this module for     #
#  large projects big loops etc.                                        #
#                                                                       #
#########################################################################
#  Depends on: sqlite module, basically all python std.                 #
#                                                                       #
#########################################################################

import sqlite3
from copy import copy
from pathlib import Path
from typing import Any


class DB:
    def __init__(self, db_file_path: str, table_name: str, row_labels: list[str], keep_open: bool) -> None:
        """Initialize the DB object.

        :param db_file_path: str. Path for the file to save the SQLite DB.
        :param table_name: str. Name of the table to use.
        :param row_labels: list[str]. Strings with the data keys to store, columns of the table.
        :param keep_open: bool. If set to True, manually call connect and close.
        """
        self.filepath = db_file_path
        self.table_name = table_name
        self.row_labels = row_labels
        self.keep_open = keep_open
        self._check_if_exists_if_not_create()

    def to_dict(self, data):
        """Convert a row to a dictionary.

        :param data: list representing a full row to convert to a dict with the respective keys defined in row_labels.
        """
        return {n: data[i] for i, n in enumerate(self.row_labels)}

    def to_dict_with_id(self, data: list[Any]) -> dict[str, Any]:
        """Convert a row to a dictionary with the "id" field.

        :param data: list representing a full row to convert to a dict with the respective keys defined in row_labels.
        """
        return {n: data[i] for i, n in enumerate(["id"] + self.row_labels)}

    def to_list(self, data: dict[str, Any]) -> list[Any]:
        """Convert a dictionary to a row list as defined by row_labels.

        :param data: dict.
        """
        return [data[n] if n in data.keys() else "" for n in self.row_labels]

    def _check_if_exists_if_not_create(self):
        self._connect()
        try:
            self.cursor.execute("SELECT * FROM " + self.table_name)
            col_name_list = [tuple[0] for tuple in self.cursor.description]
            col_name_list.remove("id")
        except:
            col_name_list = []
        self._close()
        if not sorted(col_name_list) == sorted(self.row_labels):
            self.delete_table()
            self._connect()
            self.cursor.execute(
                "CREATE TABLE IF NOT EXISTS "
                + self.table_name
                + " (id INTEGER primary key AUTOINCREMENT,"
                + str(self.row_labels)[1:-1]
                + ")"
            )
            self._close()

    def connect(self):
        self.connection = sqlite3.connect(self.filepath)
        self.cursor = self.connection.cursor()
        self.connected = True

    def _connect(self):
        if self.keep_open:
            return
        self.connect()

    def close(self):
        self.connection.commit()
        self.connection.close()
        self.connected = False

    def _close(self):
        if self.keep_open:
            return
        self.close()

    def _save_data(self, data_: dict[str, Any]):
        rows = self.to_list(data_)
        self.cursor.execute(
            "INSERT INTO "
            + self.table_name
            + " ("
            + str(self.row_labels)[1:-1]
            + ")VALUES ("
            + (len(self.row_labels) * "?,")[:-1]
            + ")",
            rows,
        )

    def new_data(self, data_: dict[str, Any]) -> int:
        self._connect()
        self._save_data(data_)
        id = copy(self.cursor.lastrowid)
        self._close()
        if id is None:
            raise BaseException("Error saving data!")
        return id

    def save_data_list(self, lista: list[dict[str, Any]]):
        self._connect()
        [self._save_data(data_) for data_ in lista]
        self._close()

    def _get_data(self, id: int) -> dict[str, Any]:
        return self.to_dict(
            list(list(self.cursor.execute("SELECT * FROM " +
                 self.table_name + " WHERE id = ?", (id,)))[0])[1:]
        )

    def get_data(self, id: int) -> dict[str, Any]:
        self._connect()
        data_ = self._get_data(id)
        self._close()
        return data_

    def get_data_with_id(self, id: int) -> dict[str, Any]:
        self._connect()
        data_ = self._get_data(id)
        self._close()
        data_.update({"id": id})
        return data_

    def get_all(self):
        self._connect()
        data_s = [self.to_dict(row[1:]) for row in self.cursor.execute(
            "SELECT * FROM " + self.table_name)]
        self._close()
        return data_s

    def get_all_with_id(self):
        self._connect()
        data_s = [self.to_dict_with_id(row) for row in self.cursor.execute(
            "SELECT * FROM " + self.table_name)]
        self._close()
        return data_s

    def _get_by_key(self, key: str, value: Any):
        if key not in self.row_labels:
            raise BaseException("Invalid Key!")
        self._connect()
        cursor = self.cursor.execute(
            "SELECT * FROM " + self.table_name + " WHERE " + key + " = ?", (value,))
        data = cursor.fetchone()
        self._close()
        return data

    def get_by_key(self, key: str, value: Any):
        data = self._get_by_key(key, value)
        return self.to_dict(list(data)[1:]) if data else None

    def get_by_key_with_id(self, key: str, value: Any):
        data = self._get_by_key(key, value)
        return self.to_dict_with_id(data) if data else None

    def find_data(self, key: str, name: Any):
        func = str
        try:
            float(name)
            func = float
        except:
            pass
        self._connect()
        if isinstance(name, str):
            id_list = [
                [list(data_)[0], self.to_dict(list(data_)[1:])[key]]
                for data_ in list(self.cursor.execute("SELECT * FROM " + self.table_name))
                if name.lower() in str(self.to_dict(list(data_)[1:])[key]).lower()
            ]
        else:
            id_list = [
                [list(data_)[0], self.to_dict(list(data_)[1:])[key]]
                for data_ in list(self.cursor.execute("SELECT * FROM " + self.table_name))
                if str(name) == str(self.to_dict(list(data_)[1:])[key])
            ]
        self._close()
        try:
            return [x[0] for x in sorted(id_list, key=lambda x: func(x[1]))]
        except ValueError:
            return [x[0] for x in sorted(id_list, key=lambda x: str(x[1]))]

    def find_exact_match_from_key(self, key, nome):
        func = str
        try:
            float(nome)
            func = float
        except:
            pass
        self._connect()
        if isinstance(nome, str):
            id_list = [
                [list(data_)[0], self.to_dict(list(data_)[1:])[key]]
                for data_ in list(self.cursor.execute("SELECT * FROM " + self.table_name))
                if nome.lower() == str(self.to_dict(list(data_)[1:])[key]).lower()
            ]
        else:
            id_list = [
                [list(data_)[0], self.to_dict(list(data_)[1:])[key]]
                for data_ in list(self.cursor.execute("SELECT * FROM " + self.table_name))
                if str(nome) == str(self.to_dict(list(data_)[1:])[key])
            ]
        self._close()
        try:
            return [x[0] for x in sorted(id_list, key=lambda x: func(x[1]))]
        except ValueError:
            return [x[0] for x in sorted(id_list, key=lambda x: str(x[1]))]

    def get_data_list_by_id_list(self, id_list: list[int]) -> list[dict[str, Any]]:
        return [self.get_data(id) for id in id_list]

    def get_data_list_by_id_list_with_id(self, id_list: list[int]) -> list[dict[str, Any]]:
        return [self.get_data_with_id(id) for id in id_list]

    def find_data_by_key(self, key: str, name: Any):
        return sorted(self.get_data_list_by_id_list(self.find_data(key, name)), key=lambda x: x[key])

    def find_greater_than(self, key: str, value: Any):
        assert isinstance(value, int) or isinstance(
            value, float), "Enter numeric values"
        self._connect()
        id_list = [
            [list(data_)[0], self.to_dict(list(data_)[1:])[key]]
            for data_ in list(self.cursor.execute("SELECT * FROM " + self.table_name))
            if float(value) <= float(self.to_dict(list(data_)[1:])[key])
        ]
        self._close()
        return [x[0] for x in sorted(id_list, key=lambda x: x[1])]

    def find_less_than(self, key, value):
        assert isinstance(value, int) or isinstance(
            value, float), "Enter numeric values"
        self._connect()
        id_list = [
            [list(data_)[0], self.to_dict(list(data_)[1:])[key]]
            for data_ in list(self.cursor.execute("SELECT * FROM " + self.table_name))
            if float(value) >= float(self.to_dict(list(data_)[1:])[key])
        ]
        self._close()
        return [x[0] for x in sorted(id_list, key=lambda x: x[1])]

    def find_data_bigger_than(self, key: str, value: Any):
        return sorted(
            self.get_data_list_by_id_list(self.find_greater_than(key, value)),
            key=lambda x: x[key],
        )

    def find_data_less_than(self, key: str, value: Any):
        return sorted(
            self.get_data_list_by_id_list(self.find_less_than(key, value)),
            key=lambda x: x[key],
        )

    def delete_data(self, id: int):
        self._connect()
        id_str = str(id)
        self.cursor.execute(
            "DELETE FROM " + self.table_name + " WHERE ID = ?", (id_str,))
        self._close()

    def update(self, id: int, data_: dict[str, Any]):
        """Update given id with new dict.

        :param id: id to modify.
        :param data_: data dict that can only contain fields to update.
        """
        d = self.get_data(id)
        d.update(data_)
        d = self.to_list(d)
        self._connect()
        self.cursor.execute(
            "UPDATE " + self.table_name + " SET " +
            " = ?,".join(self.row_labels) + "= ? WHERE id= ?",
            (d + [id]),
        )
        self._close()

    def delete_table(self):
        """Delete the table."""
        self._connect()
        self.cursor.execute("DROP TABLE IF EXISTS " + self.table_name)
        self._close()

    def delete_all(self):
        """Delete the DB file."""
        Path(self.filepath).unlink()
