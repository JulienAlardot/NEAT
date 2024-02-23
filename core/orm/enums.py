from core.orm.database import _db

_matching_node_types = dict(_db.execute("""SELECT name, id FROM node_type ORDER BY id"""))
_matching_mutation_types = dict(_db.execute("""SELECT name, id FROM mutation_type ORDER BY id"""))


class NodeTypes:
    """ Dataclass used as an enum for the different node types """
    bias, input, hidden, output = _matching_node_types.values()


class MutationTypes:
    """ Dataclass used as an enum for the different types of connection """
    weight_change, switch_enabled, split_connection, = _matching_mutation_types.values()
