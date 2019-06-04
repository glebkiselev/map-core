import logging

import mapcore.grounding.sign_task as st
import random
from mapcore.grounding.semnet import Sign
from copy import copy
import itertools


MAX_CL_LV = 1

class HTNSearch():
    def __init__ (self, signs):
        self.world_model = signs
        self.MAX_ITERATION = 30
        self.exp_acts = []
        self.exp_sits = []
        self.htn = self.world_model['htn_0'].meanings[1]
        self.scenario = self.htn.spread_down_htn_activity_act('meaning', 4)
        self.active_pm = self.world_model['*start 0*'].images[1]
        logging.debug('Start: {0}'.format(self.active_pm.longstr()))

    def search_plan(self):
        self.I_sign, self.I_obj, self.agents = self.__get_agents()
        plans = self._map_iteration(self.active_pm, iteration=0, current_plan=[])
        return plans


    def applicable_search(self, meanings, active_pm):
        applicable_meanings = []
        for agent, cm in meanings:
            result, checked = self._check_activity(cm, active_pm.sign.meanings[1], backward=False)
            if result:
                applicable_meanings.append((agent, checked))
        return applicable_meanings

    def _map_iteration(self, active_pm, iteration, current_plan, prev_state = []):
        # spread down from htn to get  means of included acts
        # find acts to create a plan
        logging.debug('STEP {0}:'.format(iteration))
        logging.debug('\tSituation {0}'.format(active_pm.longstr()))

        if iteration >= len(self.scenario):
            logging.debug('\tMax iteration count')
            return None

        act_matrice = self.scenario[iteration]

        active_chains = active_pm.spread_down_activity('image', 4)
        active_signif = set()

        for chain in active_chains:
            pm = chain[-1]
            active_signif |= pm.sign.spread_up_activity_act('significance', 4)

        chains = []
        for cm in active_signif:
            if cm.sign == act_matrice.sign:
                chains.extend(cm.spread_down_activity('significance', 5))
        merged_chains = []
        for chain in chains:
            for achain in active_chains:
                if chain[-1].sign == achain[-1].sign and len(chain) > 2 and chain not in merged_chains:
                    merged_chains.append(chain)
                    break
        meanings = self._generate_meanings_htn(act_matrice, merged_chains)
        applicable_meanings = self.applicable_search(meanings, active_pm)

        if not applicable_meanings:
            return None
        logging.info("len of curent plan is: {0}. Len of applicable: {1}".format(len(current_plan), len(applicable_meanings)))
        final_plans = []
        for ag_mask, script in applicable_meanings:
            plan = copy(current_plan)
            next_pm = self._time_shift_forward(active_pm.sign.meanings[1], script)
            plan.append((active_pm, script.sign.name, script, ag_mask))
            prev_state.append(active_pm)
            if len(plan) != len(self.scenario):
                recursive_plans = self._map_iteration(next_pm, iteration + 1, plan, prev_state)
                if recursive_plans:
                    final_plans.extend(recursive_plans)
            else:
                final_plans.append(plan)
                plan_actions = [x.sign.name for _, _, x, _ in plan]
                logging.info("len of detected plan is: {0}".format(len(plan)))
                logging.info(plan_actions)

        return final_plans


    def hierarch_acts(self):
        """
        This function implements experience actions search in agent's world model
        :return:
        """
        exp_acts = {}
        for name, sign in self.world_model.items():
            if sign.meanings and sign.images:
                for index, cm in sign.meanings.items():
                    if cm.is_causal():
                        exp_acts.setdefault(sign, {})[index] = cm

        applicable_meanings = {}
        used = {key: {} for key in exp_acts.keys()}
        for agent in self.agents:
            for conn in agent.out_meanings:
                if conn.in_sign in exp_acts and not conn.in_index in used[conn.in_sign]:
                    if conn.in_index in exp_acts[conn.in_sign]:
                        applicable_meanings.setdefault(conn.in_sign, []).append((agent, exp_acts[conn.in_sign][conn.in_index]))
                        used.setdefault(conn.in_sign, {})[conn.in_index] = getattr(conn.in_sign, 'meanings')[conn.in_index]


        for key1, value1 in exp_acts.items():
            for key2, value2 in value1.items():
                if not key2 in used[key1]:
                    applicable_meanings.setdefault(key1, []).append(
                        (None, value2))

        return applicable_meanings

    def hierarchical_exp_search(self, active_pm, check_pm, iteration, prev_state, acts, cur_plan = []):
        """
        create a subplan using images info
        :param script: parametrs to generate plan
        :return:plan
        """
        if not cur_plan:
            logging.info('Clarify experience plan')
        applicable = []
        if self.backward:
            act = acts[-(iteration+1)].sign
        else:
            act = acts[iteration].sign
        finall_plans = []
        plan = copy(cur_plan)

        for agent, cm in [action for action in self.exp_acts[act] if (action[0] is not None and len(action[1].cause))]:
            result, checked = self._check_activity(cm, active_pm.sign.meanings[1], self.backward)
            if result:
                applicable.append((agent, checked))

        if not applicable:
            logging.info('No applicable actions was found')
            return None

        for action in applicable:
            next_pm = self._time_shift_forward(active_pm.sign.meanings[1], action[1], self.backward)
            included_sit = [sit for sit in self.exp_sits if sit.includes('image', next_pm)]
            if included_sit:
                plan.append(
                    (active_pm, action[1].sign.name, action[1], action[0]))
                logging.info('Experience action %s added to plan' % action[1].sign.name)
            else:
                continue
            # if acts:
                # if not self.backward:
                #     acts.pop(0)
                # else:
                #     acts.pop(-1)
            if next_pm.includes('image', check_pm):
                    if plan:
                        finall_plans.extend(plan)
                    else:
                        finall_plans.extend(plan)
                        break
            else:
                plan = self.hierarchical_exp_search(next_pm, check_pm, iteration+1, prev_state, acts, plan)
                if plan:
                    finall_plans.extend(plan)
                    break
        return finall_plans

    def __get_agents(self):
        agent_back = set()
        I_sign = self.world_model['I']
        agent_back.add(I_sign)
        I_objects = [con.in_sign for con in I_sign.out_significances if con.out_sign.name == "I"]
        if I_objects:
            I_obj = I_objects[0]
        else:
            I_obj = None
        return I_sign, I_obj, agent_back

    def _generate_meanings(self, chains):
        def __get_role_index(chain):
            index = 0
            rev_chain = reversed(chain)
            for el in rev_chain:
                if len(el.cause) == 0:
                    continue
                elif len(el.cause) == 1:
                    if len(el.cause[0].coincidences) ==1:
                        index = chain.index(el)
                    else:
                        return index
                else:
                    return index
            return None

        def __get_big_role_index(chain):
            index = None
            for el in chain:
                if len(el.cause) == 1:
                    if len(el.cause[0].coincidences) ==1:
                        index = chain.index(el)
                        break
                else:
                    continue
            if index:
                return index
            return None

        big_replace = {}

        replace_map = {}
        main_pm = None
        for chain in chains:
            role_index = __get_role_index(chain)
            if role_index:
                if not chain[role_index].sign in replace_map:
                    replace_map[chain[role_index].sign] = [chain[-1]]
                else:
                    if not chain[-1] in replace_map[chain[role_index].sign]:
                        replace_map[chain[role_index].sign].append(chain[-1])
            role_index = __get_big_role_index(chain)
            if role_index:
                if not chain[role_index].sign in big_replace:
                    big_replace[chain[role_index].sign] = [chain[role_index + 1]]
                else:
                    if not chain[role_index + 1] in big_replace[chain[role_index].sign]:
                        big_replace[chain[role_index].sign].append(chain[role_index + 1])
                main_pm = chain[0]

        connectors = [agent.out_meanings for agent in self.agents]

        main_pm_len = len(main_pm.cause) + len(main_pm.effect) + 2

        mapped_actions = {}
        for agent_con in connectors:
            for con in agent_con:
                if con.in_sign == main_pm.sign:
                    mapped_actions.setdefault(con.out_sign, set()).add(con.in_sign.meanings[con.in_index])

        new_map = {}
        rkeys = {el for el in replace_map.keys()}
        pms = []

        for agent, lpm in mapped_actions.items():
            for pm in lpm.copy():
                if len(pm.cause) + len(pm.effect) != main_pm_len:
                    lpm.remove(pm)
                    continue
                pm_signs = set()
                pm_mean = pm.spread_down_activity('meaning', 3)
                for pm_list in pm_mean:
                    pm_signs |= set([c.sign for c in pm_list])
                role_signs = rkeys & pm_signs
                if not role_signs:
                    lpm.remove(pm)
                    if not pms:
                        pms.append((agent, pm))
                    else:
                        for _, pmd in copy(pms):
                            if pmd.resonate('meaning', pm):
                                break
                        else:
                            pms.append((agent, pm))
            old_pms = []

            for pm in lpm:
                if len(pm.cause) + len(pm.effect) != main_pm_len:
                    continue
                pm_signs = set()
                pm_mean = pm.spread_down_activity('meaning', 3)
                for pm_list in pm_mean:
                    pm_signs |= set([c.sign for c in pm_list])
                if pm_signs not in old_pms:
                    old_pms.append(pm_signs)
                else:
                    continue
                role_signs = rkeys & pm_signs
                for role_sign in role_signs:
                    new_map[role_sign] = replace_map[role_sign]

                for chain in pm_mean:
                    if chain[-1].sign in big_replace and not chain[-1].sign in new_map :
                        for cm in big_replace.get(chain[-1].sign):
                            if self.world_model['cell?x'] in cm.get_signs() and self.world_model['cell?y'] in cm.get_signs():
                                new_map[chain[-1].sign] = [cm]


                ma_combinations = mix_pairs(new_map)

                for ma_combination in ma_combinations:
                    cm = pm.copy('meaning', 'meaning')
                    breakable = False
                    for role_sign, obj_pm in ma_combination.items():
                        if obj_pm.sign in pm_signs:
                            breakable = True
                            break
                        obj_cm = obj_pm.copy('significance', 'meaning')
                        cm.replace('meaning', role_sign, obj_cm)
                    if breakable:
                        continue

                    if not pms:
                        pms.append((agent, cm))
                    else:
                        for _, pmd in copy(pms):
                            if pmd.resonate('meaning', cm):
                                break
                        else:
                            pms.append((agent, cm))
                if len(old_pms) == 64:
                    break

        return pms

    def _check_activity(self, pm, next_cm, backward = False, prec_search = False):
        if len(pm.cause) and len(pm.effect):
            result = True
        else:
            result = False

        bigger = next_cm.cause
        smaller = self._applicable_events(pm, backward)
        if prec_search: bigger, smaller = smaller, bigger

        for event in smaller:
            for fevent in bigger:
                if event.resonate('meaning', fevent, True):
                    break
            else:
                result = False
                break

        if not result:
            expanded = pm.expand('meaning')
            if not len(expanded.effect) == 0:
                return self._check_activity(expanded, next_cm, backward, prec_search)
            else:
                expanded.sign.remove_meaning(expanded)
                return False, pm
        return result, pm


    def long_relations(self, plans):
        logging.info("Choosing the plan for auction")
        min = len(plans[0])
        for plan in plans:
            if len(plan) < min:
                min = len(plan)
        plans = [plan for plan in plans if len(plan) == min]

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

    def _meta_check_activity(self, active_pm, scripts, prev_pms, iter):
        heuristic = []
        nextact = None
        if iter < len(self.scenario):
            nextact = self.scenario[iter+1]
        for agent, script in scripts:
            estimation = self._time_shift_forward(active_pm.sign.meanings[1], script)
            for prev in prev_pms:
                if estimation.resonate('image', prev, False, False):
                    break
            else:
                counter = 0
                if nextact:
                    for event in self._applicable_events(estimation.sign.meanings[1]):
                        for ce in self._applicable_events(nextact):
                            if event.resonate('meaning', ce):
                                counter += 1
                                break
                else:
                    counter+=1
                heuristic.append((counter, script.sign.name, script, agent))
        if heuristic:
            best_heuristics = max(heuristic, key=lambda x: x[0])
            return list(filter(lambda x: x[0] == best_heuristics[0], heuristic))
        else:
            return None

    def _applicable_events(self, pm, effect = False):
        """
        Search only in events without connecting to agents
        :param pm:
        :param effect:
        :return:
        """
        applicable = []
        if effect:
            search_in_part = pm.effect
        else:
            search_in_part = pm.cause
        for event in search_in_part:
            if len(event.coincidences) == 1:
                flag = False
                for connector in event.coincidences:
                    if connector.out_sign in self.agents:
                        flag = True
                if flag:
                    continue
            applicable.append(event)
        return applicable

    def recursive_files(self, direct, ext):
        """
        Recursive domain search
        :param direct:
        :param ext:
        :return:
        """
        import os
        extfiles = []
        for root, subfolder, files in os.walk(direct):
            for file in files:
                if file.endswith(ext):
                    extfiles.append(os.path.join(root, file))
            for sub in subfolder:
                extfiles.extend(self.recursive_files(os.path.join(root, sub), ext))
            return extfiles

    def _time_shift_forward(self, active_pm, script, backward = False):
        """
        Next situation synthesis
        :param active_pm: meaning of active situation
        :param script: meaning of active action
        :param backward: planning style
        :return:
        """
        next_situation = Sign(st.SIT_PREFIX + str(st.SIT_COUNTER))
        self.world_model[next_situation.name] = next_situation
        pm = next_situation.add_meaning()
        st.SIT_COUNTER += 1
        copied = {}
        for event in active_pm.cause:
            for es in self._applicable_events(script, effect=backward):
                if event.resonate('meaning', es):
                    break
            else:
                pm.add_event(event.copy(pm, 'meaning', 'meaning', copied))
        for event in self._applicable_events(script, effect=not backward):
            pm.add_event(event.copy(pm, 'meaning', 'meaning', copied))
        pm = pm.copy('meaning', 'image')
        return pm

    def _generate_meanings_htn(self, action_meaning, merged_chains):
        def __get_role_index(chain):
            index = 0
            rev_chain = reversed(chain)
            for el in rev_chain:
                if len(el.cause) == 0:
                    continue
                elif len(el.cause) == 1:
                    if len(el.cause[0].coincidences) ==1:
                        index = chain.index(el)
                    else:
                        return index
                else:
                    return index
            return None


        # # Find already changed roles
        changed_roles = {}
        pm_chains = action_meaning.spread_down_activity('meaning', 5)
        for chain in pm_chains:
            for achain in merged_chains:
                if chain[-1].sign == achain[-1].sign and len(chain) > 2:
                    changed_roles.setdefault(chain[-1], set()).add(achain[-3].sign)

        replace_map = {}
        changed_signs = [cm.sign for cm in changed_roles]
        for chain in pm_chains:
            index = __get_role_index(chain)
            if index != 0 and chain[index].sign not in replace_map:
                to_replace = {ch[-1] for ch in merged_chains if ch[-3].sign == chain[index].sign and ch[-1].sign not in changed_signs}
                if to_replace:
                    replace_map.setdefault(chain[index].sign, set()).update(to_replace)

        # connectors = [agent.out_meanings for agent in self.agents]
        # mapped_actions = {}
        # for agent_con in connectors:
        #     for con in agent_con:
        #         if con.in_sign == action_meaning.sign:
        #             mapped_actions.setdefault(con.out_sign, set()).add(con.in_sign.meanings[con.in_index])
        pms = []

        ma_combinations = mix_pairs(replace_map)

        for ma_combination in ma_combinations:
            cm = action_meaning.copy('meaning', 'meaning')
            for role_sign, obj_pm in ma_combination.items():
                obj_cm = obj_pm.copy('significance', 'meaning')
                cm.replace('meaning', role_sign, obj_cm)
            if not pms:
                pms.append((ma_combination[self.world_model['agent?ag']].sign, cm))
            else:
                for _, pmd in copy(pms):
                    if pmd.resonate('meaning', cm):
                        break
                else:
                    pms.append((ma_combination[self.world_model['agent?ag']].sign, cm))

        return pms

def mix_pairs(replace_map):
    """
    mix roles and objects.
    :param replace_map:
    :return:
    """
    new_chain = {}
    elements = []
    merged_chains = []
    used_roles = []
    replace_map = list(replace_map.items())

    def get_role(obj, roles):
        for role in roles:
            if obj in role[1]:
                return role

    for item in replace_map:
        elements.append(item[1])
    elements = list(itertools.product(*elements))
    clean_el = copy(elements)
    for element in clean_el:
        if not len(set(element)) == len(element):
            elements.remove(element)
    for element in elements:
        for obj in element:
            avalaible_roles = [x for x in replace_map if x not in used_roles]
            role = get_role(obj, avalaible_roles)
            if role:
                used_roles.append(role)
                new_chain[role[0]] = obj
        merged_chains.append(new_chain)
        new_chain = {}
        used_roles = []
    return merged_chains












