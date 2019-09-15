from .get_rabit import get_rabbit_sender

import sys


def _wrap_errors(cls, f):
    def decorated(*a, **kw):
        execution_error = False
        failure_reason = ''

        try:
            f(*a, **kw)
            execution_error = True
        except NotImplementedError as e:
            failure_reason = e.__class__.__name__
        except MemoryError as e:
            org = sys.exc_info()
            f.__details = org[1]
            failure_reason = e.__class__.__name__
        except AssertionError as e:
            org = sys.exc_info()
            f.__details = org[1]
            failure_reason = e.__class__.__name__
        except Exception as e:
            org = sys.exc_info()
            f.__details = org[1]
            failure_reason = 'GenericError'

        return failure_reason, execution_error

    decorated.__test = f
    return decorated

def test_suite(section=''):
    def test_steps(cls, self):
        sender = get_rabbit_sender()

        try:
            as_json = []
            correct = 0
            total = 0
            real_correct = 0
            real_total = len(cls.__tests)

            public_score_total = 0
            public_score_acc = 0
            private_score_total = 0
            private_score_acc = 0

            public_extra_total = 0
            public_extra_acc = 0
            private_extra_total = 0
            private_extra_acc = 0

            for _, test, name in sorted(cls.__tests):
                f = getattr(cls, test)                
                failure_reason, result = f(self)

                for fnc in f.__test.__postrun_hooks:
                    fnc(f.__test)

                real_correct += result
                if f.__test.__public:
                    correct += result
                    total += 1

                    if f.__test.__is_score_public:
                        if f.__test.__extra_score:
                            public_extra_acc += f.__test.__get_score(result)
                            public_extra_total += f.__test.__max_score
                        else:
                            public_score_acc += f.__test.__get_score(result)
                            public_score_total += f.__test.__max_score

                if f.__test.__extra_score:
                    private_extra_acc += f.__test.__get_score(result)
                    private_extra_total += f.__test.__max_score
                else:
                    private_score_acc += f.__test.__get_score(result)
                    private_score_total += f.__test.__max_score

                as_json.append({
                        'name': name,
                        'result': result,
                        'failure_reason': failure_reason,
                        'public': f.__test.__public,
                        'hide_details': f.__test.__hide_details,
                        'details': str(getattr(f.__test, '__details', None)),
                        'desc': getattr(f.__test, '__desc', ':('),
                        'hint': getattr(f.__test, '__hint', 'Try again'),
                        'score': f.__test.__get_score(result),
                        'max_score': f.__test.__max_score,
                        'is_score_public': f.__test.__is_score_public
                    })

            # Section done, send results now
            sender.send_result({
                'name': str(cls),
                'header': section,
                'tests': as_json,
                'score': {
                    'private': { 
                        'absolute': {
                            'correct': real_correct, 
                            'total': real_total 
                        },
                        'numeric': {
                            'score': private_score_acc,
                            'total': private_score_total,
                            'extra-score': private_extra_acc,
                            'extra-total': private_extra_total
                        }
                    },
                    'public': {
                        'absolute': {
                            'correct': correct, 
                            'total': total 
                        },
                        'numeric': {
                            'score': public_score_acc,
                            'total': public_score_total,
                            'extra-score': public_extra_acc,
                            'extra-total': public_extra_total
                        }
                    }
                }
            })
        except:
            import traceback
            traceback.print_exc()

    def decorate(cls):
        cls.__tests = []
        items = cls.__dict__.copy()

        for attr in items: # there's propably a better way to do this
            f = getattr(cls, attr)

            if callable(f):
                setattr(cls, attr, None)
                setattr(cls, '__test_' + attr, _wrap_errors(cls, f))

                lno = f.__code__.co_firstlineno
                cls.__tests.append((lno, '__test_' + attr, attr))
                
        setattr(cls, 'test_steps', lambda self: test_steps(cls, self))
        return cls
    return decorate

