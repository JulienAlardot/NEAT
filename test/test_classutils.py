from unittest import TestCase

from core.classutils import Connection, Genotype, HistoricalConnection, Node, NodeTypes
from core.database import Database


class TestNodeTypes(TestCase):

    def test_attributes(self):
        self.assertEqual(1, NodeTypes.input)
        self.assertEqual(2, NodeTypes.hidden)
        self.assertEqual(3, NodeTypes.output)


class TestNode(TestCase):
    def setUp(self):
        self._db = Database('test/test', override=True)

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
        n1 = Node(self._db, node_type=NodeTypes.input)
        n2 = Node(self._db, node_type=NodeTypes.output)
        hc = HistoricalConnection(self._db, in_node_id=n1.id, out_node_id=n2.id)
        hc2 = HistoricalConnection(self._db, historical_connection_id=hc.id)
        n3 = Node(self._db, connection_historical_id=hc.id)
        self.assertEqual(hc.id, hc2.id)
        self.assertEqual(hc.in_node, hc2.in_node)
        self.assertEqual(hc.out_node, hc2.out_node)
        self.assertEqual(1, n3.connection_historical)


class TestHistoricalConnection(TestCase):
    def setUp(self):
        self._db = Database('test/test', override=True)

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


class TestConnection(TestCase):
    def setUp(self):
        self._db = Database('test/test', override=True)

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

        c1 = Connection(self._db, genotype_id=1, in_node_id=1, out_node_id=2)
        c2 = Connection(self._db, genotype_id=2, in_node_id=1, out_node_id=2)
        self.assertNotEqual(c1.id, c2.id)
        self.assertNotEqual(c1.genotype_id, c2.genotype_id)
        self.assertEqual(c1.historical_id, c2.historical_id)


class TestGenotype(TestCase):

    def setUp(self):
        self._db = Database('test/test', override=True)

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
        gen2 = Genotype(self._db, node_ids={1, 2, }, connections_dict=connections_dict)
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
        gen3 = Genotype(self._db, node_ids={1, 2, 3, 4, 5, 6, 7}, connections_dict=connections_dict2)
        with self.assertRaises(TypeError):
            gen ^ {6, }
        self.assertEqual(1.0, gen ^ gen2)
        self.assertEqual(1 / 3, gen ^ gen3)
