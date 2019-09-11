import logging
import random
import re

class Tmessage:
    def __init__(self, plan, agents, active_pm=None, checked_pm=None):
        # for agents which can make multiple actions with different type of block. Not to remake previous actions.
        self.actions = plan
        self.agents = agents
        self.hagent = None
        self.bagents = None
        self.active_pm = active_pm
        self.checked_pm = checked_pm
        self.lagents = set()
        self.lsizes = set()
        self.lblocks = set()
        self.types = ['help_request', 'Approve', 'Broadcast']
        self.greetings = ['Hello ', 'Greetings ', 'Good day ']
        self.questions = ['Can you help to achieve the goal?', 'What can you do in this situation?']
        self.sit = ['The situation is', 'Now, we have']

    def xstr(self, sit):
        if sit is None:
            return ""
        else:
            return sit.name

    def broadcast(self):
        message=random.choice(self.greetings)+"all!!! My name is " +self.agents+  ". I have made a plan and it is: "
        if self.actions and not self.bagents:
            for situation in self.actions:
                message+= situation[1] + " "+ self.xstr(situation[3])+ "; "
            return message
        elif self.bagents:
            return "broadcast to special agents"
        else:
            return "plan doesn't exist"

    def approve(self):
        if isinstance(self.agents, list):
            self.bagents = self.agents
        elif isinstance(self.agents, str):
            self.hagent = self.agents
        else:
            logging.info("wrong amount of agents!")
        if self.bagents:
            self.broadcast()
        message=random.choice(self.greetings)+"all!!! My name is " +self.agents+  ". I have made a plan and it is: "
        if self.actions:
            for situation in self.actions:
                message+= situation[1] + " "+ self.xstr(situation[3])+ "; "
            return message
        else:
            return "plan doesn't exist"
    def save_achievement(self):
        message = random.choice(self.greetings) + "My name is " + self.agents + ". I have made a plan and it is: "
        if self.actions:
            for act in self.actions:
                message+= act[1] + " "+ self.xstr(act[3])+ ";"
                if len(act)>4 and act[4] is not None:
                    message+=str(act[4][0]) +';' + str(act[4][1])+ " && "
            return message
        else:
            return "plan doesn't exist"

def reconstructor(message):
    m = re.search('(?<=My name is )\w+', message)
    agent = m.group(0)
    plan = message.split(":")[1]
    plan = re.sub("I", agent, plan)
    return agent, plan