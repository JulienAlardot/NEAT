from unittest import TestCase

from core.database import Database


class NEATBaseTestCase(TestCase):
    def setUp(self):
        self.maxDiff = 50000
        self._db = Database('test/test', override=True)
        self._db.execute("""INSERT INTO model_metadata DEFAULT VALUES""")


class NEATBaseTestCaseMemory(TestCase):
    def setUp(self):
        self.maxDiff = 50000
        self._db = Database(':memory:', override=True)
        self._db.execute("""INSERT INTO model_metadata DEFAULT VALUES""")
