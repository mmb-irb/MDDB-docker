# MongoDB image for Podman nodes: the official image with gosu replaced by setpriv.
# 8.0 is the long-term support release; the plain mongo:8 tag moves to newer short-lived releases.
ARG MONGO_IMAGE=docker.io/library/mongo:8.0
FROM ${MONGO_IMAGE}
# Delete the gosu binary in its own layer (overwriting it would leave it in the base layer for scanners)
RUN rm /usr/local/bin/gosu
COPY gosu.sh /usr/local/bin/gosu
