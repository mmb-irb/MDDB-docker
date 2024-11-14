# Tips

In this section there are some interesting **tips** that can be useful for **debugging** errors or checking the **database**.

## Avoid cache for docker-compose

> NOTE: **From July 2024 onwards**, the instruction for Docker Compose in **mac** is without hyphen, so from now on, `docker-compose up -d` is `docker compose up -d` when executing in **macOS**.

Ie when developing and doing changes in git repo.

1. Stop all containers and remove all images: 

    ```sh
    docker-compose down --rmi all
    ```

2. Rebuild images avoiding cache:

    ```sh
    docker-compose build --no-cache

3. Rebuild a single service avoiding cache but preserving the rest of services (only service_name has changed):

    ```sh
    docker-compose build --no-cache <service_name>
    ```

4. Up services:
    ```sh
    docker-compose up -d
    ```

## Rebuild single service

For rebuilding a single service avoiding cache but preserving the rest of services:

1. **Rebuild the Service Image Without Cache:** Use docker-compose to rebuild the image locally, targeting only the service you want to update:

    ```sh
    docker-compose build --no-cache <service_name>
    ```

2. **Update the Service in the Swarm:** In Docker Swarm, you can force the service to use the updated image by running:

    ```sh
    docker service update --force <stack_name>_<service_name>
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

Add two more replicas to my_stack_website:

```sh
docker service scale my_stack_website=4
```

## Check service tasks

```sh
docker service ps my_stack_mongodb
```

In case of errors, use the --no-trunc flag for the sake of seeing the whole error text:

```sh
docker service ps my_stack_mongodb --no-trunc
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

Take into account that acessing mongoDB as **root/admin** user is **not recommended** as with this user there are **no restrictions** once inside the database. We strongly recommend to use the **users** defined in the [**mongo-init.js**](../mongodb/mongo-init.js) file for accessing the database.

## Docker logs

Show logs for a container:

```sh
docker logs my_rest
```

## Apache logs

    docker logs <apache_container_ID>