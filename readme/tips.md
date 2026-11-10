# Tips

In this section there are some interesting **tips** that can be useful for **debugging** errors or checking the **database**.

## Avoid cache for docker-compose

> NOTE: In **docker old versions** the instruction for Docker Compose is with hyphen, so instead of `docker compose build`, `docker-compose build` must be typed and executed.

Ie when developing and doing changes in git repo.

1. Stop all containers and remove all images: 

    ```sh
    docker stack rm my_stack
    docker compose down --rmi all
    ```

2. Rebuild images avoiding cache:

    ```sh
    docker compose build --no-cache
    ```

3. Rebuild a single service avoiding cache but preserving the rest of services (only service_name has changed):

    ```sh
    docker compose build --no-cache <service_name>
    ```

4. Deploy the stack again (the services run in Docker Swarm, not with `docker compose up`):
    ```sh
    python3 scripts/stack-deploy.py -t my_stack
    ```

## Clean docker

When working with Docker, **even after removing images and containers**, Docker can leave behind various unused resources that take up **disk space**. To clean up your system effectively, you can use the following commands:

1. **Remove** unused containers, images and networks:

    Docker has a built-in command to clean up resources that are not in use:

        docker system prune

    This command will prompt you to confirm that you want to remove all unused data. If you want to avoid the prompt, you can add the -f (force) flag:

        docker system prune -f

2. **Cleaning up** the Docker builder **cache**:

    Docker build cache can also take up significant space. You can remove unused build cache:

        docker builder prune

    If you want to remove all build cache, including the cache used by the active build process:

        docker builder prune -a -f

3. Remove unused **volumes**:

    By default, docker system prune does not remove unused volumes. If you want to remove them as well, you can use:

        docker system prune --volumes

    If you want to avoid the prompt, you can add the -f (force) flag:

        docker system prune --volumes -f

    To ensure, list volumes:

        docker volume ls

    For removing all volumes (beware):

        docker volume rm $(docker volume ls -q)

4. Remove unused **networks**:

    Usually, the steps above remove the networks related to the project, but this instruction removes the unused networks:

        docker network prune -f

    To ensure, list networks:

        docker network ls

5. **Check disk usage** by Docker objects

        docker system df

## Scale a service:

Add two more replicas to my_stack_client:

```sh
docker service scale my_stack_client=4
```

Set new memory limit to my_stack_client:

```sh
docker service update --limit-memory 1g my_stack_client
```

Multiple options:

```sh
docker service update --limit-memory 1g --reserve-memory 512m --limit-cpu 2 --replicas 3 my_stack_client
```

## Stop a service:

Stop my_stack_mongo-backup service:

```sh
docker service rm my_stack_mongo-backup
```

## Check service tasks

```sh
docker service ps my_stack_mongodb
```

In case of errors, use the --no-trunc flag for the sake of seeing the whole error text:

```sh
docker service ps my_stack_mongodb --no-trunc
```

## Enter any container bypassing entrypoint

```sh
  docker exec -it <container_ID> /bin/sh
```

## Execute mongo docker in terminal mode

```sh
docker exec -it <mongo_container_ID> bash
```

And then: 

```sh
mongosh 
```

For entering the database in **terminal mode**. Take into account that, for **checking** your database and its **collections**, you must use the **authentication credentials** defined in the [**mongo-init.js**](../mongodb/mongo-init.js) file. For example, for checking the **collections** of the mddb_db **database**, please follow the next steps:

Switch to **mddb_db** database (or the name defined in the [**mongo-init.js**](../mongodb/mongo-init.js) file):

    use mddb_db

**Authenticate** with one of the **users** defined in the [**mongo-init.js**](../mongodb/mongo-init.js) file:

    db.auth('user_r','pwd_r');

Execute some mongo shell instruction:

    show collections

Additionally, users are able to access the database as a **root/admin** user, as defined in the [**docker-compose.yml**](../docker-compose.yml) file:

    mongosh --username <ROOT_USER> --password <ROOT_PASSWORD>

Take into account that accessing mongoDB as **root/admin** user is **not recommended** as with this user there are **no restrictions** once inside the database. We strongly recommend to use the **users** defined in the [**mongo-init.js**](../mongodb/mongo-init.js) file for accessing the database.

## Add new user to Mongo

The actions of the [**mongo-init.js**](../mongodb/mongo-init.js) file are executed only once, when the mongodb service is deployed for the first time. For avoiding to wipe out the database and deploying the service from scratch, execute the following code for adding a new user to the database:

```js
docker exec -it <mongo_container_ID> mongosh \
  "mongodb://$MONGO_INITDB_ROOT_USERNAME:$MONGO_INITDB_ROOT_PASSWORD@$VRE_LITE_DB_SERVER:27017/admin" \
  --eval "
    db = db.getSiblingDB('$VRE_LITE_MONGO_DATABASE');
    db.createUser({
      user: '$VRE_LITE_DB_LOGIN',
      pwd: '$VRE_LITE_DB_PASSWORD',
      roles: [{role: 'readWrite', db: '$VRE_LITE_MONGO_DATABASE'}]
    });
  "
```

## Mongo restore

If there is a previous version of the database it can be copied into the **my_stack_mongodb** service. This is the instruction for performing a `mongorestore` from a **mongo dump**:

    docker run --rm --network data_network -v <PATH_TO_MONGODUMP>:/dump mongo:8.0 mongorestore --host my_stack_mongodb --port 27017 --username <ROOT_USER> --password <ROOT_PASSWORD> --authenticationDatabase admin --db <DB_TO_RESTORE> /dump/<DB_TO_RESTORE>

* **PATH_TO_MONGODUMP:** Path to the mongo dump.
* **ROOT_USER:** Root user for the DB.
* **ROOT_PASSWORD:** Root password for the DB.
* **DB_TO_RESTORE:** Name of the database to restore.

## Open temporarily MongoDB port

The MongoDB port is **closed by default** for security purposes. If needed, it can be **temporarily** open with this command:

```sh
docker service update --publish-add mode=host,published=27017,target=27017 my_stack_mongodb
```

Check that the **27017 port** is effectively open:

```sh
$ ss -tuln | grep 27017
tcp   LISTEN 0      4096             0.0.0.0:27017      0.0.0.0:*          
tcp   LISTEN 0      4096                [::]:27017         [::]:*
```

After using it, please **execute** the following command for **closing** it again:

```sh
docker service update --publish-rm mode=host,published=27017,target=27017 my_stack_mongodb
```

Now the following command:

```sh
$ ss -tuln | grep 27017
```

Should return nothing again.

## Check image version

```sh
docker run --entrypoint "" --rm <image_name> sh -c "cat /app/version.txt"
```

## Docker logs

Show logs for a container:

```sh
docker logs my_rest
```

## Apache logs

    docker logs <apache_container_ID>