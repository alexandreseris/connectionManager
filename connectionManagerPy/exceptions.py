# -*- coding: utf-8 -*-


class _BaseClassException(Exception):
    def __init__(self, message):
        super().__init__(message)
    def __repr__(self):
        return str(self.__class__) + ": " + str(self.args[0])
    def __str__(self):
        return self.__repr__()


class NotImplemented(_BaseClassException):
    pass
