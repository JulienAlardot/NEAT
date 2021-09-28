import unittest
from unittest.mock import Mock

from core import timeit
from test_activations import TestActivationsMethods
from test_genetic import TestConnGene, TestNodeGene, TestGenesHistory, TestSpecimen


class TestCoreFunctions(unittest.TestCase):
    def test_timeit(self):
        def f():
            pass

        out = list()
        mock_stdout = Mock()
        mock_stdout.write = lambda x: out.append(x)
        f = timeit(f, mock_stdout)
        pattern = r"^Execution of <function TestCoreFunctions.test_timeit.<locals>.f at 0x[0-9a-z]{12}> took \d\d+:\d\d:\d\d:\d{3}\.?\d*$"
        f()
        self.assertRegex(out[-1], pattern)


if __name__ == '__main__':
    unittest.main()
