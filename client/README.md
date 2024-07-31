# Client

The **website client** is a **React App**.

For this project, the following repo has been used:

https://mmb.irbbarcelona.org/gitlab/d.beltran.anadon/mdposit_client

## Config files

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

* api - API URL to query. It must be an absolute URL. Take into account that, depending on the [**Virtual Hosts configuration**](setup#setting-up-virtual-hosts), this URL should look like `http(s)://your_server_ip/api/rest/`.
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

## Dockerfiles

In this repo there are two dockerfiles: one for creating the container from the **client build** and another for creting it from the **client repo**.

### Dockerfile (build)

This Dockerfile is used taking as a starting point the **build** of the client. It copies the build folder into a **nginx** container and exposes the port 80.

```Dockerfile
# Use nginx Alpine Linux as base image
FROM nginx:alpine

# Copy the built React app to nginx
COPY build /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

### Dockerfile2 (repo)

This Dockerfile is used taking as a starting point the **repository** of the client. It **creates the build** from the repo and then, it copies the build into a **nginx** container and exposes the port **80**.

```Dockerfile
# Stage 1: Build the React app
FROM node:16.19.1 AS build

# Set working directory
WORKDIR /app

# Copy mdposit_client directory to /app (in a future, git clone repo)
COPY mdposit_client ./
COPY .env ./
COPY host-config.js ./src

# Install dependencies
RUN npm install

# Build the React app
RUN npm run build

# Stage 2: Serve the React app with nginx
FROM nginx:alpine

# Copy the built React app from the previous stage
COPY --from=build /app/build /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

As docker compose uses the **Dockerfile** file by default, please **change the name** of this file if using it as a Docekrfile.