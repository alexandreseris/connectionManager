# -*- coding: utf-8 -*-

import mysql.connector

import connectionManagerPy.drivers.connectionAbstrCls as connectionAbstrCls
import connectionManagerPy.drivers.sql.sqlConnectionAbstrCls as sqlConnectionAbstrCls


class Driver(connectionAbstrCls.ConnectionAbstrCls, sqlConnectionAbstrCls.SqlConnectionAbstrCls):
    def connect(self):
        self.originalDriver = mysql.connector
        ssl_ca = self.connectionInfos.get("ssl_ca")
        ssl_key = self.connectionInfos.get("ssl_key")
        ssl_cert = self.connectionInfos.get("ssl_cert")
        self.conn = mysql.connector.connect(host=self.connectionInfos["url"],
                                            user=self.connectionInfos["username"],
                                            password=self.connectionInfos["password"],
                                            database=self.connectionInfos["database"],
                                            port=self.connectionInfos["port"],
                                            ssl_ca=ssl_ca,
                                            ssl_key=ssl_key,
                                            ssl_cert=ssl_cert)
        self.cur = self.conn.cursor()
        del self.connectionInfos

    def getCursorCols(self):
        return list(self.cur.column_names)
    def exec(self, req):
        self.cur.execute(req)
        tmp = self.cur.fetchone()
        while tmp:
            yield dict(zip(self.cur.column_names, tmp))
            tmp = self.cur.fetchone()

    def close(self):
        self.cur.close()
        self.conn.close()
