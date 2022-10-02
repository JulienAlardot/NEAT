from unittest import TestCase

from core.activation import sigmoid


class TestActivation(TestCase):
    def test_sigmoid(self):
        self.assertAlmostEqual(0, sigmoid(-10), 6)
        self.assertAlmostEqual(0.5, sigmoid(0), 6)
        self.assertAlmostEqual(1, sigmoid(10), 6)
