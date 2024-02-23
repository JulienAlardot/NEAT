from unittest import TestCase

from core.activation import sigmoid, relu, EPSILON, leaky_relu


class TestActivation(TestCase):
    def test_sigmoid(self):
        """ Tests sigmoid activation function """

        self.assertAlmostEqual(0, sigmoid(-10), 6)
        self.assertAlmostEqual(0.5, sigmoid(0), 6)
        self.assertAlmostEqual(1, sigmoid(10), 6)
    
    def test_relu(self):
        """ Tests ReLu activation function """
        self.assertEqual(0, relu(0))
        self.assertEqual(1, relu(1))
        self.assertEqual(0, relu(-1))
    
    def test_lrelu(self):
        """ Tests Leaky ReLu activation function """
        self.assertEqual(0, leaky_relu(0))
        self.assertEqual(1, leaky_relu(1))
        self.assertEqual(-EPSILON, leaky_relu(-1))
