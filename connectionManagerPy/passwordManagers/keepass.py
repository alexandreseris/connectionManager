# -*- coding: utf-8 -*-

import re

from pykeepass import PyKeePass as _PyKeePass

from connectionManagerPy.connectionManager import FIELD_TRANSPOSITION_ENUM as _FIELD_TRANSPOSITION_ENUM


class PasswordManager():
    def __init__(self, filePath, variousInfosFieldSeparator="=", variousInfosLineSeparator="\n", commentChar="#", pathDict={}, pwd=None):
        if pwd is None:
            from getpass import getpass as _getpass
            pwd = _getpass("password for {}: ".format(filePath))
        self._keyPassFile = _PyKeePass(filePath, pwd)
        self.variousInfosFieldSeparator = variousInfosFieldSeparator
        self.variousInfosLineSeparator = variousInfosLineSeparator
        self.commentChar = commentChar
        self.pathDict = pathDict # dict witch map a connection name to a location in the keepass file

    def getEntry(self, path=None, name=None):
        if path is None and name is not None:
            path = self.pathDict[name]
        elif path is None and name is None:
            raise TypeError("either path or name params must be passed to getEntry")
        return self._keyPassFile.find_entries(path=path)

    def parseEntry(self, entry):
        entryInfos = {}
        if entry.username is not None:
            entryInfos[_FIELD_TRANSPOSITION_ENUM.USER.value] = entry.username
        if entry.password is not None:
            entryInfos[_FIELD_TRANSPOSITION_ENUM.PASSWORD.value] = entry.password
        if entry.url is not None:
            entryInfos[_FIELD_TRANSPOSITION_ENUM.HOST.value] = entry.url
        for line in entry.notes.split(self.variousInfosLineSeparator):
            if not re.search(r"^[ \t]*" + re.escape(self.commentChar), line):
                columnSplit = line.split(self.variousInfosFieldSeparator)
                if len(columnSplit) >= 2:
                    lineKey = columnSplit[0]
                    lineValue = self.variousInfosFieldSeparator.join(columnSplit[1:])
                    entryInfos[lineKey] = lineValue
        return entryInfos

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self._keyPassFile.close()
