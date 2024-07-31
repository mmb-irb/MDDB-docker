# Tips

In this section there are some interesting **tips** that can be useful for **debugging** errors or checking the **database**.

## Avoid cache for docker-compose

Ie when developing and doing changes in git repo.

1. Stop all containers and remove all images: 

    ```sh
    docker-compose down --rmi all
    ```

2. Rebuild images avoiding cache:

    ```sh
    docker-compose build --no-cache
    ```

3. Up services:
    ```sh
    docker-compose up -d
    ```

## Execute mongo docker in terminal mode

```sh
docker exec -it my_mongo_container bash
```

And then: 

```sh
mongosh 
```

For entering the database in **terminal mode**. Take into account that, for **checking** your database and its **collections**, you must use the **authentication credentials** defined in the [**mongo-init.js**](../mongo-init.js) file. For example, for checking the **collections** of the mddb_db **database**, please follow the next steps:

Switch to **mddb_db** database (or the name defined in the [**mongo-init.js**](../mongo-init.js) file):

    use mmddb_db

**Authenticate** with one of the **users** defined in the [**mongo-init.js**](../mongo-init.js) file:

    db.auth('user_r','pwd_r');

Execute some mongo shell instruction:

    show collections

Additionally, users are able to access the database as a **root/admin** user, as defined in the [**docker-compose.yml**](../docker-compose-git.yml) file:

    mongosh --username <ROOT_USER> --password <ROOT_PASSWORD>

Take into account that acessing mongoDB as **root/admin** user is **not recommended** as with this user there are **no restrictions** once inside the database. We strongly recommend to use the **users** defined in the [**mongo-init.js**](../mongo-init.js) file for accessing the database.

## Docker logs

Show logs for a container:

```sh
docker logs my_rest
```