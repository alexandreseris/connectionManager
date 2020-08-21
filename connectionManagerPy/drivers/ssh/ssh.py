# -*- coding: utf-8 -*-

import fabric

import connectionManagerPy.drivers.connectionAbstrCls as connectionAbstrCls


class Driver(connectionAbstrCls.ConnectionAbstrCls):
    def connect(self):
        self.originalDriver = fabric
        host = self.connectionInfos.pop("url")
        user = self.connectionInfos.pop("username")
        password = self.connectionInfos.pop("password")
        self.conn = fabric.Connection( # doc : https://docs.fabfile.org/en/2.5/api/connection.html
            host=host,
            user=user,
            connect_kwargs={"password": password},
            **self.connectionInfos)
        del self.connectionInfos
    def exec(self, cmd, warn=True, hide=True, **kwargs): # PB sur l'encodage utilisé, les accents passent pas peut importe l'encod passé en param
        """execute la commande passée et retourne un objet représentant le résultat (stdout, stderr, etc)
        doc: http://docs.pyinvoke.org/en/stable/api/runners.html#invoke.runners.Runner.run
        """
        return self.conn.run(cmd, warn=warn, hide=hide, **kwargs)
    def put(self, localFile, remoteFile, preserve_mode=False):
        """upload file via scp
        doc: https://docs.fabfile.org/en/2.5/api/transfer.html#fabric.transfer.Transfer.put
        """
        return self.conn.put(localFile, remoteFile, preserve_mode=preserve_mode)
    def get(self, remoteFile, localFile, preserve_mode=False):
        """download file via scp
        doc: https://docs.fabfile.org/en/2.5/api/transfer.html#fabric.transfer.Transfer.get
        """
        return self.conn.get(remoteFile, localFile, preserve_mode=preserve_mode)


    def close(self):
        self.conn.close()
