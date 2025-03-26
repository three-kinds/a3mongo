# -*- coding: utf-8 -*-
from typing import Dict, List
from pymongo import MongoClient
from pymongo.database import Database

DEFAULT_NAME = "default"


class MongoClientFactory:
    _client_list: List[MongoClient] = list()
    _name2conf: Dict[str, Dict] = dict()
    _name2db: Dict[str, Database] = dict()

    @classmethod
    def init_mongo_clients(cls, conf: dict):
        for name, cf in conf.items():
            client: MongoClient = MongoClient(**cf)
            db = client[cf["authSource"]]

            cls._client_list.append(client)
            cls._name2conf[name] = cf
            cls._name2db[name] = db

    @classmethod
    def get_db(cls, name: str | None = None) -> Database:
        if name is None:
            name = DEFAULT_NAME

        db = cls._name2db.get(name)
        if db is None:
            raise AssertionError(f"Invalid mongo client [{name}]")

        return db

    @classmethod
    def close_all_clients(cls):
        for client in cls._client_list:
            client.close()

        cls._client_list = list()
        cls._name2conf = dict()
        cls._name2db = dict()
