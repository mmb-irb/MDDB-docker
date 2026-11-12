# REST API

The **REST API** is a **NodeJS + Express** application.

For this project, the following repo has been used:

https://github.com/mmb-irb/MDDB-REST-API/

## Trajectory format converter

The REST API converts trajectories from its internal `.bin` format to other formats (XTC, TRR, NetCDF, DCD) with a small C++ executable that relies on a [customized chemfiles fork](https://github.com/d-beltran/chemfiles).

This executable is **precompiled** and stored in this folder (`chemfiles_bin_converter`), so the Dockerfiles just copy it into the REST API `build` folder. No chemfiles, cmake or compiler is needed to build the image.

The executable is fully statically linked, so it does not depend on any library in the image. It only runs on `linux/amd64`.

It must be rebuilt whenever the chemfiles fork or the converter source (`assembly/chemfiles_bin_converter.cpp` in the REST API) changes:

```bash
./build-chemfiles-converter.sh <chemfiles fork directory> <REST API directory>
```

The script builds it inside the same base image used by the Dockerfiles and prints the commits it was built from.

> [!WARNING]
> The executable must be compatible with the REST API version being deployed. Update it before (or together with) a REST API release which changes the converter arguments.

## Dockerfile

The [Dockerfile](Dockerfile) clones the [REST API repository](https://github.com/mmb-irb/MDDB-REST-API/) at the version given in the `VERSION` build argument (or the latest release), installs it, writes its `.env` from the build arguments (database server and users, port, host name, node name), copies the [host configuration file](#host-configuration-file) if there is one, copies the trajectory converter, and runs it with **pm2** as an unprivileged user.

## Host configuration file

The REST API host configuration sets the service name, description and accession example in its swagger docs, and how it behaves depending on the requesting host:
whether unpublished projects are hidden (`production`), whether it is the global API (`global`) or which collection it serves (`collection`).

To give this node its own configuration, create the file **`rest/config.yml`**.
It is ignored by git, so every node keeps its own one.
The build copies it as `config.yml` at the root of the REST API repository, where the API looks for it.
Without it the API uses its default configuration for every host: a generic `MDposit` node with the accession example `A0001` which **shows unpublished projects**.

Start from one of the examples in the REST API repository, which describe every field and its default value:

* [example-single-config.yml](https://github.com/mmb-irb/MDDB-REST-API/blob/master/example-single-config.yml): one single configuration, for a node with one URL or which behaves the same in all of them.
* [example-multiple-config.yml](https://github.com/mmb-irb/MDDB-REST-API/blob/master/example-multiple-config.yml): a different configuration for each URL (domain) which serves the API, e.g. a production and a development domain.

For instance, a production node with one URL only needs:

```yaml
name: My node
description: The federated node server of my lab
accession: A0001
production: true
```

Missing fields take their default values, and unknown fields stop the API when it starts (see its logs).
REST API versions up to v0.0.19 ignore `rest/config.yml` and keep their own configuration, which includes every node.

The configuration is part of the build, so **rebuild the REST API after changing it**:

```bash
python3 scripts/rebuild.py -s rest -t my_stack
```

In development mode ([Dockerfile.dev](Dockerfile.dev)) `rest/config.yml` is used the same way.

The REST API connects to MongoDB **once, when it starts**: if it started before MongoDB was ready (first deploy, reboot), restart it with `docker service update --force <stack>_rest`.
