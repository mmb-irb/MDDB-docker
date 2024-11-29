//use admin;

// TO TEST
/*const username = process.env.MONGO_INITDB_ROOT_USERNAME;
const password = process.env.MONGO_INITDB_ROOT_PASSWORD;
IF IT WORKS; CHECK WITH THE OTHERS!!!
*/

// Create a user with root permissions on 'admin' database.
/*db.createUser({
  user: 'MONGO_INITDB_ROOT_USERNAME',
  pwd: 'MONGO_INITDB_ROOT_PASSWORD',
  roles: [ 
    { role: 'root', db: 'admin' } 
  ]
});*/

// Switch to the desired database
db = db.getSiblingDB(process.env.MONGO_INITDB_DATABASE);

// Create a user with readWrite permissions on <MONGO_INITDB_DATABASE> database. This user will be used for the loader
db.createUser({
  user: process.env.LOADER_DB_LOGIN,
  pwd: process.env.LOADER_DB_PASSWORD,
  roles: [
    { role: 'readWrite', db: process.env.MONGO_INITDB_DATABASE }
  ]
});

// Create a user with read permissions on <MONGO_INITDB_DATABASE> database. This user will be used for the REST API
db.createUser({
  user: process.env.REST_DB_LOGIN,
  pwd: process.env.REST_DB_PASSWORD,
  roles: [
    { role: 'read', db: process.env.MONGO_INITDB_DATABASE }
  ]
});