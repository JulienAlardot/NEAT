import numba as nb
from numba.experimental import jitclass


@jitclass((
        ("type", nb.types.string),
        ("id", nb.types.uint32)
))
class Gene:
    gtype: str
    gid: int

    def __init__(self, gid, gtype):
        self.id = gid
        self.type = gtype


@jitclass((
        ("type", nb.types.string),
        ("subtype", nb.types.string),
        ("id", nb.types.uint32)

))
class NodeGene:
    subtype: str
    type: str
    id: int

    def __init__(self, subtype, gid):
        self.type = "node"
        self.subtype = subtype
        self.id = gid





class GeneRecorder:
    def __init__(self):
        self._nodes: tuple = tuple()
        self._connections: tuple = tuple()

    @property
    def nodes(self):
        return self._nodes

    @property
    def connections(self):
        return self._connections

    def add_gene(self, gene):
        """

        :param Gene gene: new gene to add to the corresponding list
        """
        if gene["type"] not in ("node", "connection"):
            raise ValueError(f"gene['type'] was not node nor connection, but {gene['type']}")
        try:
            if gene["type"] == 'connection':
                _ = self._connections[gene["id"]]
            elif gene["type"] == 'node':
                _ = self._nodes[gene["id"]]
        except IndexError:
            if gene["type"] == 'connection':
                self._connections = tuple(list(self._connections) + [gene])
            elif gene["type"] == 'node':
                self._nodes = tuple(list(self._nodes) + [gene])


@jitclass((
        ("input_size", nb.types.uint16),
        ("output_size", nb.types.uint16),
        # ("_node_genes", nb.types.List(nb.types.uint16)),
        # ("_conn_genes", nb.types.List(nb.types.uint16)),
))
class Estimator:
    input_size: int
    output_size: int
    _node_genes: list
    _conn_genes: list

    def __init__(self, input_size=5, output_size=5):
        self.input_size = input_size)
        self.output_size = output_size
        self._node_genes = [*range(input_size)]
        self._conn_genes = [*range(input_size, input_size + output_size)]


if __name__ == '__main__':
    import sys

    print("test")
    gene = Gene(gid=0, gtype="node")
    nodegene = NodeGene(gid=0, subtype="hidden")
    conngene = ConnGene(gid=0, in_node=1, out_node=2, weight=.5)
    gr = GeneRecorder()
    dlm = Estimator(input_size=5, output_size=5)
    print(sys.getsizeof(gene))
    print(sys.getsizeof(gene))
    print(sys.getsizeof(nodegene))
    print(sys.getsizeof(dlm))
