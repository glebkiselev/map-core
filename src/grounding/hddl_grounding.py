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
            new_obj = __add_sign(signa[1]+signa[0])
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
                role_sig = role_name[0][1] + role_name[0][0]
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

def __ground_single_method(method):
    pass

def __ground_method(method):
    task = signs[method.task]
    subtasks = {}
    for tasknum, subtask in method.subtasks.items():
        subtask_sign = signs[subtask[0]]
        subtask_params = set()
        for param in subtask[1]:
            param_descr = list(filter(lambda x: x[0] == param, method.parameters))[0]
            subtask_params.add(param_descr[1] + param_descr[0])
        for _, signif in subtask_sign.significances.items():
            chains = signif.spread_down_activity('significance', 5)
            signif_roles = set([chain[-2].sign.name for chain in chains])
            if subtask_params <= signif_roles:
                subtasks[tasknum] = signif
            else:
                print()# берем экшн домена и по параметрам меняем последовательность
    if len(method.subtasks) == 1:
        signif = subtasks['task0']
        task_signif = task.add_significance()
        connector = task_signif.add_feature(signif)
        signif.sign.add_out_significance(connector)

    # else:
    #     #TODO search for each signif with spread down activity
    #     pass
    #     print()
        #
        #
        #
        # if method.ordering:
        #     for stask in method.ordering:
        #         signif = subtasks[stask]
        #         connector = task_signif.add_feature(signif)
        #         signif.sign.add_out_significance(connector)
        # else:

def ground(domain, problem, agent = 'I', exp_signs=None):
    for type, stype in domain['types']:
        stype_sign = __add_sign(stype)
        stype_signif = stype_sign.add_significance()
        type_sign = __add_sign(type)
        connector = stype_signif.add_feature(obj_signifs[type_sign], zero_out=True)
        type_sign.add_out_significance(connector)

    for obj, type in problem['objects']:
        obj_sign = __add_sign(obj)
        if obj == 'I':
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
        __ground_method(method)
    print()



