# -*- coding: utf-8 -*-
from unittest import TestCase
from pymongo.database import Database
from a3mongo import MongoClientFactory
from a3mongo.mongo_client_factory import DEFAULT_NAME


class TestMongoClientFactory(TestCase):

    def test_get_db(self):
        conf = {
            DEFAULT_NAME: {
                "host": "127.0.0.1",
                "port": 27017,
                "authSource": "db_name"
            }
        }
        MongoClientFactory.init_mongo_clients(conf=conf)
        default_db = MongoClientFactory.get_db()
        self.assertIsInstance(default_db, Database)

        with self.assertRaises(AssertionError):
            MongoClientFactory.get_db(name="not_exist")
