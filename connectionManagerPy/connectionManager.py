# -*- coding: utf-8 -*-

from os.path import dirname as _dirname
from os.path import realpath as _realpath
from os.path import isfile as _isfile
from os.path import join as _join
from os import environ as _environ
from platform import system as _system
from enum import Enum as _Enum

import connectionManagerPy.utils as _utils


class FIELD_TRANSPOSITION_ENUM(_Enum):
    USER = "user"
    PASSWORD = "password"
    HOST = "host"


class ConnectionManager(metaclass=_utils.Singleton):
    drivers = {} # cache for getDriver method to avoid importing the same module several times and to not load every one at the same time

    def __init__(self, createSqliteInMemory=True, configFilePath=None, configDict={}):
        """fields in configDict or in configFile:
            keePassFilePath
            keePassNotesSeparator
            driversTypes
            password (not recommended)

            the configFile is first imported and its value is override by the configDict parameter
            each field must be given in the config file or the configDict parameter with the exception of password
            if password is not set, a prompt will ask you for it
        """
        from pykeepass import PyKeePass as _PyKeePass
        from pykeepass.exceptions import CredentialsIntegrityError as _CredentialsIntegrityError

        self.config = {}

        if configFilePath is None:
            if _system() == "Windows":
                configFilePath = _environ["USERPROFILE"]
            elif _system() in ("Linux", "Darwin"):
                configFilePath = _environ["HOME"]
            configFilePath = _join(configFilePath, ".connectionManagerpy", "config.py")

        if _isfile(configFilePath):
            configDictInFile = _utils.importFromPath(configFilePath).configDict
            self.config.update(configDictInFile)
            self.config.update(configDict)
        else:
            self.config.update(configDict)

        self.keePassFilePath = self.config["keePassFilePath"]
        self.keePassNotesSeparator = self.config["keePassNotesSeparator"]
        self.driversTypes = self.config["driversTypes"]

        try:
            pwd = self.config.get("password")
            if pwd is None:
                from getpass import getpass as _getpass
                pwd = _getpass("mdp: ")
            self.keyPassFile = _PyKeePass(self.keePassFilePath, pwd)
        except FileNotFoundError:
            raise FileNotFoundError(self.keePassFilePath + " inexistant")
        except _CredentialsIntegrityError:
            raise ValueError("mot de passe incorrect pour " + self.keePassFilePath)
        if createSqliteInMemory:
            self.inMemory = self.getDriver("sql", "sqlite")
            self.inMemory = self.inMemory()
            self.inMemory.connect(self.inMemory.inmemory)

    def _parseEntry(self, entry):
        entryInfos = {**dict(
            [
                ( elem.split(self.keePassNotesSeparator)[0], self.keePassNotesSeparator.join(elem.split(self.keePassNotesSeparator)[1:]) )
                for elem in entry.notes.split("\n")
            ]
        )}
        entryInfos["username"] = entry.username
        entryInfos["password"] = entry.password
        entryInfos["url"] = entry.url
        return entryInfos

    def _getConnectionInfos(self, driverType=None, connectionName=None, connectionEnv=None, connectionPath=None):
        """get the keypass entry infos by looking from driverType, connectionName and connectionEnv or connectionPath
        """
        if driverType is not None and connectionName is not None and connectionEnv is not None:
            try:
                driverTypeGroup = self.keyPassFile.find_groups(path=self.driversTypes[driverType])
            except KeyError:
                raise ValueError("le type de connexion " + driverType + " n'est pas paramétré dans le fichier de config")
            if driverTypeGroup is None:
                raise ValueError("le type de connexion " + driverType + " n'existe pas en tant que groupe dans le fichier")

            try:
                connectionNameGroupe = self.keyPassFile.find_groups(name=connectionName, group=driverTypeGroup)[0]
            except IndexError:
                raise ValueError("le nom de connexion " + connectionName + " n'existe pas en tant que groupe dans le fichier dans le groupe " + driverType)

            try:
                entry = self.keyPassFile.find_entries(title=connectionEnv, group=connectionNameGroupe)[0]
            except IndexError:
                raise ValueError("l'environnement " + connectionEnv + " n'existe pas en tant qu'entrée dans le fichier dans le groupe " +
                                 connectionNameGroupe + " du groupe " + driverType)
        elif connectionPath is not None:
            entry = self.keyPassFile.find_entries(path=connectionPath)
            if entry is None:
                raise ValueError("l'entrée " + connectionPath + " n'existe pas")
        else:
            raise TypeError("_getConnectionInfos doit recevoir 3 (driverType, connectionName, connectionEnv) ou 1 (connectionPath) argument")

        return self._parseEntry(entry)

    @classmethod
    def getDriver(cls, driverType, connType):
        """take driverType and connType to return the corresponding class imported from the file system.
        Used internally and can be used for the connections where no authentification is needed (sqlite for instance)
        USAGE:
            with a context manager:
                drv = connectionManager.ConnectionManager.getDriver(driverType="sql", connType="sqlite")
                with drv(test="test") as c:
                    c.exec("execTest")
            without a context manager:
                drv = connectionManager.ConnectionManager.getDriver(driverType="sql", connType="sqlite")
                d = drv(test="test")
                d.connect()
                d.exec("execTest")
                d.close()
        """
        calcPath = _join(_realpath(_dirname(__file__)), "drivers", driverType, connType + ".py")
        # we first check if the driver has already been imported and stored in the class to buy time
        try:
            try:
                return cls.drivers[driverType][connType]
            except KeyError:
                driver = _utils.importFromPath(calcPath)
                driver = driver.Driver
                if not cls.drivers.get(driverType):
                    cls.drivers[driverType] = {}
                cls.drivers[driverType][connType] = driver
                return driver
        except FileNotFoundError:
            raise FileNotFoundError("aucun driver trouvé dans " + calcPath)

    def autoConnect(self, driverType, connectionName=None, connectionEnv=None, connectionPath=None, **additionnalConnectionInfos):
        """look for the corresponding entry in the keypass file, retrive connection infos, retrive corresponding driver and return an instance of the driver initialised with the connection infos
        USAGE:
            with a context manager:
                manager = connectionManager.ConnectionManager(pwd="lala")
                with manager.autoConnect(driverType="sql", connectionName="bddlambda", connectionEnv="prod") as a:
                    a.exec("execTest")
            without a context manager:
                b = manager.autoConnect(driverType="sql", connectionName="bddlambda", connectionEnv="prod")
                b.connect()
                b.exec("execTest")
                b.close()
        """
        if connectionName is not None and connectionEnv is not None:
            connectionInfos = self._getConnectionInfos(driverType, connectionName, connectionEnv)
            searchMethod = (driverType, connectionName, connectionEnv)
        elif connectionPath is not None:
            connectionInfos = self._getConnectionInfos(connectionPath)
            searchMethod = (connectionPath,)
        else:
            raise ValueError("autoConnect doit recevoir les arguments connectionName et connectionEnv ou connectionPath")
        try:
            connType = connectionInfos["type"]
        except KeyError:
            raise ValueError("aucun type de connexion trouvé dans les notes pour " + str(searchMethod))
        connectionInfos.pop("type")
        drv = self.getDriver(driverType, connType)
        mergedConnectionsInfos = {**connectionInfos, **additionnalConnectionInfos}
        return drv(**mergedConnectionsInfos)

    def _close(self):
        del self.keyPassFile
