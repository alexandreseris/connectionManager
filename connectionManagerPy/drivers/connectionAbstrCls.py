# -*- coding: utf-8 -*-

import connectionManagerPy.exceptions as exceptions


class ConnectionAbstrCls():
    # abstract methods
    def connect(self, *args, **kwargs):
        raise exceptions.NotImplemented("class must implement connect method")
    def exec(self, *args, **kwargs):
        raise exceptions.NotImplemented("class must implement exec method")
    def close(self, *args, **kwargs):
        raise exceptions.NotImplemented("class must implement close method")
    # real methods
    def __init__(self, **connectionInfos):
        self.connectionInfos = connectionInfos
    def __enter__(self):
        self.connect()
        return self
    def __exit__(self, type, value, traceback):
        self.close()
