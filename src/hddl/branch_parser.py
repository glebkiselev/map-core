"""
This file contain functions to parse branches and  leaves

"""

import re

class TypesStmt():
    pass

class PredicatesStmt():
    def __init__(self, name, signature):
        self.name = name[0]
        self.signature = signature
        self.arity = len(signature)

    def __repr__(self):
        predicate = self.name + ' '
        for element in [''.join(sig[0] +' - ' + sig[1]) for sig in self.signature]:
            predicate+=element + ' '
        return predicate[:-1]

class TaskStmt():
    def __init__(self, name, parameters, precondition, effect):
        self.name = name[0]
        self.parameters = parameters
        self.precondition = precondition
        self.effect = effect

    def __repr__(self):
        return self.name

class MethodStmt():
    def __init__(self, name, parameters, task, subtasks, ordering, ):
        self.name = name[0]
        self.parameters = parameters
        self.task = task
        self.subtasks = subtasks
        self.ordering = ordering
        self.abstraction_lv = 0 #depth from method to basic action


    def __repr__(self):
        return self.name

class ActionStmt():
    pass

def parse_types (types):
    """
    Parse are list of types
    :return: returns the list of tuples subtypes and types
    """
    return re.findall('([A-Za-z]*) - ([A-Za-z]*)', types)

def parse_predicates (preds_descr):
    """
    Parse a list of predicates
    :return: returns the list of PredicatesStmt objects
    """
    predicates = []
    for st, end, _ in tree_sample(preds_descr):
        predicate_descr = preds_descr[st:end].strip()
        name = re.findall('^\w+', predicate_descr)
        signatures = re.findall('(\?\w+) - (\w+)', predicate_descr)
        predicate = PredicatesStmt(name, signatures)
        predicates.append(predicate)
    return predicates

def tokenizer(tokens):
    for val in tokens:
        yield val

def parse_task (task):
    """
    Parse task. Tasks contain parameters, preconditions
    and effect groups of statements. Tasks can be realized by one or several
    methods. Tasks are abstract actions.
    :return: returns the TaskStmt object

    """
    ukeys = [':parameters', ':precondition', ':effect']
    name = re.findall('^\w+', task.strip())
    my_token = tokenizer(ukeys)
    flag = False
    start_token = next(my_token)
    definition =[]
    while not flag:
        try:
            next_token = next(my_token)
            part = [''.join(el) for el in task.split(start_token)[1].split(next_token)][0]
            signatures = re.findall('(\?\w+) - (\w+)', part)
            definition.append(signatures)
            start_token = next_token
        except StopIteration:
            part = [''.join(el) for el in task.split(start_token)][1]
            definition.append(re.findall('(\?\w+) - (\w+)', part))
            flag = True

    return TaskStmt(name, definition[0], definition[1], definition[2])

def parse_method (method):
    """
    Parse method. Methods contain parameters, task, subtasks
    and ordering if subtasks more than one. Methods are lists of actions or subtasks.
    Sometimes methods contain constraints of the current realization.
    :return: returns the MethodStmt object.

    """
    ukeys = [':parameters', ':task', ':subtasks', ':ordering']
    name = re.findall('^\w+', method.strip())
    params = [''.join(el) for el in method.split(':parameters')[1].split(':task')][0]
    parameters = re.findall('(\?\w+) - (\w+)', params)
    task = [''.join(el) for el in method.split(':task')[1].split(':subtasks')][0]
    task_name = re.findall('^\w+', task.strip())
    print()





    return MethodStmt(name)

def parse_action (iter):
    """
    Actions contain parameters, preconditions and effect groups of
    statements.
    :return: returns the ActionStmt object
    """
    values = {}
    return ActionStmt(values)

def tree_sample(line, opendelim='(', closedelim=')'):
    stack = []
    for m in re.finditer(r'[{}{}]'.format(opendelim, closedelim), line):
        pos = m.start()
        if line[pos-1] == '\\':
            continue
        c = line[pos]
        if c == opendelim:
            stack.append(pos+1)

        elif c == closedelim:
            if len(stack) > 0:
                prevpos = stack.pop()
                yield prevpos, pos, len(stack)
            else:
                # error
                print("encountered extraneous closing quote at pos {}: '{}'".format(pos, line[pos:] ))
                pass

    if len(stack) > 0:
        for pos in stack:
            print("expecting closing quote to match open quote starting at: '{}'"
                  .format(line[pos-1:]))