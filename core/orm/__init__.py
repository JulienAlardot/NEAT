from typing import Dict

from core.orm.database import Database


class AbstractModelElement:
    _table: str = None
    _columns: Dict[str, type] = {'id': int}

    def __init__(self, db):
        """

        :param core.orm.database.Database db:
        """
        self._db: Database = db

    def _cast_data_to_types(self, *args):
        if not args:
            return args
        cleaned_args = []
        for key, value in zip(self._columns, args):
            cleaned_args.append(self._columns.get(key, str)(value))
        return tuple(cleaned_args)

    def _search_from_id(self, element_id: int, class_table=None):
        class_table = class_table or self.__class__
        res = self._db.execute(
            f"""
                SELECT {', '.join(class_table._columns)}
                FROM {class_table._table}
                WHERE id = {element_id}
                ORDER BY id DESC
                LIMIT 1
            """
        )
        if not res:
            raise ValueError(f"No {__class__} exists with that id")
        return self._cast_data_to_types(*res)

    def _search_from_data(self, class_table=None, **kwargs):
        class_table = class_table or self.__class__
        where_clause = ' AND '.join((f"{key} = {value}" for key, value in kwargs.items()))

        res = self._db.execute(
            f"""
                SELECT {', '.join(class_table._columns)}
                FROM {class_table._table}
                WHERE {where_clause}
                ORDER BY id DESC
                LIMIT 1
            """
        )
        return self._cast_data_to_types(*res)
