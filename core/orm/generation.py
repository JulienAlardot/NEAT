class Generation:
    def __init__(self, db, generation_id=None):
        self._db = db
        if generation_id:
            res = self._db.execute(
                f"""
            SELECT id
            FROM generation
            WHERE id = {generation_id}
            ORDER BY id DESC
            LIMIT 1
            """)
            if not res:
                raise ValueError("Specified generation_id doesn't exist")
            self.id = res[0]
        else:
            self._db.execute("""INSERT INTO generation DEFAULT VALUES""")
            res = self._db.execute("""SELECT MAX(id) FROM generation""")
            self.id = res[0][0]

    @property
    def best_score(self):
        res = self._db.execute(
            f"""
        SELECT MAX(score)
        FROM individual
        INNER JOIN population AS pop ON pop.id = individual.population_id
        WHERE pop.generation_id = {self.id}
        """)
        return res[0][0] or 0

    @property
    def individual_ids(self):
        res = self._db.execute(
            f"""
        SELECT individual.id
        FROM individual
        INNER JOIN population AS pop ON pop.id = individual.population_id
        WHERE pop.generation_id = {self.id}
        """)
        return set((row[0] for row in res))
