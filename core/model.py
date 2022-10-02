import random

from core.orm import (
    Connection, Generation, Genotype, HistoricalConnection, Individual, Node, NodeTypes,
    Population, Specie,
)


class NEATModel:
    def __init__(self, db):
        self._db = db
        self._start_generation = None
        self._generation = None
        self._population = None
        self._input_node_ids = tuple()
        self._output_node_ids = tuple()

    def _initialize_nodes(self, size_input, size_output):
        self._start_generation = self._generation = self.get_generation()
        self._input_node_ids = []
        self._output_node_ids = []
        self._input_node_ids.append(self.get_node(NodeTypes.bias).id)
        for i in range(size_input):
            self._input_node_ids.append(self.get_node(NodeTypes.input).id)
        for i in range(size_output):
            self._output_node_ids.append(self.get_node(NodeTypes.output).id)

    def _initialize_population(self, pop_size):
        node_ids = set(self._input_node_ids + self._output_node_ids)
        bias_node_id = self.get_node(NodeTypes.bias).id
        connections = ({"in_node_id": bias_node_id, "out_node_id": out_id, "weight": ((random.random() * 2) - 1)}
                       for out_id in self._output_node_ids)
        connections = tuple(connections)
        individual_dict = {'genotype_kwargs': {"node_ids": node_ids, "connection_dicts": connections}}
        individual_dicts = (individual_dict for i in range(pop_size))

        self._population = self.get_population(generation_id=self._generation.id, individual_dicts=tuple(
                individual_dicts))

    def initialize(self, size_input, size_output, pop_size=100, speciation_tresh=0.25):
        self._db.execute(f"""
        INSERT INTO model_metadata (speciation_tresh, population_size) VALUES ({speciation_tresh}, {pop_size})
        """)
        self._initialize_nodes(size_input, size_output)
        self._initialize_population(pop_size)

    #####################
    # classes shortcuts #
    #####################

    def get_connection(self, historical_connection_id=None, in_node_id=None, out_node_id=None, genotype_id=None,
                       connection_id=None, weight=None, is_enabled=None):
        return Connection(self._db, historical_connection_id, in_node_id, out_node_id, genotype_id, connection_id,
                          weight, is_enabled)

    def get_generation(self, generation_id=None):
        return Generation(self._db, generation_id)

    def get_genotype(self, genotype_id=None, node_ids=None, connection_dicts=None):
        return Genotype(self._db, genotype_id, node_ids, connection_dicts)

    def get_hist_connection(self, historical_connection_id=None, in_node_id=None, out_node_id=None):
        return HistoricalConnection(self._db, historical_connection_id, in_node_id, out_node_id)

    def get_individual(self, individual_id=None, population_id=None, genotype_id=None, genotype_kwargs=None,
                       specie_id=None, score=None):
        return Individual(self._db, individual_id, population_id, genotype_id, genotype_kwargs, specie_id, score)

    def get_node(self, node_type=None, connection_historical_id=None, node_id=None):
        return Node(self._db, node_type, connection_historical_id, node_id)

    def get_population(self, population_id=None, generation_id=None, individual_dicts=None):
        return Population(self._db, population_id, generation_id, individual_dicts)

    def get_specie(self, specie_id=None):
        return Specie(self._db, specie_id)
