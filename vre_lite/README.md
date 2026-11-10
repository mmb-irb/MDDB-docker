# VRE lite

The **VRE lite** is a **Nuxt** application.

For this project, the following repo has been used:

https://github.com/mmb-irb/mddb-vre/

## Dockerfile

The [Dockerfile](Dockerfile) clones the [VRE lite repository](https://github.com/mmb-irb/mddb-vre/) at the version given in the `VERSION` build argument (or the latest release), writes its `.env` from the build arguments (MinIO, database, node and stack names...), builds the Nuxt app, and adds the MinIO client `mc` (from the `pgsty/mc` image). On start it waits for MinIO to be healthy, so VRE lite stays down while MinIO is down.
