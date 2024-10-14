// Switch to the desired database
db = db.getSiblingDB('DB_NAME'); // Replace 'mddb_db' with your database name

// Create a user with readWrite permissions on 'mddb_db' database. This user will be used for the loader
db.createUser({
  user: 'LOADER_DB_LOGIN',
  pwd: 'LOADER_DB_PASSWORD',
  roles: [
    { role: 'readWrite', db: 'DB_NAME' }
  ]
});

// Create a user with read permissions on 'mddb_db' database. This user will be used for the REST API
db.createUser({
  user: 'REST_DB_LOGIN',
  pwd: 'REST_DB_PASSWORD',
  roles: [
    { role: 'read', db: 'DB_NAME' }
  ]
});