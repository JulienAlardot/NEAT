import os
import sqlite3 as sql


class Database:
    def __init__(self, name, override=False):
        name = name + ".sqlite" if not name.endswith('.sqlite') else name
        name = os.path.abspath(name)
        if name in os.listdir(os.path.dirname(__file__)) and not override:
            raise FileExistsError('A database with this name already exists')

        self._filename = name
        self._name = '.'.join(name.split('.')[:-1])
        self._con = self._connect()
        self._cursor = self._create_cursor()

        if override:
            self._clear()
        try:
            self.init_db()
            self._con.commit()
        except sql.OperationalError:
            pass

    def _connect(self):
        return sql.connect(self._filename)

    def _create_cursor(self):
        return self._con.cursor()

    def _clear(self):
        self._cursor.executescript("""
        PRAGMA writable_schema = 1;
        delete from sqlite_master where type in ('table', 'index', 'trigger');
        PRAGMA writable_schema = 0;
        VACUUM;
        PRAGMA INTEGRITY_CHECK;
        PRAGMA foreign_keys = ON;
        """)
        self._con.commit()

    def init_db(self):
        self._cursor.executescript("""
        CREATE TABLE node_type (
            id INTEGER PRIMARY KEY,
            name VARCHAR(6) NOT NULL UNIQUE
            );
            
        INSERT INTO node_type (name)
            VALUES  ('Input'),
                    ('Hidden'),
                    ('Output');
        
        CREATE TABLE node (
            id INTEGER PRIMARY KEY,
            node_type_id INTEGER,
            connection_historical_id INTEGER UNIQUE,
            FOREIGN KEY (node_type_id)
                REFERENCES node_type (id)
                ON DELETE RESTRICT
                ON UPDATE RESTRICT
            );
            
        CREATE TABLE connection_historical (
                id INTEGER PRIMARY KEY,
                in_node_id int NOT NULL,
                out_node_id int NOT NULL,
                FOREIGN KEY (in_node_id)
                    REFERENCES node (id)
                    ON DELETE RESTRICT 
                    ON UPDATE RESTRICT, 
                FOREIGN KEY (out_node_id)
                    REFERENCES node (id)
                    ON DELETE RESTRICT
                    ON UPDATE RESTRICT,
                CHECK (in_node_id != out_node_id)
            );
            
        CREATE TABLE genotype (
            id INTEGER PRIMARY KEY
            );
                
        CREATE TABLE connection (
            id INTEGER PRIMARY KEY,
            historical_id INTEGER NOT NULL,
            genotype_id INTEGER NOT NULL,
            is_enabled BOOLEAN DEFAULT TRUE NOT NULL,
            weight FLOAT DEFAULT 1.0 NOT NULL,
            FOREIGN KEY (historical_id)
                REFERENCES connection_historical (id)
                ON DELETE CASCADE 
                ON UPDATE CASCADE ,
            FOREIGN KEY (genotype_id)
                REFERENCES genotype (id)
                ON DELETE CASCADE
                ON UPDATE CASCADE,
            UNIQUE (historical_id, genotype_id)
            );
        
        CREATE TABLE genotype_node_rel (
            id INTEGER PRIMARY KEY,
            genotype_id INTEGER NOT NULL,
            node_id INTEGER NOT NULL,
            UNIQUE (node_id, genotype_id),
            FOREIGN KEY (genotype_id)
                REFERENCES genotype (id)
                    ON DELETE CASCADE 
                    ON UPDATE CASCADE,
            FOREIGN KEY (node_id)
                REFERENCES node (id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
            );    
        
        CREATE TABLE generation (
            id INTEGER PRIMARY KEY
            );
        
        CREATE TABLE specie (
            id INTEGER PRIMARY KEY
            );
        
        CREATE TABLE population (
            id INTEGER PRIMARY KEY,
            generation_id INTEGER NOT NULL,
            FOREIGN KEY (generation_id)
                REFERENCES generation (id)
                ON DELETE CASCADE
                ON UPDATE CASCADE
            );
        
        CREATE TABLE individual (
            id INTEGER PRIMARY KEY,
            genotype_id INTEGER NOT NULL,
            specie_id INTEGER NOT NULL,
            score INTEGER DEFAULT 0 NOT NULL,
            population_id INTEGER NOT NULL,
            FOREIGN KEY (genotype_id)
                REFERENCES genotype(id)
                ON DELETE CASCADE 
                ON UPDATE CASCADE ,
            FOREIGN KEY (specie_id)
                REFERENCES specie (id)
                ON DELETE CASCADE
                ON UPDATE CASCADE,
            FOREIGN KEY (population_id)
                REFERENCES population (id)
                ON DELETE CASCADE
                ON UPDATE CASCADE
            );
        
        CREATE TABLE individual_population_rel (
            id INTEGER PRIMARY KEY,
            individual_id INTEGER NOT NULL,
            population_id INTEGER NOT NULL,
            UNIQUE (individual_id, population_id),
            FOREIGN KEY (individual_id)
                REFERENCES individual (id)
                    ON DELETE CASCADE 
                    ON UPDATE CASCADE,
            FOREIGN KEY (population_id)
                REFERENCES population (id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
            );
        """)

    def execute(self, query):
        query += '' if query.endswith(';') else ';'
        query = query.replace('!= NULL', 'IS NOT NULL')
        query = query.replace('= NULL', 'IS NULL')
        try:
            res = self._cursor.execute(query)
        except sql.IntegrityError as sql_error:
            raise ValueError from sql_error
        if "INSERT INTO" in query or "UPDATE" in query:
            self._con.commit()
        return res.fetchall()
