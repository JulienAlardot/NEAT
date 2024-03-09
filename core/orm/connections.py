from typing import Dict

from core.orm import AbstractModelElement


class HistoricalConnection(AbstractModelElement):
    _table: str = 'connection_historical'
    _columns: Dict[str, type] = {'id': int, 'in_node_id': int, 'out_node_id': int}
    id: int
    in_node: int
    out_node: int

    def __init__(self, db, historical_connection_id=None, in_node_id=None, out_node_id=None):
        if not (historical_connection_id or (in_node_id and out_node_id)):
            raise ValueError("Must be given either an existing historical_connection_id or in and out_node_id")

        super().__init__(db)
        res = None, None, None
        if historical_connection_id:
            res = self._search_from_id(
                historical_connection_id,
                class_table=HistoricalConnection,
            )
            if not res:
                raise ValueError('No HistoricalConnection exists with that id')
        elif in_node_id and out_node_id:
            if in_node_id == out_node_id:
                raise ValueError("in_node_id and out_node_id must be different nodes")
            res = self._search_from_data(
                class_table=HistoricalConnection,
                in_node_id=in_node_id,
                out_node_id=out_node_id,
            )
            if not res:
                res = self._create_historical_connection(in_node_id, out_node_id)
            if not res:
                raise ValueError("Incorrect values for in_node_id and/or out_node_id parameters")
        self.id, self.in_node, self.out_node = res

    def _create_historical_connection(self, in_node_id, out_node_id):
        self._db.execute(
            f"""
                INSERT INTO connection_historical (in_node_id, out_node_id)
                    VALUES ({in_node_id}, {out_node_id})
            """
        )
        return self._search_from_data(class_table=HistoricalConnection, in_node_id=in_node_id, out_node_id=out_node_id)


class Connection(HistoricalConnection):
    _table: str = 'connection'
    _columns: Dict[str, type] = {
        'id': int,
        'genotype_id': int,
        'weight': float,
        'is_enabled': bool,
        'historical_id': int,
    }
    genotype_id: int
    is_enabled: bool
    weight: float
    in_node: int
    out_node: int

    def __init__(
            self,
            db,
            historical_connection_id=None,
            in_node_id=None,
            out_node_id=None,
            genotype_id=None,
            connection_id=None,
            weight=None,
            is_enabled=None,
    ):
        if not connection_id and not genotype_id:
            raise ValueError("Must specify a genotype_id or a connection_id")
        if historical_connection_id or (in_node_id and out_node_id):
            super().__init__(
                db=db,
                historical_connection_id=historical_connection_id,
                in_node_id=in_node_id,
                out_node_id=out_node_id,
            )
            self.historical_id = self.id
        else:
            AbstractModelElement.__init__(self, db=db)

        if connection_id:
            res = self._search_from_id(connection_id)
            self.id, self.genotype_id, self._weight, self._is_enabled, self.historical_id = res
            historical_connection = HistoricalConnection(self._db, historical_connection_id=self.historical_id)
            self.in_node = historical_connection.in_node
            self.out_node = historical_connection.out_node

        if not connection_id:
            res = self._db.execute(
                f"""
            SELECT id
            FROM genotype
            WHERE id = {genotype_id}
            ORDER BY id DESC
            LIMIT 1
            """)
            if not res:
                raise ValueError("Specified genotype_id doesn't exist")

            res = self._db.execute(
                f"""
            SELECT id, genotype_id, is_enabled, weight
            FROM connection
            WHERE genotype_id = {genotype_id} AND historical_id = {self.historical_id}
            ORDER BY id DESC
            LIMIT 1
            """)

            if res:
                self.id, self.genotype_id, self._is_enabled, self._weight = res
                if is_enabled:
                    self.is_enabled = is_enabled
                if weight:
                    self.weight = weight
            else:
                is_enabled = is_enabled if is_enabled is not None else True
                weight = weight if weight is not None else 1.0
                self._db.execute(
                    f"""
                INSERT INTO connection (historical_id, genotype_id, is_enabled, weight)
                    VALUES ({self.historical_id}, {genotype_id}, {is_enabled}, {weight})
                """)

                res = self._db.execute(
                    f"""
                SELECT id
                FROM connection
                WHERE (historical_id = {self.historical_id}
                        AND genotype_id = {genotype_id}
                        AND is_enabled = {"TRUE" if is_enabled else "FALSE"}
                        AND weight = {weight})
                ORDER BY id DESC
                LIMIT 1
                """)

                self.id = res[0]
                self._weight = weight
                self._is_enabled = is_enabled
                self.genotype_id = genotype_id
            historical_connection = HistoricalConnection(self._db, historical_connection_id=self.historical_id)
            self.in_node = historical_connection.in_node
            self.out_node = historical_connection.out_node

    @property
    def is_enabled(self):
        return self._is_enabled

    @is_enabled.setter
    def is_enabled(self, value: bool):
        self._db.execute(
            f"""
        UPDATE connection
            SET is_enabled = {"TRUE" if value else "FALSE"}
        WHERE id = {self.id}
        """)
        self._is_enabled = value

    @property
    def weight(self):
        return self._weight

    @weight.setter
    def weight(self, value: float):
        self._db.execute(f"""UPDATE connection SET weight = {value} WHERE id = {self.id}""")
        self._weight = value
