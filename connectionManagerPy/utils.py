# -*- coding: utf-8 -*-

import importlib.util as _importlib
from os.path import basename as _basename


def importFromPath(path):
    """
    import all modules in dir except __init__ and places them in modules dict
    """
    spec = _importlib.spec_from_file_location(_basename(path)[:-3], path)
    mod = _importlib.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
