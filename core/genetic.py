import random
from typing import Tuple

import numpy as np

from core import specimen_to_graph


class ConnectionSubtype:
    INPUT = 0
    HIDDEN = 1
    OUTPUT = 2


class ConnGene:
    in_node: int
    out_node: int
    weight: float
    enabled: bool
    gid: int

    def __init__(self, gid, weight, in_node, out_node, enabled=True):
        """

        :param int gid:
        :param float weight:
        :param int in_node:
        :param bool enabled:
        :param int out_node:
        """
        self.type = 0
        self.enabled = enabled
        self.id = gid
        self.weight = weight
        self.in_node = in_node
        self.out_node = out_node
        self._input = 0.

    @property
    def input(self):
        return self._input

    @input.setter
    def input(self, value: float):
        self._input = value

    @property
    def output(self):
        return self.weight * self._input


class NodeGene:
    subtype: int
    id: int

    def __init__(self, gid, subtype):
        """

        :param int gid:
        :param int or float or str subtype:
        """
        self.subtype = subtype
        self.id = gid

    @property
    def subtype(self):
        return self._subtype

    @subtype.setter
    def subtype(self, subtype):
        """

        :param int or float or str subtype:
        """
        if subtype.__class__ == str:
            subtype = subtype.lower()
            if subtype in ("input", "hidden", "output"):
                self._subtype = ConnectionSubtype.INPUT if subtype == "input" else ConnectionSubtype.HIDDEN \
                    if subtype == "hidden" else ConnectionSubtype.OUTPUT
            else:
                raise ValueError(f'subtype parameter must be either "input", "hidden" or "output" not {subtype}')
        elif subtype.__class__ in (int, float):
            subtype = int(subtype)
            if subtype in tuple(range(3)):
                self._subtype = subtype
            else:
                raise ValueError(f'subtype parameter must be either 1, 2, 3 not {subtype}')
        else:
            raise TypeError(f"subtype parameter type must be either str or int")


class GenesHistory:
    def __init__(self, input_size, output_size):
        input_nodes: Tuple[Tuple[int, int]] = tuple((i, ConnectionSubtype.INPUT) for i in range(input_size))
        output_nodes: Tuple[Tuple[int, int]] = tuple(
            (i, ConnectionSubtype.OUTPUT) for i in range(input_size, input_size + output_size))
        connections = list()

        i: int = 0
        for in_node in input_nodes:
            for out_node in output_nodes:
                connections.append((i, in_node[0], out_node[0]))
                i += 1

        self._connections: tuple = tuple(connections)
        self._nodes: Tuple[Tuple[int, int]] = input_nodes + output_nodes[:]

    @property
    def connections_genes(self):
        return self._connections

    @property
    def nodes_genes(self):
        return self._nodes

    @property
    def input_nodes_ids(self):
        return tuple([i for i, v in self._nodes if v == ConnectionSubtype.INPUT])

    @property
    def output_nodes_ids(self):
        return tuple([i for i, v in self._nodes if v == ConnectionSubtype.OUTPUT])

    @property
    def hidden_nodes_ids(self):
        return tuple([i for i, v in self._nodes if v == ConnectionSubtype.HIDDEN])

    def add_connection(self, in_node, out_node):
        if in_node == out_node:
            raise ValueError("Cannot connect a node to itself")

        if in_node in self.output_nodes_ids or out_node in self.input_nodes_ids:
            raise ValueError("Cannot use a model output node as a node input for a new connection or "
                             "a model input node as an output")
        conn_id = -1
        for conn in self._connections:
            if conn[1] == in_node and conn[2] == out_node:
                conn_id = conn[0]
                break

        if conn_id == -1:
            conn_id = len(self._connections)
            self._connections = self._connections[:] + ((conn_id, in_node, out_node),)
        return conn_id

    def add_node(self):
        new_node = (len(self._nodes), 1)
        self._nodes = self._nodes[:] + (new_node,)
        return new_node[0]

    def split_connection(self, in_node, out_node, weight=0.5):
        nodes_ids = self.input_nodes_ids + self.output_nodes_ids + self.hidden_nodes_ids
        if in_node not in nodes_ids:
            raise ValueError(f"{in_node} not found in {nodes_ids} in_node parameter")
        if out_node not in nodes_ids:
            raise ValueError(f"{out_node} not found in {nodes_ids} in_node parameter")
        temp_out_nodes = set()
        temp_in_nodes = set()
        conn_id_start = -1
        conn_id_end = -1
        for conn in self._connections:
            if conn[1] == in_node:
                temp_in_nodes.add(conn[2])
            if conn[2] == out_node:
                temp_out_nodes.add(conn[1])
        nodes = tuple(temp_in_nodes.intersection(temp_out_nodes))
        if len(nodes) == 1:
            new_node_id = nodes[0]
            for conn in self._connections:
                if conn[1] == in_node and conn[2] == new_node_id:
                    conn_id_start = conn[0]
                elif conn[1] == new_node_id and conn[2] == out_node:
                    conn_id_end = conn[0]
                if conn_id_start != -1 and conn_id_end != -1:
                    break
        elif len(nodes) == 0:
            new_node_id = self.add_node()
            conn_id_start = self.add_connection(in_node, new_node_id)
            conn_id_end = self.add_connection(new_node_id, out_node)

        else:
            raise IndexError("More than one node found matching the connection, there should be no duplicates")

        return [conn_id_start, in_node, new_node_id, 1.0], [conn_id_end, new_node_id, out_node, weight]


class Specimen:
    def __init__(self, history, input_size=1, output_size=1, generation=1, id=1):

        if input_size < 1 or output_size < 1:
            raise ValueError(f"{'input_size' if input_size < 1 else 'output_size'} parameter minimum value is 1")

        self.history: GenesHistory = history
        nodes = self.history.nodes_genes
        connection = list()
        for conn in self.history.connections_genes:
            connection.append([conn[0], conn[1], conn[2], 1.0, True])
        self._connections = connection
        self.nodes = np.array([[node_id, 0, sum((1 for x in self._connections if x[2] == node_id))]
                               for node_id, _ in nodes])
        self.input_nodes = tuple(range(input_size))
        base_nodes = input_size + output_size
        self.output_nodes = tuple(range(input_size, base_nodes + 1))
        self.hidden_nodes = tuple(node[0] for node in self._nodes if node[0] > base_nodes)
        self.generation = generation
        self.id = id

    @property
    def nodes(self):
        return self._nodes

    @nodes.setter
    def nodes(self, nodes):
        self._nodes = np.array(nodes, dtype=np.float32)

    @property
    def input_nodes(self):
        return self._input_nodes

    @input_nodes.setter
    def input_nodes(self, nodes):
        self._input_nodes = self.history.input_nodes_ids

    @property
    def output_nodes(self):
        return self._output_nodes

    @output_nodes.setter
    def output_nodes(self, nodes):
        self._output_nodes = nodes

    @property
    def hidden_nodes(self):
        return self._hidden_nodes

    @hidden_nodes.setter
    def hidden_nodes(self, nodes):
        self._hidden_nodes = nodes

    @property
    def connections(self):
        return self._connections

    @connections.setter
    def connections(self, connections):
        self._connections = connections

    @property
    def input_nodes_ids(self):
        return self.history.input_nodes_ids

    @property
    def output_nodes_ids(self):
        return self.history.output_nodes_ids

    @property
    def hidden_nodes_ids(self):
        base_nodes_ids = self.input_nodes_ids + self.output_nodes_ids
        return tuple(node_id for node_id in self._nodes[:, 0] if node_id not in base_nodes_ids)

    def forward(self, in_value, treshold=1e-6):
        treshold *= len(self._output_nodes)
        outputs = len(self._output_nodes)
        old_outputs = 0
        self._nodes[np.isin(self._nodes[:, 0], self._input_nodes), 1] = in_value
        output_nodes = np.isin(self._nodes[:, 0], self._output_nodes)
        connections = tuple((in_node, out_node_raw, weight) for _, in_node, out_node_raw, weight, state
                            in self._connections if state)
        while abs(outputs - old_outputs) > treshold:
            old_outputs = outputs
            outputs = 0.
            r_x = dict()
            for (in_node, out_node_raw, weight) in connections:
                in_nodes = self._nodes[self._nodes[:, 0] == in_node, :]
                out_node = self._nodes[self._nodes[:, 0] == out_node_raw, :][0]
                r_x[out_node[0]] = r_x[out_node[0]] if out_node[0] in r_x else 0.
                for node in in_nodes:
                    value = (node[1] * weight) / out_node[-1]
                    r_x[out_node[0]] += value
                self._nodes[self._nodes[:, 0] == out_node[0], 1] = r_x[out_node[0]]

            outputs = self._nodes[output_nodes].sum()
        return self._nodes[output_nodes, 1]

    def split_connection(self, input_node, output_node, weight):
        conn1, conn2 = self.history.split_connection(input_node, output_node, weight)
        self._connections += [conn1 + [True], conn2 + [True]]
        if conn1[2] not in self._nodes[:, 0]:
            self._nodes = np.concatenate([self._nodes, [[conn1[2], 0., 1.]]])
        if conn1[2] not in self._hidden_nodes:
            self._hidden_nodes = tuple(sorted(self._hidden_nodes + (conn1[2],)))

        for conn_id, in_node, out_node, weight, state in self._connections:

            if in_node == in_node and out_node == output_node:
                self._connections[conn_id][-1] = False
                break

    def add_connection(self, in_node, out_node, weight=1.0):
        conn_id = self.history.add_connection(in_node, out_node)
        self._nodes[self._nodes[:, 0] == out_node, -1] += 1
        self._connections += [[conn_id, in_node, out_node, weight, True]]

    def vizualise(self):
        return specimen_to_graph(self)


class Mutator:
    def __init__(self):
        pass

    def __call__(self, specimen):
        return specimen

    @staticmethod
    def mutation_switch_connection(connections, p):
        for i in range(connections):
            if random.random() < p:
                connections[i][-1] = not connections[i][-1]
        return connections

    @staticmethod
    def mutation_weight_change(connections, p, delta=1.0):
        for i in range(connections):
            if random.random() < p:
                connections[i][-2] += random.uniform(-delta, delta)
        return connections

    @staticmethod
    def mutation_split_connection(specimen, p):
        connections = specimen.connections
        for i in range(connections):
            if random.random() < p:
                specimen.split_connection(*connections[i][1:3])

    @staticmethod
    def mutation_add_connection(specimen, p):
        connections = specimen.connections
        for i in range(connections):
            if random.random() < p:
                specimen.add_connection(*connections[i][1:3], 1.0)

if __name__ == "__main__":
    Specimen(GenesHistory(1, 2))
