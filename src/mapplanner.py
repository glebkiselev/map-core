import logging
import os

from mapcore.pddl.parser import Parser
from mapcore.agent.manager import Manager

SOLUTION_FILE_SUFFIX = '.soln'

import platform

if platform.system() != 'Windows':
    delim = '/'
else:
    delim = '\\'

class MapPlanner():
    def __init__(self, **kwargs):
        kwgs = kwargs['Settings']
        self.agtype = kwgs['agtype']
        self.agpath = kwgs['agpath']
        self.domain, self.problem = self.find_domain(kwgs['path'], kwgs['task'])
        self.refinement = eval(kwgs['refinement_lv'])
        self.backward = eval(kwgs['backward'])
        logging.info('MAP algorithm has started...')

    def search_upper(self, path, file):
        """
        Recursive domain search
        :param path: path to the current task
        :param file: domain name
        :return: full path to the domain
        """
        if not file in os.listdir(path):
            new_path = '/'
            for element in path.split(delim)[1:-2]:
                new_path+=element + delim
            return self.search_upper(new_path, file)
        else:
            return path + delim + file


    def find_domain(self, path, number):
        """
        Domain search function
        :param path: path to current task
        :param number: task number
        :return:
        """
        domain = 'domain.pddl'
        task = 'task' + number + '.pddl'
        if not domain in os.listdir(path):
            domain2 = self.search_upper(path, domain)
            if not domain2:
                raise Exception('domain not found!')
            else:
                domain = domain2
        else:
            domain = path + domain
        if not task in os.listdir(path):
            raise Exception('task not found!')
        else:
            problem = path + task

        return domain, problem

    def _parse(self, domain_file, problem_file):
        """

        :param domain_file:
        :param problem_file:
        :return:
        """
        parser = Parser(domain_file, problem_file)
        logging.info('Parsing Domain {0}'.format(domain_file))
        domain = parser.parse_domain()
        logging.info('Parsing Problem {0}'.format(problem_file))
        problem = parser.parse_problem(domain)
        logging.debug(domain)
        logging.info('{0} Predicates parsed'.format(len(domain.predicates)))
        logging.info('{0} Actions parsed'.format(len(domain.actions)))
        logging.info('{0} Objects parsed'.format(len(problem.objects)))
        logging.info('{0} Constants parsed'.format(len(domain.constants)))
        return problem

    def search_classic(self):
        """
        classic PDDL-based plan search search
        :return: the final solution
        """
        problem = self._parse(self.domain, self.problem)
        logging.info('Agent I started planning')
        manager = Manager(problem, self.agpath, self.agtype, self.refinement, backward=self.backward)
        solution = manager.manage_agent()
        return solution

