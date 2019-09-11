import importlib
import logging
import multiprocessing
import os
import random
import time
from copy import copy

from planning.grounding import pddl_grounding
from planning.search.mapsearch import MapSearch
from planning.grounding import hddl_grounding
from swm.agent import Agent


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
            self.name = [el[0] for el in problem.objects if el[1] == 'agent'][0]
        except IndexError:
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
        This functions is needed to load world-model.
        :return: task - sign representation of the problem.
        """
        logging.info('Grounding start: {0}'.format(self.problem.name))
        signs = self.load_swm()
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
        if solutions:
            self.solution = self.sort_plans(solutions)
            if self.backward:
                self.solution = list(reversed(self.solution))
            file_name = task.save_signs(self.solution)
            if file_name:
                logging.info('Agent ' + self.name + ' finished all works')
        else:
            logging.info('Agent' + self.name + ' couldnt find any solution for problem %s' % self.problem.name)

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

class Manager:
    def __init__(self, problem, agpath = 'planning.agent.planning_agent', agtype = 'PlanningAgent', TaskType = 'pddl', backward = False):
        self.problem = problem
        self.solution = []
        self.finished = None
        self.agtype = agtype
        self.agpath = agpath
        self.TaskType = TaskType
        self.backward = backward


    def agent_start(self, agent):
        """
        Function that send task to agent
        :param agent: I
        :return: flag that task accomplished
        """
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger("process-%r" % (agent.name))
        logger.info('Agent {0} start planning'.format(agent.name))
        saved = agent.search_solution()
        if saved:
            logger.info('Agent {0} finish planning'.format(agent.name))
            self.finished = True
        return agent.name +' finished'

    def manage_agent(self):
        """
        Create a separate process for the agent
        :return: the best solution
        """
        class_ = getattr(importlib.import_module(self.agpath), self.agtype)
        workman = class_()
        workman.initialize(self.problem, self.TaskType, self.backward)
        multiprocessing.set_start_method('spawn')
        ag = multiprocessing.Process(target=self.agent_start, args = (workman, ))
        ag.start()
        ag.join()
        if self.solution:
            return self.solution
        else:
            time.sleep(1)

        return None