from core.database import Database

_db = Database(f'{__file__}/../../data/template', override=True)

_matching = {key: value for value, key in _db.execute("""SELECT id, name FROM node_type ORDER BY name""")}


class NodeTypes:
    hidden, input, output = _matching.values()


class Node:
    def __init__(self, db, node_type=None, connection_historical_id=None, node_id=None):
        self._db = db

        if isinstance(node_type, str):
            node_type = getattr(NodeTypes, node_type.lower())

        if node_id:
            res = self._db.execute(f"""
            SELECT id, node_type_id, connection_historical_id  FROM node WHERE id = {node_id} LIMIT 1
            """)
            if not res:
                raise ValueError('No node exists with that id')
            self.id, self.node_type, self.connection_historical = res[0]
        else:
            if not connection_historical_id and not node_type:
                raise ValueError('A node must have a connection_historical_id or a node_type specified')

            if connection_historical_id:
                res = self._db.execute(f"""
                    SELECT id FROM connection_historical WHERE id = {connection_historical_id}
                """)
                if not res:
                    raise ValueError('The given connection_historical_id does not exists')

            node_type = node_type or NodeTypes.hidden
            self._db.execute(f"""
                INSERT INTO node (node_type_id, connection_historical_id)
                    VALUES ({node_type}, {connection_historical_id or "NULL"})
            """)
            res = self._db.execute(f"""
                SELECT id
                FROM node
                WHERE node_type_id = {node_type} AND connection_historical_id = {connection_historical_id or "NULL"}
                ORDER BY id DESC
                LIMIT 1
            """)
            if not res:
                raise ValueError('Incorrect node_type or connection_historical_id given')
            self.id = res[0][0]
            self.node_type = node_type
            self.connection_historical = connection_historical_id


class HistoricalConnection:
    def __init__(self, db, historical_connection_id=None, in_node_id=None, out_node_id=None):
        self._db = db

        if historical_connection_id:
            res = self._db.execute(f"""
            SELECT id, in_node_id, out_node_id 
            FROM connection_historical 
            WHERE id = {historical_connection_id} 
            LIMIT 1
            """)
            if not res:
                raise ValueError('No HistoricalConnection exists with that id')
            self.id, self.in_node, self.out_node = res[0]
        elif in_node_id and out_node_id:
            if in_node_id == out_node_id:
                raise ValueError("in_node_id and out_node_id must be different nodes")

            res = self._db.execute(f"""
            SELECT id, in_node_id, out_node_id  
                FROM connection_historical 
                WHERE in_node_id = {in_node_id} AND out_node_id = {out_node_id}
                LIMIT 1
            """)
            if res:
                self.id, self.in_node, self.out_node = res[0]
            else:
                self._db.execute(f"""
                INSERT INTO connection_historical (in_node_id, out_node_id)
                    VALUES ({in_node_id}, {out_node_id})
                """)
                res = self._db.execute(f"""
                    SELECT id
                    FROM connection_historical
                    WHERE in_node_id = {in_node_id} AND out_node_id = {out_node_id}
                    ORDER BY id DESC
                    LIMIT 1
                """)
                if not res:
                    raise ValueError("Incorrect values for in_node_id and/or out_node_id parameters")
                self.id = res[0][0]
                self.in_node = in_node_id
                self.out_node = out_node_id
        else:
            raise ValueError(
                    "A Connection must be given either an existing historical_connection_id or in and out_node_id")


class Connection(HistoricalConnection):
    def __init__(self, db, historical_connection_id=None, in_node_id=None, out_node_id=None,
                 genotype_id=None, connection_id=None, weight=None, is_enabled=None):
        self._db = db
        conn_id = None
        if not connection_id and not genotype_id:
            raise ValueError("Must specify a genotype_id or a connection_id")

        if connection_id:
            res = self._db.execute(f"""
            SELECT id, genotype_id, weight, is_enabled, historical_id
            FROM connection
            WHERE id = {connection_id}
            ORDER BY id DESC
            LIMIT 1
            """)
            if not res:
                raise ValueError("Specified connection_id doesn't exist")
            conn_id, self.genotype_id, self._weight, self._is_enabled, historical_connection_id = res[0]
        super().__init__(db, historical_connection_id, in_node_id, out_node_id)
        self.historical_id = int(self.id)
        self.id = conn_id

        if not connection_id:
            res = self._db.execute(f"""
            SELECT id
            FROM genotype
            WHERE id = {genotype_id}
            ORDER BY id DESC
            LIMIT 1
            """)
            if not res:
                raise ValueError("Specified genotype_id doesn't exist")

            res = self._db.execute(f"""
            SELECT id, genotype_id, is_enabled, weight
            FROM connection
            WHERE genotype_id = {genotype_id} AND historical_id = {self.historical_id}
            ORDER BY id DESC
            LIMIT 1
            """)

            if res:
                self.id, self.genotype_id, self._is_enabled, self._weight = res[0]
                if is_enabled:
                    self.is_enabled = is_enabled
                if weight:
                    self.weight = weight
            else:
                is_enabled = is_enabled if is_enabled is not None else True
                weight = weight if weight is not None else 1.0
                self._db.execute(f"""
                INSERT INTO connection (historical_id, genotype_id, is_enabled, weight)
                    VALUES ({self.historical_id}, {genotype_id}, {is_enabled}, {weight}) 
                """)

                res = self._db.execute(f"""
                SELECT id
                FROM connection
                WHERE (historical_id = {self.historical_id} 
                        AND genotype_id = {genotype_id} 
                        AND is_enabled = {"TRUE" if is_enabled else "FALSE"} 
                        AND weight = {weight})
                ORDER BY id DESC
                LIMIT 1
                """)

                self.id = res[0][0]
                self._weight = weight
                self._is_enabled = is_enabled
                self.genotype_id = genotype_id

    @property
    def is_enabled(self):
        return self._is_enabled

    @is_enabled.setter
    def is_enabled(self, value: bool):
        self._db.execute(f"""
        UPDATE connection
            SET is_enabled = {"TRUE" if value else "FALSE"}
        WHERE id = {self.id}
        """)
        self._is_enabled = value

    @property
    def weight(self):
        return self._weight

    @weight.setter
    def weight(self, value: float):
        self._db.execute(f"""UPDATE connection SET weight = {value} WHERE id = {self.id}""")
        self._weight = value


class Genotype:
    def __init__(self, db, genotype_id=None, node_ids=None, connections_dict=None):
        self._db = db

        if not (genotype_id or (node_ids and connections_dict)):
            raise ValueError("Must specify either an existing genotype_id or both node_ids and connections_dict")

        if genotype_id:
            res = self._db.execute(f"""
            SELECT id
            FROM genotype
            WHERE id = {genotype_id}
            ORDER BY id DESC
            LIMIT 1
            """)
            if not res:
                raise ValueError("Specified genotype_id doesn't exist")
            self.id = genotype_id
            res = self._db.execute(f"""
            SELECT connection.id
            FROM connection
            WHERE connection.genotype_id = {genotype_id}
            """)
            self.connection_ids = set((sub_res[0] for sub_res in res))
            res = self._db.execute(f"""
            SELECT node_id
            FROM genotype_node_rel
            WHERE genotype_node_rel.genotype_id = {genotype_id}
            """)
            self.node_ids = set((sub_res[0] for sub_res in res))
        else:
            res = self._db.execute("""
            SELECT MAX(id)
            FROM genotype
            """)
            self.id = (res[0][0] or 0) + 1
            self._db.execute(f"""
            INSERT INTO genotype (id)
                VALUES ({self.id})            
            """)
            node_values = ",\n".join((f"({self.id}, {node_id})" for node_id in sorted(node_ids)))
            self._db.execute(f"""
            INSERT INTO genotype_node_rel (genotype_id, node_id)
                VALUES {node_values} 
            """)
            res = self._db.execute(f"""
            SELECT node_id
            FROM genotype_node_rel
            WHERE genotype_node_rel.genotype_id = {self.id}
            """)
            self.node_ids = set((row[0] for row in res))
            self.connection_ids = set()
            for connection in connections_dict:
                connection.update({'genotype_id': self.id})
                self.connection_ids.add(Connection(self._db, **connection).id)

    @property
    def historical_connection_ids(self):
        connection_ids = ', '.join((str(c_id) for c_id in self.connection_ids))
        res = self._db.execute(f"""
        SELECT historical_id
        FROM connection
        WHERE id IN ({connection_ids})
        """)
        return set((row[0] for row in res))

    def __xor__(self, other):
        if not isinstance(other, Genotype):
            raise TypeError(
                    "Cannot use xor operator between an instance of 'Genotype' and an instance of another class"
            )
        diff_nodes = len(other.node_ids ^ self.node_ids)
        total_nodes = max(len(other.node_ids), len(self.node_ids))
        diff_connections = len(other.historical_connection_ids ^ self.historical_connection_ids)
        total_connections = max(len(other.historical_connection_ids), len(self.historical_connection_ids))
        return (total_nodes + total_connections - diff_nodes - diff_connections) / (total_nodes + total_connections)


class Individual:
    def __init__(self, db, individual_id=None, population_id=None, genotype_id=None, genotype_kwargs=None,
                 specie_id=None, score=None):
        self._db = db
        score = score or 0
        if not individual_id and (not population_id or not (genotype_id or genotype_kwargs)):
            raise ValueError(
                    "Must specify an individual_id, or a population_id and either an a genotype_id or a genotype_kwargs"
            )
        if individual_id:
            res = self._db.execute(f"""
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
                res = self._db.execute(f"""
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
                res = self._db.execute(f"""
                SELECT gen.id AS genotype_id,
                       specie.id AS specie_id
                FROM specie
                INNER JOIN individual AS ind ON specie.id = ind.specie_id
                INNER JOIN genotype AS gen ON ind.genotype_id = gen.id
                WHERE gen.id != {genotype_id} AND ind.population_id = {population_id}
                """)
                if res:
                    best_specie_id = None
                    best_result = min(1., max(0., 1. - self.speciation_treshold))
                    for other_id, specie_id in (row for row in res):
                        other_genotype = Genotype(self._db, genotype_id=other_id)
                        genotypes_similarity = genotype ^ other_genotype
                        if genotypes_similarity > best_result:
                            best_specie_id = specie_id
                            best_result = genotypes_similarity
                        if best_result == 1.:  # Best score so no need to continue
                            break
                    specie_id = best_specie_id
            if not specie_id:
                res = self._db.execute("""
                SELECT MAX(id)
                FROM specie
                """)
                specie_id = (res[0][0] or 0) + 1
                self._db.execute(f"""INSERT INTO specie (id) VALUES ({specie_id})""")
            self._db.execute(f"""
            INSERT INTO individual (genotype_id, specie_id, score, population_id)
                VALUES ({genotype_id}, {specie_id}, {score}, {population_id})
            """)
            res = self._db.execute(f"""
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

    @property
    def speciation_treshold(self):
        res = self._db.execute("""
        SELECT speciation_tresh
        FROM model_metadata
        ORDER BY id DESC
        LIMIT 1
        """)
        if not res:
            raise ValueError("There must be at least one row in model_metadata table to fetch data from")
        return res[0][0]

    @property
    def score(self):
        return self._score

    @score.setter
    def score(self, value: int):
        self._db.execute(f"""UPDATE individual SET score = {value} WHERE id = {self.id}""")
        self._score = value


class Population:
    def __init__(self, db, population_id=None, generation_id=None, individual_dicts=None):
        self._db = db
        self.individual_ids = set()
        if not population_id and not (generation_id and individual_dicts):
            raise ValueError("Must specify either a population_id or a generation_id, and individual_dicts")
        if population_id:
            res = self._db.execute(f"""
            SELECT id, generation_id
            FROM population
            WHERE id = {population_id}
            ORDER BY id DESC
            LIMIT 1
            """)
            if not res:
                raise ValueError("Specified population_id doesn't exist")

            self.id, self.generation_id = res[0]
            res = self._db.execute(f"""
            SELECT id
            FROM individual
            WHERE population_id = {self.id}
            """)
            self.individual_ids = set((row[0] for row in res))
            if len(self) != self.model_pop_size:
                raise SystemError("Size inconsistency between loaded individual_ids size and model metadata")

        else:
            pop_size = self.model_pop_size  # Only need to fetch it once

            if pop_size != len(individual_dicts):
                raise SystemError("Size inconsistency between loaded individual_dicts size and model metadata")

            res = self._db.execute(f"""
            SELECT id from generation  WHERE id = {generation_id} ORDER BY id DESC LIMIT 1
            """)
            if not res:
                raise ValueError("Specified generation_id doesn't exist")

            self._db.execute(f"""INSERT INTO population (generation_id) VALUES ({generation_id})""")
            res = self._db.execute(f"""
            SELECT id from population WHERE generation_id={generation_id} ORDER BY id DESC LIMIT 1
            """)
            self.id = res[0][0]
            self.generation_id = generation_id
            for individual_dict in individual_dicts:
                individual_dict["population_id"] = self.id
                self.individual_ids.add(Individual(self._db, **individual_dict).id)

    def __len__(self):
        return len(self.individual_ids)

    @property
    def model_pop_size(self):
        res = self._db.execute("""
        SELECT population_size
        FROM model_metadata
        ORDER BY id DESC
        LIMIT 1
        """)
        if not res:
            raise ValueError("There must be at least one row in model_metadata table to fetch data from")
        return res[0][0]

    @property
    def species(self):
        res = self._db.execute(f"""
        SELECT specie.id
        FROM specie
        INNER JOIN individual AS ind on specie.id = ind.specie_id
        WHERE ind.population_id = {self.id}
        """)
        return set((row[0] for row in res))

    @property
    def best_score(self):
        res = self._db.execute(f"""
        SELECT MAX(score)
        FROM individual
        WHERE individual.population_id = {self.id}
        """)
        return res[0][0] or 0
