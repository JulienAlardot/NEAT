import unittest

import numpy as np

from core import genetic as cg


class TestConnGene(unittest.TestCase):
    def test_init(self):
        conn_gene = cg.ConnGene(1, 0.5, 1, 2, True)
        self.assertEqual(1, conn_gene.id)
        self.assertEqual(0.5, conn_gene.weight)
        self.assertEqual(1, conn_gene.in_node)
        self.assertEqual(2, conn_gene.out_node)
        self.assertTrue(conn_gene.enabled)

    def test_input_output(self):
        conn_gene = cg.ConnGene(1, 0.5, 1, 2, True)
        self.assertEqual(0, conn_gene.input)
        self.assertEqual(0, conn_gene.output)
        conn_gene.input = 5
        self.assertEqual(5, conn_gene.input)
        self.assertEqual(2.5, conn_gene.output)


class TestNodeGene(unittest.TestCase):
    def test_init(self):
        node_gene = cg.NodeGene(1, "input")
        self.assertEqual(1, node_gene.id)
        self.assertEqual(0, node_gene.subtype)

    def test_subtype(self):
        node_gene = cg.NodeGene(1, "input")
        self.assertEqual(0, node_gene.subtype)
        node_gene = cg.NodeGene(1, "hidden")
        self.assertEqual(1, node_gene.subtype)
        node_gene = cg.NodeGene(1, "output")
        self.assertEqual(2, node_gene.subtype)
        node_gene = cg.NodeGene(1, "OUTPUT")
        self.assertEqual(2, node_gene.subtype)

        node_gene = cg.NodeGene(1, 0)
        self.assertEqual(0, node_gene.subtype)
        node_gene = cg.NodeGene(1, 1)
        self.assertEqual(1, node_gene.subtype)
        node_gene = cg.NodeGene(1, 2)
        self.assertEqual(2, node_gene.subtype)
        node_gene = cg.NodeGene(1, 2.)
        self.assertEqual(2, node_gene.subtype)

        with self.assertRaises(ValueError):
            cg.NodeGene(1, "test")
        with self.assertRaises(ValueError):
            cg.NodeGene(1, 10)
        with self.assertRaises(TypeError):
            cg.NodeGene(1, [])


class TestGenesHistory(unittest.TestCase):
    def test_init_attributes(self):
        genes_history = cg.GenesHistory(1, 2)
        self.assertEqual(((0, 0), (1, 2), (2, 2)), genes_history.nodes_genes)
        self.assertEqual(((0, 0, 1), (1, 0, 2)), genes_history.connections_genes)
        self.assertEqual((0,), genes_history.input_nodes_ids)
        self.assertEqual(tuple(), genes_history.hidden_nodes_ids)
        self.assertEqual((1, 2), genes_history.output_nodes_ids)

    def test_add_node(self):
        genes_history = cg.GenesHistory(1, 2)
        self.assertEqual(3, genes_history.add_node())
        self.assertEqual(4, genes_history.add_node())
        self.assertEqual(((0, 0), (1, 2), (2, 2), (3, 1), (4, 1)), genes_history.nodes_genes)

    def test_add_connections(self):
        genes_history = cg.GenesHistory(1, 2)
        self.assertEqual(3, genes_history.add_node())

        self.assertEqual(0, genes_history.add_connection(0, 1))
        self.assertEqual(1, genes_history.add_connection(0, 2))

        self.assertEqual(2, genes_history.add_connection(3, 2))
        self.assertEqual(3, genes_history.add_connection(0, 3))

        with self.assertRaises(ValueError):
            genes_history.add_connection(3, 0)

        with self.assertRaises(ValueError):
            genes_history.add_connection(2, 3)

        with self.assertRaises(ValueError):
            genes_history.add_connection(3, 3)

    def test_split_connections(self):
        genes_history = cg.GenesHistory(1, 2)
        self.assertEqual(([2, 0, 3, 1.], [3, 3, 1, 0.5]), genes_history.split_connection(0, 1, 0.5))
        self.assertEqual(([2, 0, 3, 1.], [3, 3, 1, 0.8]), genes_history.split_connection(0, 1, 0.8))
        with self.assertRaises(ValueError):
            genes_history.split_connection(8, 2)
        with self.assertRaises(ValueError):
            genes_history.split_connection(0, 10)

    def test_properties(self):
        genes_history = cg.GenesHistory(1, 2)
        self.assertEqual((0,), genes_history.input_nodes_ids)
        self.assertEqual((1, 2), genes_history.output_nodes_ids)
        genes_history.add_node()
        self.assertEqual((3,), genes_history.hidden_nodes_ids)


class TestSpecimen(unittest.TestCase):
    def test_attributes_init(self):
        hist = cg.GenesHistory(1, 2)
        spec = cg.Specimen(hist)
        with self.assertRaises(ValueError):
            cg.Specimen(history=hist, input_size=0)
        with self.assertRaises(ValueError):
            cg.Specimen(history=hist, output_size=0)
        self.assertEqual((0,), spec.input_nodes)
        self.assertEqual((1, 2), spec.output_nodes)
        self.assertEqual(tuple(), spec.hidden_nodes)
        self.assertIs(hist, spec.history)
        self.assertEqual(np.array([[0, 0, 0], [1, 0, 1], [2, 0, 1]]).all(), spec.nodes.all())
        self.assertEqual((0,), spec.input_nodes_ids)
        self.assertEqual((1, 2), spec.output_nodes_ids)
        self.assertEqual(tuple(), spec.hidden_nodes_ids)

    def test_split_connection(self):
        hist = cg.GenesHistory(1, 2)
        spec = cg.Specimen(hist)
        spec.split_connection(0, 1, 0.5)
        self.assertEqual(np.array([[0, 0, 0], [1, 0, 1], [2, 0, 1], [3, 0, 1]]).all(), spec.nodes.all())
        self.assertEqual((3,), spec.hidden_nodes)

    def test_add_connection(self):
        hist = cg.GenesHistory(1, 2)
        spec = cg.Specimen(hist)
        spec.split_connection(0, 1, 0.5)
        spec.add_connection(3, 2, 0.5)
        self.assertEqual([[0, 0, 1, 1.0, False],
                          [1, 0, 2, 1.0, True],
                          [2, 0, 3, 1.0, True],
                          [3, 3, 1, 0.5, True],
                          [4, 3, 2, 0.5, True]], spec.connections)

        self.assertEqual((3,), spec.hidden_nodes_ids)

    def test_forward(self):
        hist = cg.GenesHistory(1, 2)
        spec = cg.Specimen(hist)
        self.assertEqual(tuple(np.array([1, 1])), tuple(spec.forward(1)))
        self.assertEqual(tuple(np.array([2, 2])), tuple(spec.forward(2)))

    def test_forward_split(self):
        hist = cg.GenesHistory(1, 2)
        spec = cg.Specimen(hist)
        spec.split_connection(0, 1, 0.5)
        self.assertEqual(tuple(np.array([0.5, 1])), tuple(spec.forward(1)))
        self.assertEqual(tuple(np.array([1, 2])), tuple(spec.forward(2)))

    def test_forward_add_connection(self):
        hist = cg.GenesHistory(1, 2)
        spec = cg.Specimen(hist)
        spec.split_connection(0, 1, 0.5)
        spec.add_connection(3, 2, 0.5)
        # spec.vizualise()
        self.assertEqual(tuple(np.array([0.5, 0.75])), tuple(spec.forward(1)))
        self.assertEqual(tuple(np.array([1, 1.5])), tuple(spec.forward(2)))


if __name__ == '__main__':
    unittest.main()
