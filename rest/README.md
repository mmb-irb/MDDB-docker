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

Every node has its own configuration in the file **`rest/config.yml`**, which is ignored by git.
The build copies it as `config.yml` at the root of the REST API repository, where the API looks for it.
**It is mandatory**: the build fails without it.

Root keys are the host names (domains) which serve the API, and every host has its own configuration inside.
Requests from any other host get a default configuration labeled as `(Unknown service)`, which **shows unpublished projects**.
See [example-config.yml](https://github.com/mmb-irb/MDDB-REST-API/blob/master/example-config.yml) in the REST API repository, which describes every field and its default value.
For instance, a production node with one URL:

```yaml
my-node.mddbr.eu:
    name: My node
    description: The federated node server of my lab
    accession: A0001
    production: true
```

If the requests may not reach the API with the right host name (e.g. behind a proxy which changes it), force it with `REST_URL` in the `.env` file, which is passed to the API as `HOST`.
The forced host must be configured in `rest/config.yml`.

Configuration fields at the root (a single configuration for every host), the `hosts` field, unknown fields, an empty file and a forced host which is not configured stop the API when it starts (see its logs).

Old REST API versions use other formats:

* v0.0.20: either a single configuration for every host (configuration fields at the root) or a configuration per host under `hosts`. Without the file it uses the default configuration for every host. A single configuration gets broken links (`//null`) to the OPTIMADE API and the web client in the swagger docs, so use `hosts`.
* Up to v0.0.19: `rest/config.yml` is ignored and the API keeps its own configuration, which includes every node.

The configuration is part of the build, so **rebuild the REST API after changing it**:

```bash
python3 scripts/rebuild.py -s rest -t my_stack
```

In development mode ([Dockerfile.dev](Dockerfile.dev)) `rest/config.yml` is used the same way.

The REST API connects to MongoDB **once, when it starts**: if it started before MongoDB was ready (first deploy, reboot), restart it with `docker service update --force <stack>_rest`.
