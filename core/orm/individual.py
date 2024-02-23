import random
from collections import deque

from core.orm.genotype import Genotype


class Individual:
    def __init__(
            self, db, individual_id=None, population_id=None, genotype_id=None, genotype_kwargs=None,
            specie_id=None, score=None):
        self._db = db
        score = score or 0
        if not individual_id and (not population_id or not (genotype_id or genotype_kwargs)):
            raise ValueError(
                "Must specify an individual_id, or a population_id and either an a genotype_id or a genotype_kwargs"
            )
        if individual_id:
            res = self._db.execute(
                f"""
                SELECT id, genotype_id, specie_id, score, population_id
                FROM individual
                WHERE id = {individual_id}
                ORDER BY id DESC
                LIMIT 1
            """)
            if not res:
                raise ValueError("Specified individual_id doesn't exist")
            self.id, self.genotype_id, self.specie_id, self._score, self.population_id = res[0]
        
        else:
            test_exists = {"population": population_id}
            if specie_id:
                test_exists["specie"] = specie_id
            
            if genotype_id:
                test_exists["genotype"] = genotype_id
            
            for table, value in test_exists.items():
                res = self._db.execute(
                    f"""
                    SELECT id
                    FROM {table}
                    WHERE id = {value}
                    ORDER BY id DESC
                    LIMIT 1
                """)
                if not res:
                    raise ValueError(f"Specified {table}_id doesn't exist")
            
            if not genotype_id and genotype_kwargs:
                genotype_id = Genotype(self._db, **genotype_kwargs).id
            
            if not specie_id:  # Find specie
                genotype = Genotype(self._db, genotype_id=genotype_id)
                res = self._db.execute(
                    f"""
                SELECT gen.id AS genotype_id,
                       specie.id AS specie_id
                FROM specie
                INNER JOIN individual AS ind ON specie.id = ind.specie_id
                INNER JOIN genotype AS gen ON ind.genotype_id = gen.id
                WHERE gen.id != {genotype_id} AND ind.population_id = {population_id}
                """)
                if res:
                    best_specie_id = None
                    best_result = min(1., max(0., 1. - self.speciation_threshold))
                    for other_id, other_specie_id in res:
                        other_genotype = Genotype(self._db, genotype_id=other_id)
                        genotypes_similarity = genotype ^ other_genotype
                        if genotypes_similarity > best_result:
                            best_specie_id = other_specie_id
                            best_result = genotypes_similarity
                        if best_result == 1.:  # Best score so no need to continue
                            break
                    specie_id = best_specie_id
            if not specie_id:
                specie_id = Specie(self._db).id
            self._db.execute(
                f"""
            INSERT INTO individual (genotype_id, specie_id, score, population_id)
                VALUES ({genotype_id}, {specie_id}, {score}, {population_id})
            """)
            res = self._db.execute(
                f"""
            SELECT id
            FROM individual
            WHERE ( genotype_id = {genotype_id}
                AND specie_id = {specie_id}
                AND score = {score}
                AND population_id = {population_id}
                )
            ORDER BY id DESC
            LIMIT 1
            """)
            
            self.id = res[0][0]
            self.population_id = population_id
            self._score = score
            self.specie_id = specie_id
            self.genotype_id = genotype_id
    
    def __add__(self, other):
        if not isinstance(other, Individual):
            raise TypeError(
                "Cannot use and operator between an instance of 'Individual' and an instance of another class"
            )
        if self._db != other._db:
            raise SystemError("Cannot mix databases when reproducing Individuals")
        db = self._db
        population_id = max(self.population_id, other.population_id)
        specie_id = None if self.specie_id != other.specie_id else self.specie_id
        node_ids = set()
        connection_dicts = []
        
        self_genotype = Genotype(db, self.genotype_id)
        other_genotype = Genotype(db, other.genotype_id)
        
        inner_hist_conn_ids = self_genotype.historical_connection_ids & other_genotype.historical_connection_ids
        outer_hist_conn_ids = self_genotype.historical_connection_ids | other_genotype.historical_connection_ids
        hist_conn_ids = set(inner_hist_conn_ids)
        
        for conn_id in (outer_hist_conn_ids - inner_hist_conn_ids):
            if bool(round(random.random())):
                hist_conn_ids.add(conn_id)
        
        connections_data = self._db.execute(
            f"""
        SELECT ch.id, ch.in_node_id, ch.out_node_id, conn_1.weight, conn_1.is_enabled, conn_2.weight, conn_2.is_enabled
            FROM connection_historical AS ch
            LEFT JOIN connection AS conn_1 ON ch.id = conn_1.historical_id
            LEFT OUTER JOIN connection AS conn_2 ON ch.id = conn_2.historical_id
            WHERE ( ch.id IN {tuple(hist_conn_ids)}
                AND conn_1.genotype_id = {self_genotype.id}
                AND conn_2.genotype_id = {other_genotype.id}
                )
        """)
        
        for row in connections_data:
            hist_conn_id, in_node_id, out_node_id, self_weight, self_enabled, other_weight, other_enabled = row
            node_ids |= {in_node_id, out_node_id}
            if bool(round(random.random())):
                weight = self_weight
                is_enabled = self_enabled
            else:
                weight = other_weight
                is_enabled = other_enabled
            
            connection_dicts.append(
                {
                    'historical_connection_id': hist_conn_id,
                    'weight': weight,
                    'is_enabled': is_enabled,
                })
        
        return {
            "db": db,
            "individual_id": None,
            "population_id": population_id,
            "genotype_id": None,
            "genotype_kwargs": {
                'node_ids': node_ids,
                'connection_dicts': tuple(connection_dicts),
                "parent_genotype_ids": {self_genotype.id, other_genotype.id},
            },
            "specie_id": specie_id,
            "score": None,
        }
    
    @property
    def speciation_threshold(self):
        res = self._db.execute(
            """
        SELECT speciation_tresh
        FROM model_metadata
        ORDER BY id DESC
        LIMIT 1
        """)
        if not res:
            raise ValueError("There must be at least one row in model_metadata table to fetch data from")
        return res[0][0]
    
    @property
    def score_raw(self):
        return self._score
    
    @property
    def score(self):
        res = self._db.execute(
            f"""
            SELECT COUNT(individual.id)
            FROM individual
            WHERE individual.specie_id = {self.specie_id}
        """)[0][0]
        return self._score // res
    
    @score.setter
    def score(self, value: int):
        self._db.execute(f"""UPDATE individual SET score = {value} WHERE id = {self.id}""")
        self._score = value


class Specie:
    def __init__(self, db, specie_id=None):
        self._db = db
        if specie_id:
            res = self._db.execute(
                f"""
            SELECT id
            FROM specie
            WHERE id = {specie_id}
            ORDER BY id DESC
            LIMIT 1
            """)
            if not res:
                raise ValueError("Specified specie_id doesn't exist")
            self.id = res[0][0]
        else:
            self._db.execute("""INSERT INTO specie DEFAULT VALUES""")
            res = self._db.execute("""SELECT MAX(id) FROM specie""")
            self.id = res[0][0]
    
    @property
    def best_score(self):
        res = self._db.execute(
            f"""
        SELECT MAX(score)
        FROM individual
        WHERE individual.specie_id = {self.id}
        """)
        return res[0][0] or 0
    
    @property
    def individual_ids(self):
        res = self._db.execute(
            f"""
        SELECT id
        FROM individual
        WHERE individual.specie_id = {self.id}
        """)
        return set((row[0] for row in res))
    
    def get_sorted_individuals(self, desc=True):
        res = self._db.execute(
            f"""
            SELECT id, score
            FROM individual
            WHERE individual.specie_id = {self.id}
            ORDER BY score {'DESC' if desc else ''}
        """)
        return tuple((row[0] for row in res)), tuple((row[1] for row in res))
    
    def get_culled_individuals(self):
        cull_rate = self._db.execute(
            """
            SELECT specie_cull_rate
            FROM model_metadata
            ORDER BY id
            LIMIT 1
        """)[0][0]
        individuals, scores = self.get_sorted_individuals()
        individuals = individuals[:round(len(individuals) * cull_rate)]
        return individuals, scores[:len(individuals)]
    
    @property
    def score(self):
        scores = self.get_culled_individuals()[1]
        return sum(scores) / len(scores)
    
    def select_individual(self):
        individuals, scores = self.get_culled_individuals()
        individuals = deque(individuals)
        scores = deque(scores)
        total_score = sum(scores)
        r = random.random() * total_score
        current_score = 0
        while current_score < r and individuals and scores:
            individual = individuals.popleft()
            current_score = scores.popleft()
        return individual
    
    def create_newborn(self, species_set):
        species_set = species_set - self.id
        cloning_rate, interspecie_rate = self._db.execute(
            """
            SELECT reproduction_cloning_rate, reproduction_interspecie_rate
            FROM model_metadata
        """)
        
        if random.random() < cloning_rate:
            parent = Genotype(self._db, genotype_id=self.select_individual().genotype_id)
            newborn = parent.get_mutated()
            newborn.update(
                {
                    'parent_genotype_ids': {parent.id, }
                })
            return newborn
        
        parent_2_specie = self
        if random.random() < interspecie_rate:
            parent_2_specie = Specie(self._db, specie_id=species_set.pop())
        parent_1 = self.select_individual()
        parent_2 = parent_2_specie.select_individual()
        while parent_2 == parent_1 and len(self.individual_ids) > 2:
            parent_2 = parent_2_specie.select_individual()
        
        newborn = Individual(self._db, individual_id=parent_1) + Individual(self._db, individual_id=parent_2)
        return newborn['genotype_kwargs']
