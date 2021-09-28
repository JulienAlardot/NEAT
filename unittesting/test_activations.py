import unittest
from core import activations
import math

class TestActivationsMethods(unittest.TestCase):
    def test_Relu(self):
        self.assertEqual(1, activations.Relu(1))
        self.assertEqual(0, activations.Relu(0))
        self.assertEqual(0, activations.Relu(-1))

    def test_LRelu(self):
        self.assertEqual(1, activations.LRelu(1, epsilon=1e-5))
        self.assertEqual(0, activations.LRelu(0, epsilon=1e-5))
        self.assertEqual(-1e-5, activations.LRelu(-1, epsilon=1e-5))
        self.assertEqual(1, activations.LRelu(1, epsilon=1e-4))
        self.assertEqual(0, activations.LRelu(0, epsilon=1e-4))
        self.assertEqual(-1e-4, activations.LRelu(-1, epsilon=1e-4))

    def test_Elu(self):
        self.assertEqual(1, activations.Elu(1, alpha=1))
        self.assertEqual(0, activations.Elu(0, alpha=1))
        self.assertEqual((math.e ** -1) - 1, activations.Elu(-1, alpha=1))
        self.assertEqual(1, activations.Elu(1, alpha=2))
        self.assertEqual(0, activations.Elu(0, alpha=2))
        self.assertEqual(2 * ((math.e ** -1) - 1), activations.Elu(-1, alpha=2))

    def test_Relu_backward(self):
        self.assertEqual(1, activations.Relu_backward(2))
        self.assertEqual(1, activations.Relu_backward(1))
        self.assertEqual(1, activations.Relu_backward(0))
        self.assertEqual(0, activations.Relu_backward(-1))
        self.assertEqual(0, activations.Relu_backward(-2))

    def test_LRelu_backward(self):
        self.assertEqual(1, activations.LRelu_backward(2, epsilon=1e-3))
        self.assertEqual(1, activations.LRelu_backward(1, epsilon=1e-3))
        self.assertEqual(1, activations.LRelu_backward(0, epsilon=1e-3))
        self.assertEqual(1e-3, activations.LRelu_backward(-1, epsilon=1e-3))
        self.assertEqual(1e-3, activations.LRelu_backward(-2, epsilon=1e-3))