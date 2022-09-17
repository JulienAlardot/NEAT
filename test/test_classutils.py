from unittest import TestCase

from core.classutils import HistoricalConnection, Node, NodeTypes
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
