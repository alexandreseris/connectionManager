# -*- coding: utf-8 -*-

import sqlite3

import connectionManagerPy.drivers.connectionAbstrCls as connectionAbstrCls
import connectionManagerPy.drivers.sql.sqlConnectionAbstrCls as sqlConnectionAbstrCls


class Driver(connectionAbstrCls.ConnectionAbstrCls, sqlConnectionAbstrCls.SqlConnectionAbstrCls):
    inmemory = ":memory:"
    def connect(self, *args, **kwargs):
        self.originalDriver = sqlite3
        self.conn = sqlite3.connect(*args, **{**self.connectionInfos, **kwargs})
        self.cur = self.conn.cursor()
        del self.connectionInfos
    def commit(self):
        self.conn.commit()
    def exec(self, req, autocommit=True):
        self.cur.execute(req)
        if autocommit:
            self.commit()
    def close(self):
        self.cur.close()
        self.conn.close()

    def getCursorCols(self):
        return [column[0] for column in self.cur.description]
    def select(self, req):
        self.cur.execute(req)
        for line in self.cur: # a améliorer avec un fecthone si possible
            yield dict(zip([column[0] for column in self.cur.description], line))

