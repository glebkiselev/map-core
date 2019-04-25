"""
This file contain functions to parse branches and  leaves

"""

class TypesStmt():
    pass

class PredicatesStmt():
    pass

class TaskStmt():
    pass

class MethodStmt():
    pass

class ActionStmt():
    pass

def parse_types (iter):
    """
    Parse are list of types
    :return: returns the TypesStmt object
    """
    values = []
    return TypesStmt(values)

def parse_predicates (iter):
    """
    Parse a list of predicates
    :return: returns the PredicatesStmt object
    """
    values = []
    return PredicatesStmt(values)

def parse_task (iter):
    """
    Parse task. Tasks contain parameters, preconditions
    and effect groups of statements. Tasks can be realized by one or several
    methods. Tasks are abstract actions.
    :return: returns the TaskStmt object

    """
    values = []
    return TaskStmt(values)

def parse_method (iter):
    """
    Parse method. Methods contain parameters, task, subtasks
    and ordering if subtasks more than one. Methods are lists of actions or subtasks.
    Sometimes methods contain constraints of the current realization.
    :return: returns the MethodStmt object.

    """
    values = {}
    return MethodStmt(values)

def parse_action (iter):
    """
    Actions contain parameters, preconditions and effect groups of
    statements.
    :return: returns the ActionStmt object
    """
    values = {}
    return ActionStmt(values)