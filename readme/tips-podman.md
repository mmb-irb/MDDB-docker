# Tips

In this section there are some interesting **tips** that can be useful for **debugging** errors or checking the **database**.

## Rebuild service

Example for **client** service, execute build with **--no-cache** flag:

```sh
podman build -t client_image --no-cache --build-arg NODE_ID=${NODE} --build-arg CLIENT_INNER_PORT=${CLIENT_INNER_PORT} ./client
```

An then, run the service as usual:

```sh
podman run -d --name client -p ${CLIENT_OUTER_PORT}:${CLIENT_INNER_PORT} --cpus "${CLIENT_CPU_LIMIT}" --memory "${CLIENT_MEMORY_LIMIT}" --network web_network client_image
```

## Remove all containers and images

```sh
podman system prune -a
podman system prune --volumes -f
```

## Remove unused images

```sh
podman image prune
```

## Troubleshooting

Visit this link of the official repository:

https://github.com/containers/podman/blob/main/troubleshooting.md

## Execute mongo podman in terminal mode

```sh
podman exec -it mongodb bash
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

Additionally, users are able to access the database as a **root/admin** user, as defined in the [**.env**](../.env.podman.git) file:

    mongosh --username <ROOT_USER> --password <ROOT_PASSWORD>

Take into account that acessing mongoDB as **root/admin** user is **not recommended** as with this user there are **no restrictions** once inside the database. We strongly recommend to use the **users** defined in the [**mongo-init.js**](../mongodb/mongo-init.js) file for accessing the database.

## Podman logs

Show logs for a container:

```sh
podman logs mongodb
```

## Apache logs

    podman logs apache