
from . import ast_parser
from . import importing

import numpy
import pandas
import itertools


def _apply_description(f, desc, hint, public, hide_details):
    if desc:
        f.__desc = desc

    if hint:
        f.__hint = hint

    f.__public = public
    f.__hide_details = hide_details

def _apply_score(f, max_score, default_score, is_score_public, extra_score):
    f.__is_score_public = is_score_public
    f.__max_score = max_score
    f.__default_score = default_score
    f.__extra_score = extra_score
    f.__scores = []
    f.__get_score = lambda result: 0 if not result else (f.__default_score if not f.__scores else min(f.__scores))
    f.__target_tree = {}
    f.__postrun_hooks = [_execute_ast_search]
    f.__ast_hooks = {}
    f.__pre_ast_hooks = []
    f.__post_ast_hooks = []

def _recursive_ast_search(f, target, tree):
    parser = ast_parser.parse_tree(tree)
    for callback in f.__ast_hooks[target]:
        callback(f, parser)

    # Find subcalls
    modules = importing.user_modules
    for function in parser.calls:
        attr = None
        while len(function) >= 1:
            attr_name = function.pop(0)
            for cur_module in modules:
                attr = getattr(cur_module, attr_name, None)
                if attr in (numpy, pandas, itertools):
                    continue
                
                if attr: 
                    modules = [attr]
                    break
            
            if attr is None:
                break

        try:
            if attr:
                _recursive_ast_search(f, target, get_source_tree(attr))
        except:
            pass

def _execute_ast_search(f):
    for fnc in f.__pre_ast_hooks:
        fnc(f)

    for target, tree in f.__target_tree.items():
        _recursive_ast_search(f, target, tree)

    for fnc in f.__post_ast_hooks:
        fnc(f)

def functionality_test(score, desc, hint, public=True, hide_details=True, is_score_public=False, extra_score=False):
    def wrapper(f):
        _apply_description(f, desc, hint, public, hide_details)
        _apply_score(f, score, score, is_score_public, extra_score)
        return f

    return wrapper

def specificity_test(max_score, default_score, desc, hint, public=True, hide_details=True, is_score_public=False, extra_score=False):
    def wrapper(f):
        _apply_description(f, desc, hint, public, hide_details)
        _apply_score(f, max_score, default_score, is_score_public, extra_score)
        return f

    return wrapper

def _add_static_analysis_target(f, target):
    if target not in f.__target_tree:
        f.__target_tree[target] = ast_parser.get_source_tree(target)
        f.__ast_hooks[target] = []

def _add_ast_hook(f, target, hook, pre=None, post=None):
    _add_static_analysis_target(f, target)
    f.__ast_hooks[target].append(hook)

    if pre is not None:
        f.__pre_ast_hooks.append(pre)

    if post is not None:
        f.__post_ast_hooks.append(post)

def _generic_ast_effect(f, target, score, condition):
    def ast_hook(f, parser):
        if condition(parser):
            f.__scores.append(score)
    
    _add_ast_hook(f, target, ast_hook)


def _ast_effect(f, target, score, condition, and_or='and'):
    pre_condition = []

    def pre_execute(f):
        pre_condition.clear()

    def ast_hook(f, parser):
        result = condition(parser)

        if len(pre_condition) == 0:
            pre_condition.append(result)
        elif and_or == 'and':
            pre_condition[0] = pre_condition[0] and result
        else:
            pre_condition[0] = pre_condition[0] or result

    def post_execute(f):
        if pre_condition[0]:
            f.__scores.append(score)
    
    _add_ast_hook(f, target, ast_hook, pre_execute, post_execute)

def if_call_found(target, call, score):
    def wrapper(f):
        _generic_ast_effect(f, target, score, lambda parser: any(tuple(fnc) == tuple(call) for fnc in parser.calls))
        return f

    return wrapper

def if_call_not_found(target, call, score):
    def wrapper(f):
        _ast_effect(f, target, score, lambda parser: all(tuple(fnc) != tuple(call) for fnc in parser.calls), 'and')
        return f

    return wrapper

def if_loop_found(target, types, score):
    def wrapper(f):
        _generic_ast_effect(f, target, score, lambda parser: (parser.fors and 'for' in types) or (parser.whiles and 'while' in types))
        return f

    return wrapper

def if_any_loop_found(target, score):
    return if_loop_found(target, ('for', 'while'), score)

def if_num_loops_found(target, num, score):
    def wrapper(f):
        pre_condition = [0]

        def pre_execute(f):
            pre_condition[0] = 0

        def ast_hook(f, parser):
            pre_condition[0] += len(parser.fors) + len(parser.whiles)

        def post_execute(f):
            if pre_condition[0] >= num:
                f.__scores.append(score)
        
        _add_ast_hook(f, target, ast_hook, pre_execute, post_execute)

    return wrapper

def if_comprehension_found(target, types, score):
    def wrapper(f):
        _generic_ast_effect(f, target, score, lambda parser: (parser.listComp and 'list' in types) or (parser.setComp and 'set' in types) or (parser.dictComp and 'dict' in types) or (parser.generatorExp and 'generator' in types))
        return f

    return wrapper

def if_any_comprehension_found(target, score):
    return if_comprehension_found(target, ('list', 'set', 'dict', 'generator'), score)

def if_generator_found(target, score):
    def wrapper(f):
        _generic_ast_effect(f, target, score, lambda parser: parser.yields)
        return f

    return wrapper
