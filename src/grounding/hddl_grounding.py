from src.grounding.semnet import Sign
from src.grounding.sign_task import Task

signs = {}
obj_signifs = {}
obj_means = {}


def __add_sign(sname, need_signif = True):
    if sname in signs:
        sign = signs[sname]
    else:
        sign = Sign(sname)
        signs[sname] = sign
        if need_signif:
            obj_signifs[sign] = sign.add_significance()
    return sign


def _ground_predicate(name, signature):
    pred_sign = __add_sign(name, False)
    # if more than 1 description to predicate
    pred_signif = pred_sign.add_significance()
    if len(signature):
        for signa in signature:
            if not signa[0].startswith('?'):
                right = '?' + signa[0]
            else:
                right = signa[0]
            new_obj = __add_sign(signa[1]+right)
            old_type = signs[signa[1]]
            if not [con for con in old_type.out_significances if con.in_sign == new_obj]:
                old_signif = old_type.add_significance()
                connector = obj_signifs[new_obj].add_feature(old_signif)
                old_type.add_out_significance(connector)
            connector = pred_signif.add_feature(obj_signifs[new_obj])
            new_obj.add_out_significance(connector)
    return pred_signif


def _ground_action(name, parameters, preconditions, effect):
    action_sign = __add_sign(name, False)
    act_signif = action_sign.add_significance()
    def __update_significance(predicate, effect = False):
        pred_sign = signs[predicate[0]]
        if len(predicate[1]):
            pred_signs = set()
            pred_signature = []
            for role in predicate[1]:
                role_name = list(filter(lambda x: x[0] == role, parameters))
                pred_signature.extend(role_name)
                if role_name[0][0].startswith('?'):
                    role_sig = role_name[0][1] + role_name[0][0]
                else:
                    role_sig = role_name[0][1] + '?' + role_name[0][0]
                try:
                    pred_signs.add(signs[role_sig])
                except KeyError:
                    role_sign = __add_sign(role_sig)
                    pred_signs.add(role_sign)

            for _, signif in pred_sign.significances.items():
                if signif.get_signs() == pred_signs:
                    connector = act_signif.add_feature(signif, effect=effect)
                    pred_sign.add_out_significance(connector)
                    break
            else:
                pred_signif = _ground_predicate(predicate[0], pred_signature)
                connector = act_signif.add_feature(pred_signif, effect=effect)
                pred_sign.add_out_significance(connector)

    for predicate in preconditions:
        __update_significance(predicate)
    for predicate in effect:
        __update_significance(predicate, effect=True)

    return act_signif

def __ground_single_method(parameters, subtasks, ordering, task, task_parameters, subtask, domain):
    actions = list(filter(lambda x: x.name ==subtask[0], domain['actions']))
    if len(actions):
        action = actions[0]
        subtask_parameters = []
        for param1 in subtask[1]:
            for param2 in parameters:
                if param1 == param2[0]:
                    subtask_parameters.append(param2)
        change = []
        used = []
        for param1 in subtask_parameters:
            for param2 in action.parameters:
                if param1[1] == param2[1]:
                    if param1[0] != param2[0] and action.parameters.index(param2) not in used:
                        change.append((param2[0], param1[0]))
                        used.append(action.parameters.index(param2))
                        break
        preconditions = []
        effect = []
        for predicate in action.preconditions:
            new_predicate = [predicate[0], []]
            for signa in predicate[1]:
                for pair in change:
                    if signa == pair[0]:
                        new_predicate[1].append(pair[1])
                        break
                else:
                    new_predicate[1].append(signa)
            preconditions.append(new_predicate)
        for predicate in action.effect:
            new_predicate = [predicate[0], []]
            for signa in predicate[1]:
                for pair in change:
                    if signa == pair[0]:
                        new_predicate[1].append(pair[1])
                        break
                else:
                    new_predicate[1].append(signa)
            effect.append(new_predicate)
        signif = _ground_action(subtask[0], parameters, preconditions, effect)
    else:
        methods = list(filter(lambda x: x.task == subtask[0], domain['methods']))
        if len(methods):
            old_method = methods[0]
            change = []
            for param1 in subtask[1]:
                for param2 in old_method.task_parameters:
                    if subtask[1].index(param1) == old_method.task_parameters.index(param2) and param1 != param2:
                        change.append((param2, param1))
            old_params = []
            for param2 in old_method.parameters:
                for param1 in change:
                    if param2[0] == param1[0]:
                        old_params.append((param1[1], param2[1]))
                        break
                else:
                    old_params.append(param2)
            old_subtasks = {}
            for tnum, stask in old_method.subtasks.items():
                stask_signa = []
                for param1 in stask[1]:
                    for param2 in change:
                        if param1 == param2[0]:
                            stask_signa.append(param2[1])
                            break
                    else:
                        stask_signa.append(param1)
                old_subtasks[tnum] = (stask[0], stask_signa)
            old_t_param = []
            for param1 in old_method.task_parameters:
                for param2 in change:
                    if param1 == param2[0]:
                        old_t_param.append(param2[1])
                        break
                else:
                    old_t_param.append(param1)
            signif = __ground_method(old_params, old_subtasks, old_method.ordering, old_method.task, old_t_param, domain)

    return signif

def __ground_method(parameters, subtasks, ordering, task, task_parameters, domain):
    task = signs[task]
    stasks = {}
    for tasknum, subtask in subtasks.items():
        subtask_sign = signs[subtask[0]]
        subtask_params = set()
        for param in subtask[1]:
            for param2 in parameters:
                if param2[0].endswith(param):
                    #param_descr = list(filter(lambda x: x[0].endswith(param), parameters))[0]
                    subtask_params.add(param2[1] + param2[0])
                    break
        for _, signif in subtask_sign.significances.items():
            chains = signif.spread_down_activity('significance', 5)
            signif_roles = set([chain[-2].sign.name for chain in chains])
            if subtask_params <= signif_roles:
                stasks[tasknum] = signif
                break
        else:
            signif = __ground_single_method(parameters, subtasks, ordering, task, task_parameters, subtask, domain)
            stasks[tasknum] = signif
    if len(stasks) == 1:
        signif = stasks['task0']
        task_signif = task.add_significance()
        connector = task_signif.add_feature(signif)
        signif.sign.add_out_significance(connector)
    else:
        task_signif = task.add_significance()
        for task in ordering:
            signif = stasks[task]
            connector = task_signif.add_feature(signif)
            signif.sign.add_out_significance(connector)
    return task_signif



    # # create parameters simular to method
    # parameters = []
    # for _, task in htn.subtasks.items():
    #     for obj in task[1]:
    #         for item in problem['objects']:
    #             if obj == item[0]:
    #                 parameters.append(('?' + obj, item[1]))
    # parameters.extend(htn.parameters)
    # __ground_method(parameters, htn.subtasks, htn.ordering, htn_name, [], domain)


def __ground_htn_subtask(name, args, domain, agent):
    subt_sign = signs[name]
    methods  = [method for method in domain['methods'] if method.task == name]
    change = []
    for method in methods:
        tparams = []
        for e1 in method.task_parameters:
            for e2 in method.parameters:
                if e1 == e2[0]:
                    tparams.append(signs[e2[1]+e2[0]])
                    break
        if len(args) == len(tparams):
            change = list(zip(tparams, [signs[arg].meanings[1] for arg in args]))
            break

    used = set()
    htn = None
    for _, signif in subt_sign.significances.items():
        pm = signif.copy('significance', 'meaning')
        chains = signif.spread_down_activity('significance', 6)
        for chain in chains:
            for pair in change:
                if chain[-2].sign == pair[0] and pair[0] not in used:
                    pm.replace('meaning', pair[0], pair[1])
                    used.add(pair[0])
                    break
            if len(used) == len(change):
                break
        else:
            subt_sign.remove_meaning(pm)

        if pm:
            htn = pm
    if htn:
        htn.replace('meaning', signs['agent?ag'], obj_means[signs['I']])
    else:
        print("Can't find appropriate realization for method - %s" %name)
    return htn


def _ground_htn_predicate(name, signature):
    pred_sign = signs[name]
    pred_im = pred_sign.add_image()
    for element in signature:
        el_sign = signs[element]
        el_image = el_sign.add_image()
        con = pred_im.add_feature(el_image)
        el_sign.add_out_image(con)

    return pred_im


def ground(domain, problem, agent = 'I', exp_signs=None):
    for type, stype in domain['types']:
        stype_sign = __add_sign(stype)
        stype_signif = stype_sign.add_significance()
        type_sign = __add_sign(type)
        connector = stype_signif.add_feature(obj_signifs[type_sign], zero_out=True)
        type_sign.add_out_significance(connector)

    for obj, type in problem['objects']:
        obj_sign = __add_sign(obj)
        obj_means[obj_sign] = obj_sign.add_meaning()
        type_sign = signs[type]
        tp_signif = type_sign.add_significance()
        connector = tp_signif.add_feature(obj_signifs[obj_sign], zero_out=True)
        obj_sign.add_out_significance(connector)

    for predicate in domain['predicates']:
        _ground_predicate(predicate.name, predicate.signature)

    for action in domain['actions']:
        _ground_action(action.name, action.parameters, action.preconditions, action.effect)

    for task in domain['tasks']:
        __add_sign(task.name, False)

    methods = sorted(domain['methods'], key= lambda method: len(method.subtasks))
    for method in methods:
        __ground_method(method.parameters, method.subtasks, method.ordering, method.task, method.task_parameters, domain)

    #Ground Init
    for init in problem['inits']:
        start = __add_sign('*start %s*'%str(problem['inits'].index(init)), False)
        sit_im = start.add_image()
        for predicate in init:
            pred_im = _ground_htn_predicate(predicate.name, predicate.signature)
            connector = sit_im.add_feature(pred_im)
            pred_im.sign.add_out_image(connector)


    #Ground htns to meanings
    for htn in problem['htns']:
        htn_name = 'htn_' + str(problem['htns'].index(htn))
        htn_sign = __add_sign(htn_name, False)
        htn_mean = htn_sign.add_meaning()
        for task in htn.ordering:
            subtask = htn.subtasks[task]
            cm = __ground_htn_subtask(subtask[0], subtask[1], domain, agent)
            connector = htn_mean.add_feature(cm)
            cm.sign.add_out_meaning(connector)
    print()



