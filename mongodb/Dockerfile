# MongoDB image for Podman nodes: the official image without the helpers that security scanners flag.
# 8.0 is the long-term support release; the plain mongo:8 tag moves to newer short-lived releases.
ARG MONGO_IMAGE=docker.io/library/mongo:8.0
FROM ${MONGO_IMAGE}
# Each file is deleted in its own RUN (overwriting it would leave it in the base layer for scanners):
# - gosu: built with an old Go; the entrypoint uses it to switch to the mongodb user, gosu.sh does it with setpriv
# - js-yaml 3.x: only read by the official entrypoint for a YAML --config file, which MDDB does not use
RUN rm /usr/local/bin/gosu /js-yaml.js && rm -r /opt/js-yaml
COPY gosu.sh /usr/local/bin/gosu
