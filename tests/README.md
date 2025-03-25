# Test

## 1. Deploy mongodb.

```shell
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  mongodb/mongodb-community-server:6.0.4-ubi8

```

## 2. Run tests.

```shell
make init
make coverage
make test

```