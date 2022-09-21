from unittest import mock

from core.model import NEATModel
from core.orm import NodeTypes
from test import NEATBaseTestCase


class TestNeatModel(NEATBaseTestCase):
    @mock.patch('random.random', new=lambda: 1)
    def test_init(self):
        model = NEATModel(self._db)
        size_input = 10
        size_output = 10
        pop_size = 10
        speciation_tresh = 0.25
        mocked_random = 1
        model.initialize(size_input, size_output, pop_size, speciation_tresh)

        res = self._db.execute("""SELECT id, speciation_tresh, population_size FROM model_metadata""")
        self.assertSequenceEqual(((1, .25, 100), (2, speciation_tresh, pop_size),), res)

        res = self._db.execute("""SELECT id FROM specie""")
        self.assertSequenceEqual(((1,),), res)

        res = self._db.execute("""SELECT id, generation_id FROM population""")
        self.assertSequenceEqual(((1, 1),), res)

        res = self._db.execute("""SELECT id, name FROM node_type""")
        self.assertSequenceEqual(((1, "Input"), (2, "Hidden"), (3, "Output"),), res)

        res = self._db.execute("""SELECT id, node_type_id, connection_historical_id FROM node""")
        self.assertSequenceEqual([(i + 1, NodeTypes.input if i < 10 else NodeTypes.output, None) for i in range(20)],
                                 res)

        res = self._db.execute("""SELECT id, genotype_id, specie_id, score, population_id FROM individual""")
        self.assertSequenceEqual([(i + 1, i + 1, 1, 0, 1) for i in range(10)], res)

        res = self._db.execute("""SELECT id, genotype_id, node_id FROM genotype_node_rel""")
        self.assertSequenceEqual([((20 * i) + j + 1, i + 1, j + 1) for i in range(10) for j in range(20)], res)

        res = self._db.execute("""SELECT id FROM genotype""")
        self.assertSequenceEqual(tuple(((i + 1,) for i in range(10))), res)

        res = self._db.execute("""SELECT id FROM generation""")
        self.assertSequenceEqual(((1,),), res)

        res = self._db.execute("""SELECT id, in_node_id, out_node_id FROM connection_historical""")
        self.assertSequenceEqual([((i * 10) + j + 1, i + 1, j + 11) for i in range(10) for j in range(10)], res)

        res = self._db.execute("""SELECT id, historical_id, genotype_id, is_enabled, weight FROM connection""")
        self.assertSequenceEqual(
                [((i * 100) + j + 1, j + 1, i + 1, True, mocked_random) for i in range(10) for j in range(100)], res)
