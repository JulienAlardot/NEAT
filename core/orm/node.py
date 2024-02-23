from core.activation import sigmoid
from core.orm.enums import NodeTypes


class Node:
    def __init__(self, db, node_type=None, connection_historical_id=None, node_id=None, activation_func=sigmoid):
        self._db = db
        self.input_sum = 0
        self._activation_func = activation_func
        
        if isinstance(node_type, str):
            node_type = getattr(NodeTypes, node_type.lower())
        
        if node_id:
            res = self._db.execute(
                f"""
            SELECT id, node_type_id, connection_historical_id  FROM node WHERE id = {node_id} LIMIT 1
            """)
            if not res:
                raise ValueError('No node exists with that id')
            self.id, self.node_type, self.connection_historical = res[0]
        else:
            if not connection_historical_id and not node_type:
                raise ValueError('A node must have a connection_historical_id or a node_type specified')
            
            if connection_historical_id:
                res = self._db.execute(
                    f"""
                    SELECT id FROM connection_historical WHERE id = {connection_historical_id}
                """)
                if not res:
                    raise ValueError('The given connection_historical_id does not exists')
            if node_type == NodeTypes.bias:
                self.id = self._db.execute(
                    """
                    SELECT node.id
                    FROM node
                    LEFT JOIN node_type nt on node.node_type_id = nt.id
                    WHERE nt.name = 'Bias'
                """)[0][0]
                self.node_type = node_type
                self.connection_historical = None
            else:
                node_type = node_type or NodeTypes.hidden
                self._db.execute(
                    f"""
                    INSERT INTO node (node_type_id, connection_historical_id)
                        VALUES ({node_type}, {connection_historical_id or "NULL"})
                """)
                res = self._db.execute(
                    f"""
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
    
    @property
    def output(self):
        return self._activation_func(self.input_sum)
