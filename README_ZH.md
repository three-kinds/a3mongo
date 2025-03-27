# a3mongo

[English](README.md) | 简体中文

`a3mongo` 对 `pymongo` 做了简单的封装，目的是用起来更简单。

## 1. 简介

* 可以同时配置多个 mongodb 服务
* 封装了一些常用的方法

## 2. 使用

### 安装

```shell
pip install a3mongo

```

### 样例

```python
CONF = {
    'site_a': {
        "host": "127.0.0.1",
        "port": 27017,
        "username": "username",
        "password": "password",
        "authSource": "site_a",
        "authMechanism": "SCRAM-SHA-256"
    },
    'site_b': {
        "host": "127.0.0.1",
        "port": 27018,
        "username": "username",
        "password": "password",
        "authSource": "site_b",
        "authMechanism": "SCRAM-SHA-256"
    }
}


from a3mongo import MongoClientFactory, MongoTable


class SiteUser(MongoTable):
    table_name = 'site_user'
    db_conf_name = 'site_a'

    
if __name__ == '__main__':
    MongoClientFactory.init_mongo_clients(conf=CONF)
    site_user = SiteUser()
    site_user.create_table()
    site_user.create_index_list(['name', 'gender', 'email'])
    site_user.upsert_many([
        {'name': 'Alice', 'gender': 'female', 'email': 'alice@example.com'},
        {'name': 'Bob', 'gender':'male', 'email': 'bob@example.com'},
        {'name': 'Charlie', 'gender': 'male', 'email': 'charlie@example.com'},
    ])
    male_users = site_user.find({'gender':'male'})

```
