# -*- coding: utf-8 -*-

import ibm_db

import connectionManagerPy.drivers.connectionAbstrCls as connectionAbstrCls


class Driver(connectionAbstrCls.ConnectionAbstrCls):
    def connect(self):
        # connection is reaaaalllly slow, but exec is ok tho, weird
        conn_str='database={database};hostname={host};port={port};protocol={protocol};uid={user};pwd={pwd}'.format(
            database=self.connectionInfos["database"],
            host=self.connectionInfos["url"],
            user=self.connectionInfos["username"],
            pwd=self.connectionInfos["password"],
            port=self.connectionInfos["port"],
            protocol=self.connectionInfos["protocol"])
        self.conn = ibm_db.connect(conn_str,'','')
        del self.connectionInfos
    def exec(self, req, *args):
        try:
            stmt_select = ibm_db.exec_immediate(self.conn, req)
            res = []
            tmp = ibm_db.fetch_tuple( stmt_select )
            while tmp:
                res.append(tmp)
                tmp = ibm_db.fetch_tuple( stmt_select )
            return res
        except Exception as err:
            print(req)
            raise err
    def close(self):
        ibm_db.close(self.conn)
