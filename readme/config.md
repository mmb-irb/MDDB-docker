# Set Up Configuration Files

There are several **configuration files** that must be created and modified. As almost each of the different **docker blocks** of the project have **one or more** configuration files, this section is divided by these **blocks**:

* [Client](#client)
* [Loader](#loader)
* [REST API](#rest-api)
* [MongoDB](#mongodb)
* [Docker Compose](#docker-compose)

## Client

### .env file

As of July 2024, an **empty** `.env` file must be provided in the **[client folder](../client)**. An empty **[.env.git](../client/.env.git)** file is provided to remind that this `.env` file must be created.

### host-config.js

The host configuration file is used for setting up the target API and some basic visual setup of the client. This file is used only when using the [**Dockerfile2**](../client/Dockerfile2) for building the client docker. See the [**client README**](../client) for viewing how to change the default Dockerfile for this block.


```js
// Import default query fields
import defaultQueryFields from "src/utils/constants/query-fields";

// Set the default description
const DEFAULT_DESCRIPTION = <>
    <strong>MDposit</strong> is an open platform designed to provide web
    access to atomistic molecular dynamics (MD) simulations. The aim of
    this initiative is to ease and promote data sharing along the
    wide-world scientific community in order to contribute in research.
</>;

// Set default values for every host config fields
// These values are used to fill missing values
const DEFAUL_HOST_CONFIGURATION = {
    api: 'http://localhost:8081/rest/', // be aware that the URL must be the same as the one in the server (no relative paths allowed)
    production: false,
    name: 'MDposit',
    favicon: 'mdposit_favicon',
    description: DEFAULT_DESCRIPTION,
    logo: 'logo-mdposit',
    primaryColor: '#808080', // Grey
    secondaryColor: '#fafafa', // Light grey
    searchExample: 'e.g. Orozco lab',
    optionsField: undefined, // No browser selector and no data summary pie chart by default
    optionsLabel: 'Options',
    optionsNiceNames: {},
    queryFields: defaultQueryFields,
};

// Set every host configuration
const HOST_CONFIGURATIONS = {
    // Testing
    'localhost': {
        api: 'http://localhost:8081/rest/', // be aware that the URL must be the same as the one in the server (no relative paths allowed)))
        primaryColor: '#707070', // Grey
    }
};

// Set the current host configuration
const HOST_CONFIG = HOST_CONFIGURATIONS['localhost'];

// Fill the host configuration gaps with default values
Object.entries(DEFAUL_HOST_CONFIGURATION).forEach(([ field, defaultValue ]) => {
    if (!HOST_CONFIG[field]) HOST_CONFIG[field] = defaultValue;
});

export default HOST_CONFIG;
```

Parameters that can be changed in this file:

* api - API URL to query. It must be an absolute URL. Take into account that, depending on the [**Virtual Hosts configuration**](setup.md#setting-up-virtual-hosts), this URL should look like `http(s)://your_server_ip/api/rest/`.
* production - Set if this is production (true) or development (false)
* global - Set if the API is the global (true) or federated (false)
* name - Name to be displayed in the sheet header
* favicon - Icon filename (without the format extension) to be displayed in the sheet header. Icons are located at public/.
* description - Text or JSX to be displayed in the home page
* logo - Logo filename (without the format extension) to be dipslayed on the top-left corner, in the header. Images are located at src/images/.
* primaryColor - Color of the header and additional regions along the whole web page
* secondaryColor - Color of non-primary regions along the whole web page
* searchExample - Search example: This is shown in search bars as placeholder when they are empty
* optionsField - Field in projects metadata to be used as options in the browse selector and the data summary. If no options field is passed then ignore the options label and options nice names.
* optionsLabel - Name of the options in the browse selector and the data summary
* optionsNiceNames - Nice names for every possible value in the options field. Non-matching values will remain as they are.
* queryFields - Fields to be queried in the search and advanced search pages and their configurations

## Loader

### .env file

⚠️ No sensible default value is provided for any of these fields, they **need to be defined** ⚠️

An `.env` file must be created in the **loader** folder. The file [**.env.git**](../loader/.env.git) can be taken as an example. The file must contain the following environment variables (the DB user needs to have writing rights):

| key              | value   | description                                     |
| ---------------- | ------- | ----------------------------------------------- |
| DB_AUTH_USER         | string  | db user                                         |
| DB_AUTH_PASSWORD      | string  | db password                                     |
| DB_SERVER          | `<url>` | url of the db server                            |
| DB_PORT          | number  | port of the db server                           |
| DB_NAME      | string  | name of the dbcollection                        |
| DB_AUTHSOURCE    | string  | authentication db                               |

Example:

```
DB_SERVER=my_mongo_container
DB_PORT=27017
DB_NAME=mddb_db
DB_AUTH_USER=user_rw
DB_AUTH_PASSWORD=pwd_rw
DB_AUTHSOURCE=mddb_db
```

The **DB_SERVER** must be the same name as the **mongodb container_name** in the [**docker-compose.yml**](../docker-compose-git.yml) file.

The **DB_NAME** must be the same used in the [**mongo-init.js**](../mongo-init.js) file.

The credentials **DB_AUTH_USER** and **DB_AUTH_PASSWORD** must be the same defined in the [**mongo-init.js**](../mongo-init.js) file with the **readWrite role**.

## REST API

### .env file

⚠️ No sensible default value is provided for any of these fields, they **need to be defined** ⚠️

An `.env` file must be created in the **rest** folder. The file [**.env.git**](../rest/.env.git) can be taken as an example. The file must contain the following environment variables (the DB user needs to have reading rights):

| key              | value   | description                                     |
| ---------------- | ------- | ----------------------------------------------- |
| DB_AUTH_USER         | string  | db user                                         |
| DB_AUTH_PASSWORD      | string  | db password                                     |
| DB_SERVER          | `<url>` | url of the db server                            |
| DB_PORT          | number  | port of the db server                           |
| DB_NAME      | string  | name of the dbcollection                        |
| DB_AUTHSOURCE    | string  | authentication db                               |
| LISTEN_PORT    | number  | port to query the API                               |

Example:

```
DB_SERVER=my_mongo_container
DB_PORT=27017
DB_NAME=mddb_db
DB_AUTH_USER=user_r
DB_AUTH_PASSWORD=pwd_r
DB_AUTHSOURCE=mddb_db
LISTEN_PORT=3000
```

The **DB_SERVER** must be the same name as the **mongodb container_name** in the [**docker-compose.yml**](../docker-compose-git.yml) file.

The **DB_NAME** must be the same used in the [**mongo-init.js**](../mongo-init.js) file.

The credentials **DB_AUTH_USER** and **DB_AUTH_PASSWORD** must be the same defined in the [**mongo-init.js**](../mongo-init.js) file with the **read** role.

The **LISTEN_PORT** must be the same exposed in the [**REST Dockerfile**](../rest/Dockerfile).

## MongoDB

### mongo-init.js file

This file is used for **initializing mongoDB** in docker-compose. It contains a script that **creates two users** in the **mddb_db** database: one with **read / write** permissions (it will be used by the **loader**) and the other with **read** permissions (it will be used by the **REST API**).

```js
// Switch to the desired database
db = db.getSiblingDB('mddb_db'); // Replace 'mddb_db' with your database name

// Create a user with readWrite permissions on 'mddb_db' database. This user will be used for the loader
db.createUser({
  user: 'user_rw',
  pwd: 'pwd_rw',
  roles: [
    { role: 'readWrite', db: 'mddb_db' }
  ]
});

// Create a user with read permissions on 'mddb_db' database. This user will be used for the REST API
db.createUser({
  user: 'user_r',
  pwd: 'pwd_r',
  roles: [
    { role: 'read', db: 'mddb_db' }
  ]
});
```

Please modify the values of **user** and **pwd** for both users and be sure that they match with the ones defined in the `.env` files of the **loader** and **rest** blocks.

## Docker Compose

### docker-compose.yml file

A `docker-compose.yml` file must be created in the root of the project. The file [**docker-compose-git.yml**](../docker-compose-git.yml) can be taken as an example.

Once created, open the **docker-compose.yml** with an editor and modify the volumes' routes.

Take a look as well at the **client/rest ports**. They may change depending on the host configuration. Changing the ports **inside the containers** implies to change it as well in the [**client Dockerfile**](../client/Dockerfile) and in the [**REST API Dockerfile**](../rest/Dockerfile). If changing the ports **on the host machine**, take into account that they must mach with the ones defined in the [**Set Up of the Virtual Hosts**](setup.md#setting-up-virtual-hosts).

Finally, a root credentials **MONGO_INITDB_ROOT_USERNAME** and **MONGO_INITDB_ROOT_USERNAME** for the mongoDB database must be defined as well in this file.

```yaml
services:
  loader:
    image: loader_image   # name of loader image
    container_name: my_loader   # name of loader container
    platform: linux/amd64
    build:
      context: ./loader   # folder to search Dockerfile for this image
    depends_on:
      - mongodb
    working_dir: /data
    volumes:
      - /path/to/loader/files:/data   # path where the loader will look for files
    networks:
      - my_network

  workflow:
    image: workflow_image
    container_name: my_workflow
    platform: linux/amd64
    build:
      context: ./workflow   # folder to search Dockerfile for this image
    working_dir: /data
    volumes:
      - /path/to/workflow/files:/data

  client:
    image: client_image
    container_name: my_client
    platform: linux/amd64
    build:
      context: ./client  # folder to search Dockerfile for this image
    ports:
      - "8080:80"  # port mapping, be aware that the second port is the same exposed in the client/Dockerfile

  rest:
    image: rest_image
    container_name: my_rest
    platform: linux/amd64
    build:
      context: ./rest   # folder to search Dockerfile for this image
    depends_on:
      - mongodb
    ports:
      - "8081:3000"   # port mapping, be aware that the second port is the same exposed in the rest/Dockerfile
    networks:
      - my_network

  mongodb:
    container_name: my_mongo_container
    image: mongo:6
    environment:
      MONGO_INITDB_ROOT_USERNAME: ROOT_USER
      MONGO_INITDB_ROOT_PASSWORD: ROOT_PASSWORD
    ports:
      - "27017:27017"
    volumes:
      - /path/to/db:/data/db  # path where the database will be stored (outside the container, in the host machine)
      - ./mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro # path to the initialization script
    networks:
      - my_network

networks:
  my_network: 
    name: my_network    # network name
```