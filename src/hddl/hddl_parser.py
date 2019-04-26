import re
import hddl.branch_parser as bch



class Parser:
    def __init__(self, domain_file, problem_file):
        with open(domain_file, 'r+') as dom:
            domain = dom.read()
        with open(problem_file, 'r+') as pr:
            problem = pr.read()
        self.domain = domain
        self.problem = problem
        self.utokens = [':types', ':predicates', ':task', ':method', ':action']

    def get_tokens(self, text):
        return re.findall(':[a-z]*', text)

    def tokenizer(self, tokens):
        for val in tokens:
            yield val

    def ParseDomain(self, descr):
        iner = {}
        tokens = self.get_tokens(descr)
        flag = False
        my_token = self.tokenizer(tokens)
        start_token = next(my_token)
        while not flag:
            try:
                if start_token not in self.utokens:
                    start_token = next(my_token)
                    continue
                next_token = next(my_token)
                while next_token not in self.utokens:
                    next_token = next(my_token)
                    continue
                part = [''.join(el) for el in descr.split(start_token)[1].split(next_token)][0]
                while part[-1] != ')':
                    part = part[:-1]
                else:
                    part = part[:-1]
                parsed = getattr(bch, 'parse_'+start_token[1:])(part)
                if isinstance(parsed, list):
                    iner[start_token[1:]] = parsed
                else:
                    iner.setdefault(start_token[1:], []).append(parsed)

                if next_token != start_token:
                    self.utokens.remove(start_token)
                start_token = next_token


                descr = descr.split(part)[1]

                # if start_token != ':action' and start_token != ':method':
                #     if start_token != tokens[-1]:
                #         next_token = next(my_token)
                #         blockcode = '(' + part.split(next_token)[0][:-1]
                #         for start, end, depth in self.tree_sample(blockcode):
                #             if depth != 0:
                #                 iner[start_token].append(blockcode[start:end].strip())
                #             elif len(iner[start_token]) == 0:
                #                 iner[start_token].append(blockcode[start:end].strip())
                #         start_token = next_token
                #     else:
                #         for start, end, depth in self.tree_sample(part):
                #             if depth != 0:
                #                 iner[start_token].append(part[start:end].strip())
                #         break
                # elif start_token == ':action':
                #     next_token = next(my_token)
                #     act_name = part.split(next_token)[0].strip()
                #     act_dict = {}
                #     act_dict[act_name] = self.ParseDomain(part)
                #     iner.setdefault('actions', {}).update(act_dict)
                #     while not next_token == ':action':
                #         next_token = next(my_token)
                #     start_token = next_token
                #     domain = self.domain.split(part)[1]
                # elif start_token == ':method':
                #     next_token = next(my_token)
                #     act_name = part.split(next_token)[0].strip()
                #     act_dict = {}
                #     act_dict[act_name] = self.ParseDomain(part)
                #     iner.setdefault('methods', {}).update(act_dict)
                #     while not next_token == ':method':
                #         next_token = next(my_token)
                #     start_token = next_token
                #     domain = self.domain.split(part)[1]
            except StopIteration:
                flag = True
        return iner
    def ParseProblem(self, domain):
        pass

if __name__ == '__main__':
    domain = None
    domain_file = '../benchmarks/hierarchical/domain-room.hddl'
    problem_file = '../benchmarks/hierarchical/pRfile01.hddl'


    parser = Parser(domain_file, problem_file)
    domain = parser.ParseDomain(parser.domain)
    problem = parser.ParseProblem(domain)

