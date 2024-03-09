from core.orm.generation import Generation
from core.orm.individual import Individual


class Population:
    def __init__(self, db, population_id=None, generation_id=None, individual_dicts=None):
        self._db = db
        self.individual_ids = set()
        if not population_id and not (generation_id and individual_dicts):
            raise ValueError("Must specify either a population_id or a generation_id, and individual_dicts")
        if population_id:
            res = self._db.execute(
                f"""
            SELECT id, generation_id
            FROM population
            WHERE id = {population_id}
            ORDER BY id DESC
            LIMIT 1
            """)
            if not res:
                raise ValueError("Specified population_id doesn't exist")

            self.id, self.generation_id = res[0]
            res = self._db.execute(
                f"""
            SELECT id
            FROM individual
            WHERE population_id = {self.id}
            """)
            self.individual_ids = set((row[0] for row in res))
            if len(self) != self.model_pop_size:
                raise SystemError("Size inconsistency between loaded individual_ids size and model metadata")

        else:
            generation_id = Generation(self._db, generation_id=generation_id).id
            pop_size = self.model_pop_size  # Only need to fetch it once
            if pop_size != len(individual_dicts):
                raise SystemError("Size inconsistency between loaded individual_dicts size and model metadata")
            self._db.execute(f"""INSERT INTO population (generation_id) VALUES ({generation_id})""")
            res = self._db.execute(
                f"""
            SELECT id from population WHERE generation_id={generation_id} ORDER BY id DESC LIMIT 1
            """)
            self.id = res[0]
            self.generation_id = generation_id
            for individual_dict in individual_dicts:
                individual_dict["population_id"] = self.id
                self.individual_ids.add(Individual(self._db, **individual_dict).id)

    def __len__(self):
        return len(self.individual_ids)

    @property
    def model_pop_size(self):
        res = self._db.execute(
            """
        SELECT population_size
        FROM model_metadata
        ORDER BY id DESC
        LIMIT 1
        """)
        if not res:
            raise ValueError("There must be at least one row in model_metadata table to fetch data from")
        return res[0]

    @property
    def species(self):
        res = self._db.execute(
            f"""
        SELECT specie.id
        FROM specie
        INNER JOIN individual AS ind on specie.id = ind.specie_id
        WHERE ind.population_id = {self.id}
        """)
        return set((row[0] for row in res))

    @property
    def best_score(self):
        res = self._db.execute(
            f"""
        SELECT MAX(score)
        FROM individual
        WHERE individual.population_id = {self.id}
        """)
        return res[0][0] or 0
