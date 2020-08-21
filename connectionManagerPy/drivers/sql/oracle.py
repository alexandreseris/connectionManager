# -*- coding: utf-8 -*-

import cx_Oracle

import connectionManagerPy.drivers.connectionAbstrCls as connectionAbstrCls


class Driver(connectionAbstrCls.ConnectionAbstrCls):
    def connect(self):
        self.originalDriver = cx_Oracle
        self.conn = cx_Oracle.connect(
            self.connectionInfos["username"],
            self.connectionInfos["password"],
            '{host}:{port}/{database}'.format(
                host=self.connectionInfos["url"],
                port=self.connectionInfos["port"],
                database=self.connectionInfos["database"])
        )
        self.cur = self.conn.cursor()
        del self.connectionInfos
    def exec(self, req):
        return self.cur.execute(req)
    def close(self):
        self.cur.close()
        self.conn.close()
