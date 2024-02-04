from unittest import TestCase

from core.activation import sigmoid, relu


class TestActivation(TestCase):
    def test_sigmoid(self):
        self.assertAlmostEqual(0, sigmoid(-10), 6)
        self.assertAlmostEqual(0.5, sigmoid(0), 6)
        self.assertAlmostEqual(1, sigmoid(10), 6)
    
    def test_relu(self):
        self.assertEqual(0, relu(0))
        self.assertEqual(1, relu(1))
        self.assertEqual(0, relu(-1))
