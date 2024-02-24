import os
import random

from core.orm.connections import Connection
from core.orm.enums import NodeTypes
from core.orm.node import Node


class Genotype:
    def __init__(self, db, genotype_id=None, node_ids=None, connection_dicts=None, parent_genotype_ids=None):
        self._db = db
        parent_genotype_ids = [] if parent_genotype_ids is None else parent_genotype_ids
        if not (genotype_id or (node_ids and connection_dicts)):
            raise ValueError("Must specify either an existing genotype_id or both node_ids and connection_dicts")

        if genotype_id:
            res = self._db.execute(
                f"""
            SELECT id, parent_1_id, parent_2_id
            FROM genotype
            WHERE id = {genotype_id}
            ORDER BY id DESC
            LIMIT 1
            """)
            if not res:
                raise ValueError("Specified genotype_id doesn't exist")
            self.id, *self.parent_ids = res[0]
            self.parent_ids = set((parent for parent in self.parent_ids if parent))
            res = self._db.execute(
                f"""
            SELECT connection.id
            FROM connection
            WHERE connection.genotype_id = {genotype_id}
            """)
            self.connection_ids = set((sub_res[0] for sub_res in res))
            res = self._db.execute(
                f"""
            SELECT node_id
            FROM genotype_node_rel
            WHERE genotype_node_rel.genotype_id = {genotype_id}
            """)
            self.node_ids = set((sub_res[0] for sub_res in res))
        else:
            res = self._db.execute(
                """
            SELECT MAX(id)
            FROM genotype
            """)
            self.id = (res[0][0] or 0) + 1
            self.parent_ids = set((parent for parent in parent_genotype_ids if parent))
            parent_genotype_ids = list(sorted(self.parent_ids)) + ['NULL', 'NULL']
            self._db.execute(
                f"""
            INSERT INTO genotype (id, parent_1_id, parent_2_id)
                VALUES ({self.id}, {parent_genotype_ids[0]}, {parent_genotype_ids[1]})
            """)

            node_ids |= set(
                row[0] for row in self._db.execute(
                    """
                        SELECT node.id
                        FROM node
                        LEFT JOIN node_type AS nt on node.node_type_id = nt.id
                        WHERE nt.name = 'Bias'
                    """
                )
            )
            node_values = ",\n".join((f"({self.id}, {node_id})" for node_id in sorted(node_ids)))
            self._db.execute(
                f"""
            INSERT INTO genotype_node_rel (genotype_id, node_id)
                VALUES {node_values}
            """)
            res = self._db.execute(
                f"""
            SELECT node_id
            FROM genotype_node_rel
            WHERE genotype_node_rel.genotype_id = {self.id}
            """)
            self.node_ids = set((row[0] for row in res))
            self.connection_ids = set()
            for connection in connection_dicts:
                connection.update({'genotype_id': self.id})
                self.connection_ids.add(Connection(self._db, **connection).id)

    @property
    def historical_connection_ids(self):
        connection_ids = ', '.join((str(c_id) for c_id in self.connection_ids))
        res = self._db.execute(
            f"""
        SELECT historical_id
        FROM connection
        WHERE id IN ({connection_ids})
        """)
        return set((row[0] for row in res))

    def __xor__(self, other):
        if not isinstance(other, Genotype):
            raise TypeError(
                "Cannot use xor operator between an instance of 'Genotype' and an instance of another class"
            )
        diff_nodes = len(other.node_ids ^ self.node_ids)
        total_nodes = max(len(other.node_ids), len(self.node_ids))
        diff_connections = len(other.historical_connection_ids ^ self.historical_connection_ids)
        total_connections = max(len(other.historical_connection_ids), len(self.historical_connection_ids))
        return (total_nodes + total_connections - diff_nodes - diff_connections) / (total_nodes + total_connections)

    def as_dict(self):
        connections = (Connection(self._db, connection_id=connection) for connection in sorted(self.connection_ids))
        return {
            'db': self._db,
            'genotype_id': self.id,
            'node_ids': self.node_ids,
            'connection_dicts': tuple(
                {
                    'historical_connection_id': connection.historical_id,
                    'in_node_id': connection.in_node,
                    'out_node_id': connection.out_node,
                    'weight': connection.weight,
                    'is_enabled': connection.is_enabled,
                } for connection in connections
            ),
            'parent_genotype_ids': self.parent_ids,
        }

    def get_mutated(self):
        split_rate, weight_rate, add_rate, switch_rate, weight_std = self._db.execute(
            """
            SELECT (
            mutation_split_rate, mutation_weight_rate, mutation_add_rate, mutation_switch_rate, mutation_weight_std
            )
            FROM model_metadata
            ORDER BY id DESC
            LIMIT 1
        """)[0]
        mutant = self.as_dict()
        bias_node_id = list(
            sorted(
                (row[0] for row in self._db.execute(
                    """
            SELECT node.id
            FROM node
            LEFT JOIN node_type AS nt on node.node_type_id = nt.id
            WHERE nt.name = 'Bias'
            LIMIT 1
            """))))
        mutant['node_ids'].add(bias_node_id)
        new_connections = list(mutant.get('connection_dicts', []))
        add_connection_count = 0
        in_out_node_mapping = {}
        for connection in mutant.get('connection_dicts', []):
            historical_id = connection['historical_connection_id']
            in_out_node_mapping.setdefault(connection['in_node_id'], []).append(connection['out_node_id'])
            del connection['historical_connection_id']
            r = random.random()
            m_rate = weight_rate
            if r < m_rate:
                connection['weight'] += (random.random() - .5) * 2 * weight_std
                continue
            m_rate += switch_rate
            if r < m_rate:
                connection['is_enabled'] = not connection.get('is_enabled', True)
                continue
            m_rate += add_rate
            if r < m_rate:
                add_connection_count += 1
                continue
            m_rate += split_rate
            if r < m_rate:
                new_node_id = Node(self._db, connection_historical_id=historical_id).id
                if new_node_id in mutant['node_ids']:
                    continue
                connection['is_enabled'] = False
                mutant['node_ids'].add(new_node_id)
                new_connections.extend(
                    ({
                         'in_node_id': connection['in_node'],
                         'out_node_id': new_node_id,
                         'weight': 1,
                         'is_enabled': True,
                     }, {
                         'in_node_id': bias_node_id,
                         'out_node_id': new_node_id,
                         'weight': 0.,
                         'is_enabled': True,
                     }, {
                         'in_node_id': new_node_id,
                         'out_node_id': connection['out_node'],
                         'weight': connection.weight,
                         'is_enabled': connection.is_enabled,
                     },
                    ))
        query = """
            SELECT node.id
            FROM genotype_node_rel
            INNER JOIN node ON genotype_node_rel.node_id = node.id
            INNER JOIN node_type AS nt ON node.node_type_id = nt.id
            WHERE genotype_node_rel.genotype_id = {}
                AND node_type.name = {}
                AND node.id IN ({})
        """
        input_nodes = set(
            (
                row[0] for row in self._db.execute(
                query.format(mutant['genotype_id'], 'Input', ', '.join(mutant['node_ids']))
            )))
        hidden_nodes = set(
            (
                row[0] for row in self._db.execute(
                query.format(mutant['genotype_id'], 'Hidden', ', '.join(mutant['node_ids']))
            )))
        output_nodes = set(
            (
                row[0] for row in self._db.execute(
                query.format(mutant['genotype_id'], 'Output', ', '.join(mutant['node_ids']))
            )))
        escape = False
        for input_node in input_nodes | hidden_nodes:
            for output_node in (hidden_nodes if input_node not in hidden_nodes else {}) | output_nodes:
                if output_node not in in_out_node_mapping.get(input_node, []):
                    new_connections.append(
                        {
                            'in_node_id': input_node,
                            'out_node_id': output_node,
                            'weight': (random.random() * 2) - 1,
                            'is_enabled': True,
                        })
                    add_connection_count -= 1
                    escape = add_connection_count > 0
                    break
            if escape:
                break
        mutant['connection_dicts'] = tuple(new_connections)
        del mutant['genotype_id']
        return mutant

    def draw(self, save_path=None):

        # graph header declaration
        graph_lines = [
            'digraph {', '    rankdir = "LR"', '    splines = polyline', '    bgcolor = "invis"',
            '    node [margin = 0 fontcolor = black fontsize = 32 width = 0.5 style = filled fixsized = True '
            'labelloc = b fontname = calibri]',
            '    edge [arrowhead = onormal width = 0.1 tailport = e headclip = True tailclip = True penwidth = 0.5]',
            '',
        ]

        # Assemble necessary node data
        node_mapping = {
            NodeTypes.bias: {},
            NodeTypes.input: {},
            NodeTypes.hidden: {},
            NodeTypes.output: {},
        }
        for node_id in sorted(self.node_ids):
            node_mapping[Node(self._db, node_id=node_id).node_type][node_id] = f"node_{node_id}"

        # Add nodes declaration lines
        graph_lines += [
            '    subgraph {',
            '    rank = same',
            '    node [shape = square fillcolor = cyan]',
        ]
        for node_id, name in node_mapping[NodeTypes.bias].items():
            graph_lines.append(
                f'    {name} [label = "{node_id}\\nBias" shape = "diamond"]')
        for node_id, name in node_mapping[NodeTypes.input].items():
            graph_lines.append(
                f'    {name} [label = "{node_id}"]')
        graph_lines += [
            '    }',
            '    subgraph {',
            '    node [shape = circle fillcolor = blue]',
        ]
        for node_id, name in node_mapping[NodeTypes.hidden].items():
            graph_lines.append(
                f'    {name} [label = "{node_id}"]')

        graph_lines += [
            '    }',
            '    subgraph {',
            '    rank = same',
            '    node [shape = square fillcolor = red]',
        ]
        for node_id, name in node_mapping[NodeTypes.output].items():
            graph_lines.append(
                f'    {name} [label = "{node_id}"]')

        graph_lines.append('    }')
        # Assemble necessary connection data
        connection_mapping = {
            NodeTypes.input: [],
            NodeTypes.hidden: [],
            NodeTypes.output: [],
        }
        for conn_id in sorted(self.connection_ids):
            conn = Connection(self._db, connection_id=conn_id)
            in_node_id = conn.in_node
            out_node_id = conn.out_node
            weight = conn.weight
            weight *= 1 if conn.is_enabled else 0
            if weight != 0.:
                is_pos = weight > 0
                intensity = round(min(255, max(0, ((round(abs(weight) - 1) * 2) ** (1 / 2.1)) * 32) + 128))
                ramp = '0123456789abcdef'
                intensity = ramp[intensity // 16] + ramp[intensity % 16]
                color = f"#{'00' if is_pos else intensity}00{intensity if is_pos else '00'}"
            else:
                color = '#888888'
            in_node = Node(self._db, node_id=in_node_id)
            out_node = Node(self._db, node_id=out_node_id)
            if in_node.node_type == NodeTypes.input:
                node_type = NodeTypes.input
            elif out_node.node_type == NodeTypes.output:
                node_type = NodeTypes.output
            else:
                node_type = NodeTypes.hidden
            connection_mapping[node_type].append(
                f'    node_{in_node_id} -> node_{out_node_id} [color = "{color}"]')
        # Add separator
        graph_lines.append('')

        # Add connection declaration lines
        graph_lines += connection_mapping[NodeTypes.input]
        graph_lines += connection_mapping[NodeTypes.hidden]
        graph_lines += connection_mapping[NodeTypes.output]

        "Close graph"
        graph_lines.append("}")
        graph_lines.append('')
        graph = "\n".join(graph_lines)
        if save_path:
            if os.path.isdir(save_path):
                save_path = os.path.join(save_path, f"genotype_{self.id}")

            if not save_path.lower().endswith('.dot'):
                save_path += '.dot'

            with open(save_path, 'wt', encoding='utf-8') as save:
                save.write(graph)
        return graph
