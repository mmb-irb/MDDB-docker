# Client

The **website client** is a **React App**.

For this project, the following repo has been used:

https://github.com/mmb-irb/mdposit-client-build/

## Dockerfile

This Dockerfile is used taking as a starting point the **build** of the client. It downloads the **build.zip** file corresponding to the **desired node**, it unzips into the **build folder** and, finally, it copies the content of this folder into a **nginx** container and exposes the port 80.

```Dockerfile
# Use nginx Alpine Linux as base image
FROM docker.io/library/nginx:alpine

# Define the build arguments
ARG NODE_ID
ARG CLIENT_INNER_PORT

# Define working dir
WORKDIR /app

# Download and unzip mdposit-client-build repo
RUN wget https://github.com/mmb-irb/MDposit-client-build/raw/refs/heads/main/${NODE_ID}/build.zip
RUN unzip build.zip

# Copy the built React app to nginx
RUN cp -r /app/build/* /usr/share/nginx/html

# Expose port ${CLIENT_INNER_PORT}
EXPOSE ${CLIENT_INNER_PORT}

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```