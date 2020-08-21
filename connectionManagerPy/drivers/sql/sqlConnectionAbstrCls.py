# -*- coding: utf-8 -*-


class SqlConnectionAbstrCls():
    # real methods
    def escapeString(self, string):
        return str(string).replace("'", "''")
    def formatSqlStr(self, string):
        if string is None:
            return "null"
        else:
            return "'" + self.escapeString(string) + "'"
