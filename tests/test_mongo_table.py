# -*- coding: utf-8 -*-
from unittest import TestCase
from pymongo.collection import Collection
from a3mongo import MongoTable, MongoClientFactory, DEFAULT_NAME


class TestMongoTable(TestCase):
    def setUp(self):
        conf = {DEFAULT_NAME: {"host": "127.0.0.1", "port": 27017, "authSource": "test_db"}}
        MongoClientFactory.init_mongo_clients(conf=conf)

    def tearDown(self):
        db = MongoClientFactory.get_db()
        db.drop_collection("test_table")
        MongoClientFactory.close_all_clients()

    def test_get_raw_collection(self):
        table = MongoTable(table_name="test_table")
        collection = table.get_raw_collection()
        self.assertIsInstance(collection, Collection)

    def test_is_table_exists(self):
        table = MongoTable(table_name="test_table")
        self.assertEqual(table.is_table_exists(), False)
        table.create_table()
        self.assertEqual(table.is_table_exists(), True)
        table.drop_table()
        self.assertEqual(table.is_table_exists(), False)

    def test_upsert_and_find_one(self):
        table = MongoTable(table_name="test_table")
        self.assertEqual(table.count(), 0)
        is_success, update_result = table.upsert_one({"_id": 1, "name": "Alice"})
        self.assertEqual(is_success, True)
        self.assertEqual(update_result.upserted_id, 1)
        self.assertEqual(table.count(), 1)
        entry = table.find_one({"_id": 1})
        self.assertEqual(entry["name"], "Alice")

    def test_find_many(self):
        table = MongoTable(table_name="test_table")
        self.assertEqual(table.count(), 0)
        error_count, update_result = table.insert_many(
            entry_list=[{"_id": 1, "name": "Alice"}, {"_id": 2, "name": "Bob"}, {"_id": 3, "name": "Bob"}]
        )
        self.assertEqual(error_count, 0)
        self.assertEqual(update_result.upserted_count, 3)

        entry_list = list(table.find_with_pagination(page_size=2))
        self.assertEqual(len(entry_list), 3)

        entry_list = list(table.find(filter_dict={"name": "Bob"}, sort_list=[("_id", -1)], offset=1, limit=1))
        self.assertEqual(len(entry_list), 1)
        self.assertEqual(entry_list[0]["_id"], 2)

    def test_validator(self):
        table = MongoTable(table_name="test_table")
        table.disable_validator()

        table.create_table()
        table.set_validator(required_field_list=["_id", "name"], fields_validator={"name": {"bsonType": "string"}})
        is_success, _ = table.upsert_one({"_id": 1, "name": 123})
        self.assertEqual(is_success, False)
        is_success, _ = table.upsert_one({"_id": 2, "name": "Bob"})
        self.assertEqual(is_success, True)

        table.disable_validator()
        is_success, _ = table.upsert_one({"_id": 1, "name": 123})
        self.assertEqual(is_success, True)

    def test_index(self):
        table = MongoTable(table_name="test_table")
        table.create_table()
        all_index = table.get_raw_collection().index_information()
        self.assertEqual(len(all_index), 1)

        table.create_index_list(field_name_list=["name"])
        table.create_index_list(field_name_list=["name"])

        all_index = table.get_raw_collection().index_information()
        self.assertEqual(len(all_index), 2)

        table.drop_index_list(field_name_list=["gender"])
        all_index = table.get_raw_collection().index_information()
        self.assertEqual(len(all_index), 2)

        table.drop_index_list(field_name_list=["name"])
        all_index = table.get_raw_collection().index_information()
        self.assertEqual(len(all_index), 1)

    def test_upsert_error(self):
        table = MongoTable(table_name="test_table")
        table.create_table()
        table.set_validator(required_field_list=["_id", "name"], fields_validator={"name": {"bsonType": "string"}})
        is_success, value = table.upsert_one({"_id": 1, "name": 123})
        self.assertEqual(is_success, False)
        self.assertIn("Document failed validation", value)

        error_count, write_result = table.upsert_many(entry_list=[{"_id": 1, "name": "Alice"}, {"_id": 2, "name": 123}])
        self.assertEqual(error_count, 1)
        self.assertEqual(write_result.matched_count, 1)

        error_count, write_result = table.insert_many(
            entry_list=[{"_id": 1, "name": "Alice"}, {"_id": 2, "name": 123}, {"_id": 3, "name": "Bob"}]
        )
        self.assertEqual(error_count, 1)
        self.assertEqual(write_result.upserted_count, 1)
        self.assertEqual(write_result.matched_count, 1)
