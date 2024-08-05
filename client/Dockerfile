# Use nginx Alpine Linux as base image
FROM nginx:alpine

# Copy the built React app to nginx
# COPY build /usr/share/nginx/html

# Define working dir
WORKDIR /app

# Clone mdposit-client-build repo
RUN git clone https://mmb.irbbarcelona.org/gitlab/gbayarri/mdposit-client-build

# Copy the built React app to nginx
COPY /app/mdposit-client-build/build /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]