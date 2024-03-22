# -*- coding: utf-8 -*-
import math
from typing import List, Iterable, Dict
from pymongo.operations import ReplaceOne
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.cursor import Cursor
from pymongo.errors import BulkWriteError, WriteError
from pymongo.results import UpdateResult, BulkWriteResult

from .mongo_client_factory import MongoClientFactory


class MongoTable:
    table_name: str = None
    db_conf_name: str = None

    def __init__(self, db: Database = None, table_name: str = None):
        self.db = db or MongoClientFactory.get_db(self.db_conf_name)
        self.table_name = table_name or self.table_name
        self._table = self.db.get_collection(self.table_name)

    def get_raw_collection(self) -> Collection:
        return self._table

    def is_table_exists(self) -> bool:
        return self.table_name in self.db.list_collection_names(filter={"name": self.table_name})

    def create_table(self) -> Collection:
        return self.db.create_collection(self.table_name)

    def drop_table(self):
        if self._table is not None:
            self._table.drop()
            self._table = None

    def count(self, filter_dict: dict = None) -> int:
        if filter_dict is None:
            filter_dict = dict()
        return self._table.count_documents(filter_dict)

    def find_one(self, filter_dict: dict = None) -> dict:
        return self._table.find_one(filter_dict)

    def find(self, filter_dict: dict = None, sort_list: list = None, offset: int = None, limit: int = None) -> Cursor:
        params = dict()
        if filter_dict is not None:
            params['filter'] = filter_dict

        if sort_list is not None:
            params['sort'] = sort_list

        if offset is not None:
            params['skip'] = offset
        if limit is not None:
            params['limit'] = limit

        return self._table.find(**params)

    def find_with_pagination(self, filter_dict: dict = None, sort_list: list = None, page_size: int = 10000) -> Iterable[Dict]:
        total_count = self._table.count_documents(filter=filter_dict)
        total_times = math.ceil(total_count / page_size)

        for i in range(total_times):
            offset = i * page_size
            cursor = self.find(filter_dict=filter_dict, sort_list=sort_list, offset=offset, limit=page_size)
            for entry in cursor:
                yield entry

    def upsert_one(self, entry: dict, unique_field: str = None) -> (bool, UpdateResult | str):
        unique_field = unique_field or '_id'
        try:
            update_result = self._table.replace_one({unique_field: entry[unique_field]}, entry, upsert=True)
            return True, update_result
        except WriteError as e:
            return False, str(e)

    def upsert_many(self, entry_list: list, unique_field: str = None) -> (int, BulkWriteResult):
        unique_field = unique_field or '_id'
        request_list = list()

        for entry in entry_list:
            request_list.append(
                ReplaceOne({unique_field: entry[unique_field]}, entry, upsert=True)
            )

        error_count = 0
        while True:
            try:
                write_result = self._table.bulk_write(request_list)
                return error_count, write_result
            except BulkWriteError as e:
                error_index_list = list()
                for error in e.details['writeErrors']:
                    error_index_list.append(error['index'])

                error_count += len(error_index_list)
                for index in sorted(error_index_list, reverse=True):
                    del request_list[index]

    def create_index_list(self, field_name_list: List[str], is_unique: bool = False):
        all_index = self._table.index_information()
        for field_name in field_name_list:
            if f'{field_name}_1' in all_index:
                continue
            self._table.create_index(field_name, unique=is_unique, background=True)

    def drop_index_list(self, field_name_list: List[str]):
        all_index = self._table.index_information()
        for field_name in field_name_list:
            index_name = f'{field_name}_1'
            if index_name not in all_index:
                continue
            self._table.drop_index(index_name)

    def set_validator(self, required_field_list: list, fields_validator: dict):
        return self.db.command({
            "collMod": self.table_name,
            "validator": {
                '$jsonSchema': {
                    "bsonType": "object",
                    "required": required_field_list,
                    "properties": fields_validator
                }
            },
            "validationLevel": "moderate"
        })

    def disable_validator(self):
        batch = self.db.command({'listCollections': 1, 'filter': {'name': self.table_name}})['cursor']['firstBatch']
        if len(batch) == 0:
            return

        options = batch[0].get('options')
        if isinstance(options, dict) and options.get('validator') is not None:
            return self.db.command({
                "collMod": self.table_name,
                "validationLevel": "off"
            })
