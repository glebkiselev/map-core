import re

def tokenizer(tokens):
    for val in tokens:
        yield val

def get_tokens(text):
    return re.findall(':[a-z]*', text)

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

    # while not iter.empty():
    #     next_iter = next(iter)
    #     key = parse_keyword(next_iter.peek())
    #     if key.name == 'requirements':
    #         req = parse_requirements_stmt(next_iter)
    #         domain.requirements = req
    #     elif key.name == 'types':
    #         types = parse_types_stmt(next_iter)
    #         domain.types = types
    #     elif key.name == 'predicates':
    #         pred = parse_predicates_stmt(next_iter)
    #         domain.predicates = pred
    #     elif key.name == 'constants':
    #         const = parse_constants_stmt(next_iter)
    #         domain.constants = const
    #     elif key.name == 'action':
    #         action = parse_action_stmt(next_iter)
    #         domain.actions.append(action)

def parser(domain, usefull):
    iner = {}
    tokens = get_tokens(domain)
    flag = False
    my_token = tokenizer(tokens)
    start_token = next(my_token)
    while not flag:
        try:
            if start_token not in usefull:
                start_token = next(my_token)
                continue
            iner.setdefault(start_token, [])
            part = [''.join(a) for a in domain.split(start_token)[1:]][0]
            if start_token != ':action' and start_token != ':method':
                if start_token != tokens[-1]:
                    next_token = next(my_token)
                    blockcode = '(' + part.split(next_token)[0][:-1]
                    for start, end, depth in tree_sample(blockcode):
                        if depth != 0:
                            iner[start_token].append(blockcode[start:end].strip())
                        elif len(iner[start_token]) == 0:
                            iner[start_token].append(blockcode[start:end].strip())
                    start_token = next_token
                else:
                    for start, end, depth in tree_sample(part):
                        if depth != 0:
                            iner[start_token].append(part[start:end].strip())
                    break
            elif start_token == ':action':
                next_token = next(my_token)
                act_name = part.split(next_token)[0].strip()
                act_dict = {}
                act_dict[act_name] = parser(part, [':parameters',':precondition', ':effect'])
                iner.setdefault('actions', {}).update(act_dict)
                while not next_token == ':action':
                    next_token = next(my_token)
                start_token = next_token
                domain = domain.split(part)[1]
            elif start_token == ':method':
                next_token = next(my_token)
                act_name = part.split(next_token)[0].strip()
                act_dict = {}
                act_dict[act_name] = parser(part, [':parameters',':task', ':subtasks'])
                iner.setdefault('methods', {}).update(act_dict)
                while not next_token == ':method':
                    next_token = next(my_token)
                start_token = next_token
                domain = domain.split(part)[1]
        except StopIteration:
            flag = True

    return iner

if __name__ == '__main__':
    domain = None
    domain_file = '../benchmarks/hierarchical/domain-room.hddl'
    problem_file = '../benchmarks/hierarchical/pRfile01.hddl'
    with open(domain_file, 'r+') as dom:
        domain = dom.read()

    domain = parser(domain, usefull = [':types',':predicates', ':action', ':method'])

