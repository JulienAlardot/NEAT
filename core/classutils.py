from core.database import Database

_db = Database(f'{__file__}/../../data/template', override=True)

_matching = {key: value for value, key in _db.execute("""SELECT id, name FROM node_type ORDER BY name""")}


class NodeTypes:
    hidden, input, output = _matching.values()


class Node:
    def __init__(self, db, node_type=None, connection_historical_id=None, node_id=None):
        self._db = db

        if isinstance(node_type, str):
            node_type = getattr(NodeTypes, node_type.lower())

        if node_id:
            res = self._db.execute(f"""
            SELECT id, node_type_id, connection_historical_id  FROM node WHERE id = {node_id} LIMIT 1
            """)
            if not res:
                raise ValueError('No node exists with that id')
            self.id, self.node_type, self.connection_historical = res[0]
        else:
            if not connection_historical_id and not node_type:
                raise ValueError('A node must have a connection_historical_id or a node_type specified')

            if connection_historical_id:
                res = self._db.execute(f"""
                    SELECT id FROM connection_historical WHERE id = {connection_historical_id}
                """)
                if not res:
                    raise ValueError('The given connection_historical_id does not exists')

            self._db.execute(f"""
                INSERT INTO node (node_type_id, connection_historical_id)
                    VALUES ({node_type}, {connection_historical_id or 'NULL'})
            """)
            res = self._db.execute(f"""
                SELECT id
                FROM node
                WHERE node_type_id = {node_type} AND connection_historical_id = {connection_historical_id or "NULL"}
                ORDER BY id DESC
                LIMIT 1
            """)
            if not res:
                raise ValueError('Incorrect node_type or connection_historical_id given')
            self.id = res[0][0]
            self.node_type = node_type
            self.connection_historical = connection_historical_id


class HistoricalConnection:
    def __init__(self, db, historical_connection_id=None, in_node_id=None, out_node_id=None):
        self._db = db

        if historical_connection_id:
            res = self._db.execute(f"""
            SELECT id, in_node_id, out_node_id FROM connection_historical WHERE id = {historical_connection_id} 
            LIMIT 1
            """)
            if not res:
                raise ValueError('No HistoricalConnection exists with that id')
            self.id, self.in_node, self.out_node = res[0]
        elif in_node_id and out_node_id:
            if in_node_id == out_node_id:
                raise ValueError("in_node_id and out_node_id must be different nodes")

            res = self._db.execute(f"""
            SELECT id, in_node_id, out_node_id  
                FROM connection_historical 
                WHERE in_node_id = {in_node_id} AND out_node_id = {out_node_id}
                LIMIT 1
            """)
            if res:
                self.id, self.in_node, self.out_node = res[0]
            else:
                self._db.execute(f"""
                INSERT INTO connection_historical (in_node_id, out_node_id)
                    VALUES ({in_node_id}, {out_node_id})
                """)
                res = self._db.execute(f"""
                    SELECT id
                    FROM connection_historical
                    WHERE in_node_id = {in_node_id} AND out_node_id = {out_node_id}
                    ORDER BY id DESC
                    LIMIT 1
                """)
                if not res:
                    raise ValueError("Incorrect values for in_node_id and/or out_node_id parameters")
                self.id = res[0][0]
                self.in_node = in_node_id
                self.out_node = out_node_id
        else:
            raise ValueError(
                    "A Connection must be given either an existing historical_connection_id or in and out_node_id")
