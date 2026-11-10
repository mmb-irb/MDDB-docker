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

The [Dockerfile](Dockerfile) clones the [REST API repository](https://github.com/mmb-irb/MDDB-REST-API/) at the version given in the `VERSION` build argument (or the latest release), installs it, writes its `.env` from the build arguments (database server and users, port, host name, node name), copies the trajectory converter, and runs it with **pm2** as an unprivileged user.

The REST API connects to MongoDB **once, when it starts**: if it started before MongoDB was ready (first deploy, reboot), restart it with `docker service update --force <stack>_rest`.
