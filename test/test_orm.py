import os.path
from unittest import TestCase, mock

from core.database import Database
from core.orm import (
    Connection, Generation, Genotype, HistoricalConnection, Individual, Node, NodeTypes,
    Population, Specie,
)
from test import NEATBaseTestCase


class TestMetaData(TestCase):
    def setUp(self):
        self._db = Database('test/test', override=True)

    def test_metadata_lacking(self):
        self._db.execute("""INSERT INTO generation DEFAULT VALUES""")
        for node_type in (NodeTypes.input, NodeTypes.output):
            Node(self._db, node_type)
        with self.assertRaises(ValueError):
            ind_dicts = ({
                             'genotype_kwargs': {
                                 "node_ids": {1, 2},
                                 "connections_dict": (
                                     {'in_node_id': 1, 'out_node_id': 2, },)
                             }
                         },)
            Population(self._db, generation_id=1, individual_dicts=ind_dicts)


class TestNodeTypes(TestCase):
    def test_attributes(self):
        self.assertEqual(1, NodeTypes.input)
        self.assertEqual(2, NodeTypes.hidden)
        self.assertEqual(3, NodeTypes.output)


class TestNode(NEATBaseTestCase):
    def test_init(self):
        with self.assertRaises(ValueError):
            Node(self._db, node_id=1)
        with self.assertRaises(ValueError):
            Node(self._db)
        Node(self._db, node_type=NodeTypes.input)
        Node(self._db, node_type="OUTPUT")

        with self.assertRaises(ValueError):
            Node(self._db, connection_historical_id=1)
        self.assertEqual(1, Node(self._db, node_id=1).node_type)
        self.assertEqual(3, Node(self._db, node_id=2).node_type)
        self.assertEqual(None, Node(self._db, node_id=1).connection_historical)

        with self.assertRaises(ValueError):
            Node(self._db, connection_historical_id=1)

        with self.assertRaises(ValueError):
            Node(self._db, node_id=4)

    def test_historical_connection_rel(self):
        node1 = Node(self._db, node_type=NodeTypes.input)
        node2 = Node(self._db, node_type=NodeTypes.output)
        hc = HistoricalConnection(self._db, in_node_id=node1.id, out_node_id=node2.id)
        hconnection2 = HistoricalConnection(self._db, historical_connection_id=hc.id)
        node3 = Node(self._db, connection_historical_id=hc.id)
        self.assertEqual(hc.id, hconnection2.id)
        self.assertEqual(hc.in_node, hconnection2.in_node)
        self.assertEqual(hc.out_node, hconnection2.out_node)
        self.assertEqual(1, node3.connection_historical)


class TestHistoricalConnection(NEATBaseTestCase):
    def test_init(self):
        with self.assertRaises(ValueError):
            HistoricalConnection(self._db, historical_connection_id=1)
        with self.assertRaises(ValueError):
            HistoricalConnection(self._db)
        with self.assertRaises(ValueError):
            HistoricalConnection(self._db, in_node_id=100, out_node_id=200)

        Node(self._db, node_type=NodeTypes.input)
        Node(self._db, node_type="OUTPUT")
        HistoricalConnection(self._db, in_node_id=1, out_node_id=2)

        self.assertEqual(1, HistoricalConnection(self._db, in_node_id=1, out_node_id=2).id)

        with self.assertRaises(ValueError):
            HistoricalConnection(self._db, in_node_id=1, out_node_id=1)


class TestConnection(NEATBaseTestCase):
    def test_init(self):
        self._db.execute("""
        INSERT INTO genotype (id)
            VALUES (1), (2)
        """)

        with self.assertRaises(ValueError):
            Connection(self._db, connection_id=1)

        with self.assertRaises(ValueError):
            Connection(self._db, genotype_id=200)

        with self.assertRaises(ValueError):
            Connection(self._db)
        with self.assertRaises(ValueError):
            Connection(self._db, in_node_id=100, out_node_id=200)

        Node(self._db, node_type=NodeTypes.input)
        Node(self._db, node_type="OUTPUT")
        Connection(self._db, in_node_id=1, out_node_id=2, genotype_id=1)

        self.assertEqual(1, Connection(self._db, in_node_id=1, out_node_id=2, genotype_id=1).id)
        self.assertTrue(Connection(self._db, in_node_id=1, out_node_id=2, genotype_id=1).is_enabled)
        Connection(self._db, in_node_id=1, out_node_id=2, genotype_id=1).is_enabled = False
        Connection(self._db, in_node_id=1, out_node_id=2, genotype_id=1).weight = 0.5

        self.assertFalse(Connection(self._db, in_node_id=1, out_node_id=2, genotype_id=1).is_enabled)
        self.assertEqual(0.5, Connection(self._db, in_node_id=1, out_node_id=2, genotype_id=1).weight)

        with self.assertRaises(ValueError):
            Connection(self._db, in_node_id=1, out_node_id=1, genotype_id=1)

        connection1 = Connection(self._db, genotype_id=1, in_node_id=1, out_node_id=2)
        connection2 = Connection(self._db, genotype_id=2, in_node_id=1, out_node_id=2)
        self.assertNotEqual(connection1.id, connection2.id)
        self.assertNotEqual(connection1.genotype_id, connection2.genotype_id)
        self.assertEqual(connection1.historical_id, connection2.historical_id)


class TestGenotype(NEATBaseTestCase):
    def test_init(self):
        node_i = Node(self._db, 'input')
        node_i2 = Node(self._db, 'input')
        node_i3 = Node(self._db, 'input')
        node_o = Node(self._db, 'output')
        node_o2 = Node(self._db, 'output')
        node_o3 = Node(self._db, 'output')
        node_o4 = Node(self._db, 'output')
        with self.assertRaises(ValueError):
            Genotype(self._db, genotype_id=1)
        with self.assertRaises(ValueError):
            Genotype(self._db)
        with self.assertRaises(ValueError):
            Genotype(self._db, node_ids={1, 2, })
        connections_dict = ({
                                'in_node_id': 1,
                                'out_node_id': 2,
                                'is_enabled': False,
                                'weight': 0.5,
                            },)
        with self.assertRaises(ValueError):
            Genotype(self._db, connections_dict=connections_dict)

        gen = Genotype(self._db, node_ids={1, 2, }, connections_dict=connections_dict)
        self.assertEqual(1, HistoricalConnection(self._db, 1).id)
        self.assertEqual(1, Connection(self._db, historical_connection_id=1, genotype_id=gen.id).id)
        self.assertFalse(Connection(self._db, connection_id=1, genotype_id=gen.id).is_enabled)
        self.assertEqual(0.5, Connection(self._db, connection_id=1, genotype_id=gen.id).weight)
        self.assertEqual(1, Connection(self._db, connection_id=1, genotype_id=gen.id).in_node)
        self.assertEqual(2, Connection(self._db, connection_id=1, genotype_id=gen.id).out_node)
        self.assertEqual(1, gen.id)
        self.assertSetEqual({1, }, gen.connection_ids)
        self.assertSetEqual({1, 2, }, gen.node_ids)
        genode2 = Genotype(self._db, node_ids={1, 2, }, connections_dict=connections_dict)
        connections_dict2 = ({
                                 'in_node_id': 1,
                                 'out_node_id': 2,
                                 'is_enabled': False,
                                 'weight': 0.5,
                             }, {
                                 'in_node_id': 3,
                                 'out_node_id': 7,
                                 'is_enabled': True,
                                 'weight': 1,
                             },)
        genode3 = Genotype(self._db, node_ids={1, 2, 3, 4, 5, 6, 7}, connections_dict=connections_dict2)
        with self.assertRaises(TypeError):
            gen ^ {6, }
        self.assertEqual(1.0, gen ^ genode2)
        self.assertEqual(1 / 3, gen ^ genode3)

    def test_draw(self):
        node_i1 = Node(self._db, 'input')
        node_i2 = Node(self._db, 'input')
        node_h1 = Node(self._db, 'hidden')
        node_h2 = Node(self._db, 'hidden')
        node_o1 = Node(self._db, 'output')
        node_o2 = Node(self._db, 'output')
        connections_dict = ({
                                'in_node_id': node_i1.id,
                                'out_node_id': node_o1.id,
                                'is_enabled': True,
                                'weight': 1,
                            }, {
                                'in_node_id': node_i1.id,
                                'out_node_id': node_o2.id,
                                'is_enabled': True,
                                'weight': 0,
                            }, {
                                'in_node_id': node_i2.id,
                                'out_node_id': node_o1.id,
                                'is_enabled': True,
                                'weight': 10000,
                            }, {
                                'in_node_id': node_i2.id,
                                'out_node_id': node_o2.id,
                                'is_enabled': False,
                                'weight': 10000,
                            }, {
                                'in_node_id': node_i2.id,
                                'out_node_id': node_h1.id,
                                'is_enabled': True,
                                'weight': -10000,
                            }, {
                                'in_node_id': node_h1.id,
                                'out_node_id': node_h2.id,
                                'is_enabled': True,
                                'weight': -1,
                            }, {
                                'in_node_id': node_h2.id,
                                'out_node_id': node_o1.id,
                                'is_enabled': True,
                                'weight': 0.5,
                            }, {
                                'in_node_id': node_h2.id,
                                'out_node_id': node_o2.id,
                                'is_enabled': False,
                                'weight': -0.5,
                            },
        )
        genome = Genotype(self._db, node_ids={node_i1.id, node_i2.id, node_h1.id, node_h2.id, node_o1.id, node_o2.id},
                          connections_dict=connections_dict)
        path = os.path.join(os.path.dirname(__file__), 'test_genome.dot')
        with open(path, 'rt', encoding='utf-8') as test:
            test_check = test.read()
        self.assertMultiLineEqual(test_check, genome.draw())


class TestIndividual(NEATBaseTestCase):
    def test_init(self):
        node1 = Node(self._db, NodeTypes.input)
        node2 = Node(self._db, NodeTypes.output)
        node3 = Node(self._db, NodeTypes.output)
        genotype_kwargs = {
            "node_ids": {node1.id, node2.id, node3.id},
            "connections_dict": ({
                                     'in_node_id': 1,
                                     'out_node_id': 2,
                                     'is_enabled': False,
                                     'weight': 0.5,
                                 }, {
                                     'in_node_id': 1,
                                     'out_node_id': 3,
                                     'is_enabled': True,
                                     'weight': 1,
                                 },)
        }

        with self.assertRaises(ValueError):
            Individual(self._db)
        with self.assertRaises(ValueError):
            Individual(self._db, individual_id=1)
        with self.assertRaises(ValueError):
            Individual(self._db, population_id=1)
        with self.assertRaises(ValueError):
            Individual(self._db, genotype_kwargs=genotype_kwargs)
        self._db.execute("""INSERT INTO generation (id) VALUES (1), (2)""")
        self._db.execute("""INSERT INTO population (id, generation_id) VALUES (1, 1), (2, 2)""")
        ind1 = Individual(self._db, population_id=1, genotype_kwargs=genotype_kwargs)
        self.assertEqual(1, ind1.id)
        self.assertEqual(0, ind1.score)
        self.assertEqual(1, ind1.specie_id)
        self.assertEqual(1, ind1.genotype_id)
        self.assertEqual(1, ind1.population_id)
        ind2 = Individual(self._db, population_id=1, genotype_kwargs=genotype_kwargs, score=10)
        self.assertEqual(2, ind2.id)
        self.assertEqual(10, ind2.score)
        self.assertEqual(1, ind2.specie_id)
        self.assertEqual(2, ind2.genotype_id)
        self.assertEqual(1, ind2.population_id)
        genotype_kwargs_2 = {
            "node_ids": {1, 2},
            "connections_dict": (
                {
                    'in_node_id': 1,
                    'out_node_id': 2,
                    'is_enabled': True,
                    'weight': 1.0,
                },
            ),
        }
        ind3 = Individual(self._db, population_id=1, genotype_kwargs=genotype_kwargs_2)
        self.assertEqual(3, ind3.id)
        self.assertEqual(0, ind3.score)
        self.assertEqual(2, ind3.specie_id)
        self.assertEqual(3, ind3.genotype_id)
        self.assertEqual(1, ind3.population_id)
        ind4 = Individual(self._db, population_id=2, genotype_kwargs={
            "node_ids": {1, 2},
            "connections_dict": (
                {
                    'in_node_id': 1,
                    'out_node_id': 2,
                    'is_enabled': True,
                    'weight': 1.0,
                },
            ),
        })
        self.assertEqual(4, ind4.id)
        self.assertEqual(0, ind4.score)
        self.assertEqual(3, ind4.specie_id)
        self.assertEqual(4, ind4.genotype_id)
        self.assertEqual(2, ind4.population_id)

    @mock.patch('random.random', lambda: 1)
    def test_add(self):
        node1 = Node(self._db, NodeTypes.input)
        node2 = Node(self._db, NodeTypes.output)
        node3 = Node(self._db, NodeTypes.output)
        self._db.execute("""INSERT INTO generation DEFAULT VALUES""")
        self._db.execute("""INSERT INTO population (id, generation_id) VALUES (1,1)""")
        genotype_kwargs = {
            "node_ids": {node1.id, node2.id, node3.id},
            "connections_dict": ({
                                     'in_node_id': 1,
                                     'out_node_id': 2,
                                     'is_enabled': False,
                                     'weight': 0.5,
                                 }, {
                                     'in_node_id': 1,
                                     'out_node_id': 3,
                                     'is_enabled': True,
                                     'weight': 1,
                                 },)
        }
        ind1 = Individual(self._db, genotype_kwargs=genotype_kwargs, population_id=1)
        genotype_kwargs_2 = {
            "node_ids": {node1.id, node2.id},
            "connections_dict": ({
                                     'in_node_id': 1,
                                     'out_node_id': 2,
                                     'is_enabled': True,
                                     'weight': 1,
                                 },)
        }
        ind2 = Individual(self._db, genotype_kwargs=genotype_kwargs_2, population_id=1)
        ind3 = Individual(**(ind1 + ind2))
        self.assertNotEqual(ind2.id, ind3.id)
        self.assertNotEqual(ind2.genotype_id, ind3.genotype_id)
        self.assertEqual(ind2.population_id, ind3.population_id)
        self.assertEqual(ind2.specie_id, ind3.specie_id)
        geno2 = Genotype(self._db, ind2.genotype_id)
        geno3 = Genotype(self._db, ind3.genotype_id)
        self.assertSetEqual(geno2.historical_connection_ids, geno3.historical_connection_ids)
        self.assertSetEqual(set(), geno2.connection_ids & geno3.connection_ids)
        self.assertSetEqual(geno2.node_ids, geno3.node_ids)
        self.assertEqual(1, geno3 ^ geno2)


class TestPopulation(NEATBaseTestCase):
    def test_init(self):
        node1 = Node(self._db, NodeTypes.input)
        node2 = Node(self._db, NodeTypes.input)
        node3 = Node(self._db, NodeTypes.output)
        with self.assertRaises(ValueError):
            Population(self._db, population_id=1)
        with self.assertRaises(ValueError):
            Population(self._db, generation_id=1, individual_dicts=[''] * 100)
        Generation(self._db)
        with self.assertRaises(SystemError):
            Population(self._db, generation_id=1, individual_dicts=[''])
        self._db.execute("""INSERT INTO model_metadata (population_size) VALUES (3)""")
        individual_dicts = (
            {
                'genotype_kwargs': {
                    "node_ids": {node1.id, node2.id, node3.id},
                    "connections_dict": ({
                                             'in_node_id': 1,
                                             'out_node_id': 2,
                                             'is_enabled': False,
                                             'weight': 0.5,
                                         }, {
                                             'in_node_id': 1,
                                             'out_node_id': 3,
                                             'is_enabled': True,
                                             'weight': 1,
                                         },)
                }
            }, {
                'genotype_kwargs': {
                    "node_ids": {node1.id, node2.id, node3.id},
                    "connections_dict": ({
                                             'in_node_id': 1,
                                             'out_node_id': 2,
                                             'is_enabled': False,
                                             'weight': 0.5,
                                         }, {
                                             'in_node_id': 1,
                                             'out_node_id': 3,
                                             'is_enabled': True,
                                             'weight': 1,
                                         },)
                }
            }, {
                'genotype_kwargs':
                    {
                        "node_ids": {1, 2},
                        "connections_dict": (
                            {
                                'in_node_id': 1,
                                'out_node_id': 2,
                                'is_enabled': True,
                                'weight': 1.0,
                            },
                        ),
                    },
                "score": 10
            },
        )
        pop = Population(self._db, generation_id=1, individual_dicts=individual_dicts)
        self.assertEqual(1, pop.id)
        self.assertEqual(3, pop.model_pop_size)
        self.assertSetEqual({1, 2, 3}, pop.individual_ids)
        self.assertSetEqual({1, 2}, pop.species)
        self.assertEqual(1, pop.generation_id)
        self.assertEqual(10, pop.best_score)
        del individual_dicts[-1]["score"]
        Generation(self._db)
        pop2 = Population(self._db, generation_id=2, individual_dicts=individual_dicts)
        self.assertEqual(2, pop2.id)
        self.assertEqual(3, pop2.model_pop_size)
        self.assertSetEqual({4, 5, 6}, pop2.individual_ids)
        self.assertSetEqual({3, 4}, pop2.species)
        self.assertEqual(2, pop2.generation_id)
        self.assertEqual(0, pop2.best_score)


class TestSpecie(NEATBaseTestCase):
    def test_init(self):
        with self.assertRaises(ValueError):
            Specie(self._db, 1)

        node1 = Node(self._db, NodeTypes.input)
        node2 = Node(self._db, NodeTypes.input)
        node3 = Node(self._db, NodeTypes.output)
        self._db.execute("""INSERT INTO model_metadata (population_size) VALUES (3)""")
        Generation(self._db)
        individual_dicts = (
            {
                'genotype_kwargs': {
                    "node_ids": {node1.id, node2.id, node3.id},
                    "connections_dict": ({
                                             'in_node_id': 1,
                                             'out_node_id': 2,
                                             'is_enabled': False,
                                             'weight': 0.5,
                                         }, {
                                             'in_node_id': 1,
                                             'out_node_id': 3,
                                             'is_enabled': True,
                                             'weight': 1,
                                         },)
                }
            }, {
                'genotype_kwargs': {
                    "node_ids": {node1.id, node2.id, node3.id},
                    "connections_dict": ({
                                             'in_node_id': 1,
                                             'out_node_id': 2,
                                             'is_enabled': False,
                                             'weight': 0.5,
                                         }, {
                                             'in_node_id': 1,
                                             'out_node_id': 3,
                                             'is_enabled': True,
                                             'weight': 1,
                                         },)
                }
            }, {
                'genotype_kwargs':
                    {
                        "node_ids": {1, 2},
                        "connections_dict": (
                            {
                                'in_node_id': 1,
                                'out_node_id': 2,
                                'is_enabled': True,
                                'weight': 1.0,
                            },
                        ),
                    },
                "score": 10
            },
        )
        pop = Population(self._db, generation_id=1, individual_dicts=individual_dicts)
        ind1 = Individual(self._db, tuple(sorted(pop.individual_ids))[0])
        ind2 = Individual(self._db, tuple(sorted(pop.individual_ids))[-1])
        specie1 = Specie(self._db, ind1.specie_id)
        specie2 = Specie(self._db, ind2.specie_id)
        self.assertEqual(1, specie1.id)
        self.assertEqual(0, specie1.best_score)
        self.assertSetEqual({1, 2}, specie1.individual_ids)
        self.assertEqual(2, specie2.id)
        self.assertEqual(10, specie2.best_score)
        self.assertSetEqual({3}, specie2.individual_ids)
        self.assertEqual(3, Specie(self._db).id)


class TestGeneration(NEATBaseTestCase):
    def test_init(self):
        with self.assertRaises(ValueError):
            Generation(self._db, 1)

        node1 = Node(self._db, NodeTypes.input)
        node2 = Node(self._db, NodeTypes.input)
        node3 = Node(self._db, NodeTypes.output)
        self._db.execute("""INSERT INTO model_metadata (population_size) VALUES (3)""")
        Generation(self._db)
        individual_dicts = (
            {
                'genotype_kwargs': {
                    "node_ids": {node1.id, node2.id, node3.id},
                    "connections_dict": ({
                                             'in_node_id': 1,
                                             'out_node_id': 2,
                                             'is_enabled': False,
                                             'weight': 0.5,
                                         }, {
                                             'in_node_id': 1,
                                             'out_node_id': 3,
                                             'is_enabled': True,
                                             'weight': 1,
                                         },)
                }
            }, {
                'genotype_kwargs': {
                    "node_ids": {node1.id, node2.id, node3.id},
                    "connections_dict": ({
                                             'in_node_id': 1,
                                             'out_node_id': 2,
                                             'is_enabled': False,
                                             'weight': 0.5,
                                         }, {
                                             'in_node_id': 1,
                                             'out_node_id': 3,
                                             'is_enabled': True,
                                             'weight': 1,
                                         },)
                }
            }, {
                'genotype_kwargs':
                    {
                        "node_ids": {1, 2},
                        "connections_dict": (
                            {
                                'in_node_id': 1,
                                'out_node_id': 2,
                                'is_enabled': True,
                                'weight': 1.0,
                            },
                        ),
                    },
                "score": 10
            },
        )
        pop = Population(self._db, generation_id=1, individual_dicts=individual_dicts)
        gen = Generation(self._db, pop.generation_id)
        self.assertEqual(1, gen.id)
        self.assertSetEqual({1, 2, 3}, gen.individual_ids)
        self.assertEqual(10, gen.best_score)
        self.assertEqual(2, Generation(self._db).id)
