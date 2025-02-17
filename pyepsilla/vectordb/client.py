#!/usr/bin/env python
# -*- coding:utf-8 -*-
import json, requests, socket, datetime, time, sentry_sdk
from typing import Union, Optional
from requests.packages.urllib3.exceptions import InsecureRequestWarning 
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class Client():
    def __init__(self, protocol: str = 'http', host: str = 'localhost', port: str = '8888'):
        self._protocol = protocol
        self._host = host
        self._port = port
        self._baseurl = "{}://{}:{}".format(self._protocol, self._host, self._port)
        self._db = None
        self._timeout = 10
        self._header = {'Content-type': 'application/json', "Connection": "close"}
        self.check_networking()

    def check_networking(self):
        socket.setdefaulttimeout(self._timeout)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        check_result = s.connect_ex((self._host, int(self._port)))
        s.close()
        if check_result == 0:
            print("[INFO] Connected to {}:{} successfully.".format(self._host, self._port))
        else:
            raise Exception("[ERROR] Failed to connect to {}:{}".format(self._host, self._port))

    def welcome(self):
        req_url = "{}/".format(self._baseurl)
        req_data = None
        res = requests.get(url=req_url, data=json.dumps(req_data), headers=self._header, timeout=self._timeout, verify=False)
        status_code = res.status_code
        body = res.text
        res.close()
        return status_code, body

    def state(self):
        req_url = "{}/state".format(self._baseurl)
        req_data = None
        res = requests.get(url=req_url, data=json.dumps(req_data), headers=self._header, verify=False)
        status_code = res.status_code
        body = res.json()
        res.close()
        return status_code, body

    def use_db(self, db_name: str):
        self._db = db_name

    def load_db(self, db_name: str, db_path: str, vector_scale: int = None, wal_enabled: bool = False):
        req_url = "{}/api/load".format(self._baseurl)
        req_data = {"name": db_name, "path": db_path}
        if vector_scale is not None:
            req_data["vectorScale"] = vector_scale
        if wal_enabled is not None:
            req_data["walEnabled"] = wal_enabled
        res = requests.post(url=req_url, data=json.dumps(req_data), headers=self._header, verify=False)
        status_code = res.status_code
        body = res.json()
        res.close()
        return status_code, body


    def unload_db(self, db_name: str):
        req_url = "{}/api/{}/unload".format(self._baseurl, db_name)
        res = requests.post(url=req_url, data=None, headers=self._header, verify=False)
        status_code = res.status_code
        body = res.json()
        res.close()
        return status_code, body

    def create_table(self, table_name: str, table_fields: list[str] = None):
        if self._db is None:
            raise Exception("[ERROR] Please use_db() first!")
        if table_fields is None:
            table_fields = []
        req_url = "{}/api/{}/schema/tables".format(self._baseurl, self._db)
        req_data = {"name": table_name, "fields": table_fields}
        res = requests.post(url=req_url, data=json.dumps(req_data), headers=self._header, verify=False)
        status_code = res.status_code
        body = res.json()
        res.close()
        return status_code, body

    def list_tables(self):
        if self._db is None:
            raise Exception("[ERROR] Please use_db() first!")
        req_url = "{}/api/{}/schema/tables/show".format(self._baseurl, self._db)
        res = requests.get(url=req_url, headers=self._header, verify=False)
        status_code = res.status_code
        body = res.json()
        res.close()
        return status_code, body


    def insert(self, table_name: str, records: list = None):
        if self._db is None:
            raise Exception("[ERROR] Please use_db() first!")
        if records is None:
            records = []
        req_url = "{}/api/{}/data/insert".format(self._baseurl, self._db)
        req_data = {"table": table_name, "data": records}
        res = requests.post(url=req_url, data=json.dumps(req_data), headers=self._header, verify=False)
        status_code = res.status_code
        body = res.json()
        res.close()
        return status_code, body

    def delete(self, table_name: str, primary_keys: list[Union[str,int]] = None, ids: list[Union[str,int]] = None, filter: Optional[str] = None):
        """Epsilla supports delete records by primary keys as default for now."""
        if self._db is None:
            raise Exception("[ERROR] Please use_db() first!")

        if filter == None:
            if primary_keys == None and ids == None:
                raise Exception("[ERROR] Please provide at least one of primary keys(ids) and filter to delete record(s).")
        if primary_keys == None and ids != None:
            primary_keys = ids
        if primary_keys != None and ids != None:
            try:
                sentry_sdk.sdk("Duplicate Keys with both primary keys and ids", "info")
            except Exception as e:
                pass
            print("[WARN] Both primary_keys and ids are prvoided, will use primary keys by default!")
        
        req_url = "{}/api/{}/data/delete".format(self._baseurl, self._db)
        req_data = {"table": table_name}
        if primary_keys != None:
            req_data["primaryKeys"] = primary_keys
        if filter != None:
            req_data["filter"] = filter
        res = requests.post(url=req_url, data=json.dumps(req_data), headers=self._header, verify=False)
        status_code = res.status_code
        body = res.json()
        res.close()
        return status_code, body


    def rebuild(self, timeout: int = 7200):
        req_url = "{}/api/rebuild".format(self._baseurl)
        req_data = None
        print("[INFO] waiting until rebuild is finished ...")
        start_time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        res = requests.post(url=req_url, data=json.dumps(req_data), headers=self._header, timeout=timeout, verify=False)
        end_time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        print("[INFO] Start Time:{}\n       End   Time:{}".format(start_time, end_time))
        status_code = res.status_code
        body = res.json()
        res.close()
        return status_code, body

    def query(
        self, table_name: str,
        query_field: str = "",
        query_vector: Union[list,dict] = None,
        response_fields: list = None,
        limit: int = 1,
        filter: str = "",
        with_distance: bool = False
    ):
        if self._db is None:
            raise Exception("[ERROR] Please use_db() first!")
        if query_vector is None:
            query_vector = []
        if response_fields is None:
            response_fields = []
        req_url = "{}/api/{}/data/query".format(self._baseurl, self._db)
        req_data = {
            "table": table_name,
            "queryField": query_field,
            "queryVector": query_vector,
            "response": response_fields,
            "limit": limit,
            "filter": filter,
            "withDistance": with_distance
        }
        res = requests.post(url=req_url, data=json.dumps(req_data), headers=self._header, verify=False)
        status_code = res.status_code
        body = res.json()
        res.close()
        return status_code, body

    def get(self, table_name: str, response_fields: Optional[list] = None, primary_keys: Optional[list[Union[str,int]]] = None, ids: Optional[list[Union[str,int]]] = None, filter: Optional[str] = None, skip: Optional[int] = None, limit: Optional[int] = None):
        if self._db is None:
            raise Exception("[ERROR] Please use_db() first!")
        if primary_keys != None and ids != None:
            try:
                sentry_sdk.sdk("Duplicate Keys with both primary keys and ids", "info")
            except Exception as e:
                pass
            print("[WARN] Both primary_keys and ids are prvoided, will use primary keys by default!")
        if primary_keys == None and ids != None:
            primary_keys = ids

        req_data = {"table": table_name}

        if response_fields != None:
            req_data["response"] = response_fields

        if primary_keys != None:
            req_data["primaryKeys"] = primary_keys

        if filter != None:
            req_data["filter"] = filter

        if skip != None:
            req_data["skip"] = filter

        if limit != None:
            req_data["limit"] = filter

        req_url = "{}/api/{}/data/get".format(self._baseurl, self._db)
        res = requests.post(url=req_url, data=json.dumps(req_data), headers=self._header, verify=False)
        status_code = res.status_code
        body = res.json()
        res.close()
        return status_code, body


    def drop_table(self, table_name: str = None):
        if self._db is None:
            raise Exception("[ERROR] Please use_db() first!")
        req_url = "{}/api/{}/schema/tables/{}".format(self._baseurl, self._db, table_name)
        req_data = None
        res = requests.delete(url=req_url, data=json.dumps(req_data), headers=self._header, verify=False)
        status_code = res.status_code
        body = res.json()
        res.close()
        return status_code, body

    def drop_db(self, db_name: str):
        req_url = "{}/api/{}/drop".format(self._baseurl, db_name)
        res = requests.delete(url=req_url, data=None, headers=self._header, verify=False)
        status_code = res.status_code
        body = res.json()
        res.close()
        return status_code, body
