// Switch to the desired database
db = db.getSiblingDB('DB_NAME');

// Create a user with dbOwner permissions on 'DB_NAME' database.
db.createUser({
  user: 'root',
  pwd: 'root',
  roles: [
    { role: 'dbOwner', db: 'DB_NAME' }]
});


// Create a user with readWrite permissions on 'DB_NAME' database. This user will be used for the loader
db.createUser({
  user: 'LOADER_DB_LOGIN',
  pwd: 'LOADER_DB_PASSWORD',
  roles: [
    { role: 'readWrite', db: 'DB_NAME' }
  ]
});

// Create a user with read permissions on 'DB_NAME' database. This user will be used for the REST API
db.createUser({
  user: 'REST_DB_LOGIN',
  pwd: 'REST_DB_PASSWORD',
  roles: [
    { role: 'read', db: 'DB_NAME' }
  ]
});