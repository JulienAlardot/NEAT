from unittest import TestCase

from core.classutils import Node, NodeTypes
from core.database import Database


class TestNodeTypes(TestCase):

    def test_attributes(self):
        self.assertEqual(1, NodeTypes.input)
        self.assertEqual(2, NodeTypes.hidden)
        self.assertEqual(3, NodeTypes.output)


class TestNode(TestCase):
    def setUp(cls):
        cls._db = Database('test/test', override=True)

    def test_init(self):
        with self.assertRaises(ValueError):
            Node(self._db, node_id=1)
        with self.assertRaises(ValueError):
            Node(self._db)
        Node(self._db, node_type=NodeTypes.input)
        Node(self._db, node_type="OUTPUT")
        self.assertEqual(1, Node(self._db, node_id=1).node_type)
        self.assertEqual(3, Node(self._db, node_id=2).node_type)
        self.assertEqual(None, Node(self._db, node_id=1).connection_historical)

        with self.assertRaises(ValueError):
            Node(self._db, connection_historical_id=1)

        self.assertEqual(1, Node(self._db, node_id=3).connection_historical)
