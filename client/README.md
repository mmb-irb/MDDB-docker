# Client

The **website client** is a **React App**.

For this project, the following repo has been used:

https://mmb.irbbarcelona.org/gitlab/gbayarri/mdposit-client-build

## Dockerfile

This Dockerfile is used taking as a starting point the **build** of the client. It downloads the **build.zip** file corresponding to the **desired node**, it unzips into the **build folder** and, finally, it copies this folder into a **nginx** container and exposes the port 80.

```Dockerfile
# Use nginx Alpine Linux as base image
FROM nginx:alpine

# Define an argument that can be passed from docker-compose
ARG NODE_ID

# Set the environment variable
ENV NODE_ID=$NODE_ID

# Define working dir
WORKDIR /app

# Download and unzip mdposit-client-build repo
RUN wget https://mmb.irbbarcelona.org/gitlab/gbayarri/mdposit-client-build/-/raw/main/$NODE_ID/build.zip
RUN unzip build.zip

# Copy the built React app to nginx
COPY build /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```