# -*- coding: utf-8 -*-

import requests
import json

import connectionManagerPy.drivers.connectionAbstrCls as connectionAbstrCls


class Driver(connectionAbstrCls.ConnectionAbstrCls):
    def connect(self):
        params = {
            "grant_type": self.connectionInfos["grant_type"],
            "client_id": self.connectionInfos["client_id"],
            "client_secret": self.connectionInfos["client_secret"],
            "refresh_token" : self.connectionInfos["refresh_token"]
        }
        r = requests.post("https://login.salesforce.com/services/oauth2/token", params=params)
        self.access_token = r.json().get("access_token")
        self.instance_url = r.json().get("instance_url")

        serviceListUrl = requests.get(self.instance_url + "/services/data")
        serviceListUrl = json.loads(serviceListUrl.content.decode("utf8"))
        maxVersion = max([float(x["version"]) for x in serviceListUrl])
        maxVersionUrl = [x["url"] for x in serviceListUrl if x["version"] == str(maxVersion)][0]
        self.queryUrl = maxVersionUrl
        del self.connectionInfos

    def exec(self, req=None, method="get", action=None, params=None, removeAttrs=True, verbose=False, returnRaw=True):
        headers = {
            'Authorization': 'Bearer %s' % self.access_token
        }
        if method in ("get", "post"):
            headers['Content-type'] = 'application/json'
            headers['Accept-Encoding'] = 'gzip'
        if params is None and req is not None:
            params = {"q": req}
        if action is None:
            action = self.queryUrl + "/query"
        url = self.instance_url + action
        if verbose:
            print("appel de " + method + ":" + url + " headers: " + str(headers) + " params: " + str(params))
        r = requests.request(method, url, headers=headers, params=params, timeout=10)

        if str(r.status_code)[0] in ("4", "5"):
            raise ValueError("return code: " + str(r.status_code) + ", message: " + str(r.json()))
        if method in ("get", "post") and returnRaw is False:
            res = r.json().get("records") # faudrait trouver une feinte pour au moins enlever le champs attributes qui sert à rien
            if removeAttrs and res is not None:
                _ =[ x.pop("attributes") for x in res ] # noqa
        else:
            res = r.content
        return res

    def close(self):
        pass
