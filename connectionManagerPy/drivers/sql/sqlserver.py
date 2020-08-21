# -*- coding: utf-8 -*-

import pyodbc

import connectionManagerPy.drivers.connectionAbstrCls as connectionAbstrCls
import connectionManagerPy.drivers.sql.sqlConnectionAbstrCls as sqlConnectionAbstrCls


class Driver(connectionAbstrCls.ConnectionAbstrCls, sqlConnectionAbstrCls.SqlConnectionAbstrCls):
    maxInsert = 1000

    def _optionnalParamFormat(self, string, prefix=None, suffix=None):
        if string is None:
            return ""
        else:
            return str(prefix or "") + string + str(suffix or "")

    def connect(self):
        self.originalDriver = pyodbc
        conn_str = "Driver={{SQL Server}};Server={host}{port}{instance};Database={database};uid={user};pwd={pwd}"
        conn_str = conn_str.format(database=self.connectionInfos["database"],
                                   host=self.connectionInfos["url"],
                                   instance=self._optionnalParamFormat(self.connectionInfos.get("instance"), prefix="\\"),
                                   user=self.connectionInfos["username"],
                                   pwd=self.connectionInfos["password"],
                                   port=self._optionnalParamFormat(self.connectionInfos.get("port"), prefix=",")
                                   )
        # print(conn_str)
        self.conn = pyodbc.connect(conn_str) # connect peut utiliser des arguments facultatifs à la place d'une chaine formatée, ça peut etre plus simple à utiliser
        self.cur = self.conn.cursor()
        del self.connectionInfos

    def getCursorCols(self):
        return [column[0] for column in self.cur.description]
    def exec(self, req):
        """execute la requete passée en param et yield chaque res. Safe pour les select et opérations de modifs
        il est possible  pour execute d'écrire la requete avec un pattern (utilisation de ?) il faut dans ce passer en dernier param un set des valeurs qui vont remplacer les ?
        """
        try:
            self.cur.execute(req)
            tmp = self.cur.fetchone()
            while tmp:
                yield dict(zip([column[0] for column in self.cur.description], tmp))
                tmp = self.cur.fetchone()
        except pyodbc.ProgrammingError as err:
            if err.args[0] == 'No results.  Previous SQL was not a query.':
                pass
            else:
                raise err

    def close(self):
        self.cur.close()
        self.conn.close()

