# utils.py

import re

# Adapted from https://stackoverflow.com/questions/6760685/what-is-the-best-way-of-implementing-singleton-in-python
class _Singleton(type):
    """ A metaclass that creates a Singleton base class when called. """
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(_Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Singleton(_Singleton('SingletonMeta', (object,), {})): pass

# Conversions between eid and string version
def get_atk_str(eid_or_uv, model):
    if type(eid_or_uv) is int: # eid
        eid = eid_or_uv
        uv = model.get_uv_from_eid(eid)
    elif type(eid_or_uv) is tuple: # uv
        uv = eid_or_uv
        eid = model.get_eid_from_uv(uv)
    return f'branch {eid}({min(*uv)}-{max(*uv)})'

def get_atk_eid(atk_str):
    return int(re.match(r'branch (\d+)\(.*\)', atk_str).group(1))
