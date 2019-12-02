import importlib
import logging
import multiprocessing
import os
import random
import time
from copy import copy

from mapcore.planning.grounding import pddl_grounding
from mapcore.planning.search.mapsearch import MapSearch
from mapcore.planning.grounding import hddl_grounding
from mapcore.swm.src.agent import Agent


class PlanningAgent(Agent):
    def __init__(self):
        pass

    # Initialization
    def initialize(self, problem, TaskType, backward):
        """
        This function allows agent to be initialized. We do not use basic __init__ to let
        user choose a valid variant of agent. You can take agent with othe abilities.
        :param problem: problem
        :param ref: the dynamic value of plan clarification
        """
        try:
            if TaskType != 'hddl':
                self.name = [el for el, type in problem.objects.items() if type.name == 'agent'][0]
            else:
                self.name = [el for el, type in problem.objects if type == 'agent'][0]
        except Exception:
            self.name = 'I'
        self.problem = problem
        self.solution = []
        self.final_solution = ''
        self.backward = backward
        self.TaskType = TaskType
        super().initialize(self.name)

    # Grounding tasks
    def get_task(self):
        """
        This functions is needed to load swm.
        :return: task - sign representation of the problem.
        """
        logging.info('Grounding start: {0}'.format(self.problem.name))
        signs = self.load_swm(type='classic')
        if self.TaskType == 'hddl':
            task = hddl_grounding.ground(self.problem, self.name, signs)
        else:
            task = pddl_grounding.ground(self.problem, self.name, signs)
        logging.info('Grounding end: {0}'.format(self.problem.name))
        logging.info('{0} Signs created'.format(len(task.signs)))
        return task

    def search_solution(self):
        """
        This function is needed to synthesize all plans, choose the best one and
        save the experience.
        """
        task = self.get_task()
        logging.info('Search start: {0}, Start time: {1}'.format(task.name, time.clock()))
        search = MapSearch(task, self.TaskType, self.backward)
        solutions, goal = search.search_plan()
        if goal:
            task.goal_situation = goal
        file_name = None
        if solutions:
            self.solution = self.sort_plans(solutions)
            if self.backward:
                self.solution = list(reversed(self.solution))
            file_name = task.save_signs(self.solution)
            if file_name:
                logging.info('Agent ' + self.name + ' finished all works')
        else:
            logging.info('Agent' + self.name + ' couldnt find any solution for problem %s' % self.problem.name)
        if not file_name:
            for f in os.listdir(os.getcwd()):
                if f.startswith('wmodel_'):
                    if f.split(".")[0].endswith(self.name) or f.split(".")[0].endswith('agent'):
                        file_name = f
                        break
        file_name = os.getcwd() +'/'+ file_name
        return (self.solution, goal), file_name

    def sort_plans(self, plans):
        logging.info("Agent %s choose the best solution for itself" %self.name)

        minlength = min([len(pl) for pl in plans])
        plans = [plan for plan in plans if len(plan) == minlength]
        busiest = []
        for index, plan in enumerate(plans):
            previous_agent = ""
            agents = {}
            counter = 0
            plan_agents = []
            for action in plan:
                if action[3] not in agents:
                    agents[action[3]] = 1
                    previous_agent = action[3]
                    counter = 1
                    if not action[3] is None:
                        plan_agents.append(action[3].name)
                    else:
                        plan_agents.append(str(action[3]))
                elif not previous_agent == action[3]:
                    previous_agent = action[3]
                    counter = 1
                elif previous_agent == action[3]:
                    counter += 1
                    if agents[action[3]] < counter:
                        agents[action[3]] = counter
            # max queue of acts
            longest = 0
            agent = ""
            for element in range(len(agents)):
                item = agents.popitem()
                if item[1] > longest:
                    longest = item[1]
                    agent = item[0]
            busiest.append((index, agent, longest, plan_agents))
        cheap = []
        alternative = []
        cheapest = []
        longest = 0
        min_agents = 100

        for plan in busiest:
            if plan[2] > longest:
                longest = plan[2]

        for plan in busiest:
            if plan[2] == longest:
                if len(plan[3]) < min_agents:
                    min_agents = len(plan[3])

        for plan in busiest:
            if plan[3][0]:
                if plan[2] == longest and len(plan[3]) == min_agents and "I" in plan[3]:
                    plans_copy = copy(plans)
                    cheap.append(plans_copy.pop(plan[0]))
                elif plan[2] == longest and len(plan[3]) == min_agents and not "I" in plan[3]:
                    plans_copy = copy(plans)
                    alternative.append(plans_copy.pop(plan[0]))
            else:
                plans_copy = copy(plans)
                cheap.append(plans_copy.pop(plan[0]))
        if len(cheap) >= 1:
            cheapest.extend(random.choice(cheap))
        elif len(cheap) == 0 and len(alternative):
            logging.info("There are no plans in which I figure")
            cheapest.extend(random.choice(alternative))

        return cheapest

def agent_activation(agpath, agtype, problem, backward, TaskType, childpipe):
    """
    Function that activate an agent
    :param agent: I
    :return: flag that task accomplished
    """
    logging.basicConfig(level=logging.INFO)
    class_ = getattr(importlib.import_module(agpath), agtype)
    workman = class_()
    workman.initialize(problem, TaskType, backward)
    logging.info('Agent I start planning')
    solution, file_name = workman.search_solution()
    if solution:
        logging.info('Agent I finish planning')
        childpipe.send({workman.name:(solution, file_name)})


class Manager:
    def __init__(self, problem, agpath = 'planning.agent.planning_agent', agtype = 'PlanningAgent', TaskType = 'pddl', backward = False):
        self.problem = problem
        self.solution = []
        self.finished = None
        self.agtype = agtype
        self.agpath = agpath
        self.TaskType = TaskType
        self.backward = backward

    def manage_agent(self):
        """
        Create a separate process for the agent
        :return: the best solution
        """
        try:
            multiprocessing.set_start_method('spawn')
        except RuntimeError:
            pass
        parent_conn, child_conn = multiprocessing.Pipe()
        p = multiprocessing.Process(target=agent_activation, args = (self.agpath, self.agtype, self.problem, self.backward, self.TaskType, child_conn,))
        p.start()
        solution = parent_conn.recv()
        p.join()
        return solution
