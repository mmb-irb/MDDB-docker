#!/bin/sh
# Build the precompiled trajectory format converter (chemfiles_bin_converter) used by the REST API
# The converter is built inside the same base image used by the REST API Dockerfile
# It is statically linked, so it does not depend on any library in the final image
#
# Usage: ./build-chemfiles-converter.sh <chemfiles fork directory> <REST API directory>
#   - The chemfiles fork is taken from its last commit (uncommitted changes are ignored)
#   - The converter source is taken from the REST API working directory (assembly/chemfiles_bin_converter.cpp)
#
# Set CONTAINER_ENGINE=podman to use podman instead of docker

set -e

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <chemfiles fork directory> <REST API directory>" >&2
    exit 1
fi

CHEMFILES_DIR=$1
API_DIR=$2
ENGINE=${CONTAINER_ENGINE:-docker}
OUTPUT_DIR=$(cd "$(dirname "$0")" && pwd)

# Prepare the sources in a temporary directory
SOURCES=$(mktemp -d)
trap 'rm -rf "$SOURCES"' EXIT
git -C "$CHEMFILES_DIR" archive --prefix=chemfiles/ HEAD | tar x -C "$SOURCES"
cp "$API_DIR/assembly/chemfiles_bin_converter.cpp" "$SOURCES/"

# Build chemfiles as a static library and then the converter as a fully static executable
"$ENGINE" run --rm --platform linux/amd64 \
    -v "$SOURCES:/src:ro" \
    -v "$OUTPUT_DIR:/out" \
    docker.io/library/nginx:alpine sh -c "
        set -e
        apk add --no-cache build-base cmake > /dev/null
        cmake -S /src/chemfiles -B /tmp/build -DBUILD_SHARED_LIBS=OFF -DCMAKE_BUILD_TYPE=Release -DCHFL_BUILD_TESTS=OFF -DCMAKE_INSTALL_PREFIX=/tmp/chemfiles > /dev/null
        cmake --build /tmp/build -j\$(nproc) > /dev/null
        cmake --install /tmp/build > /dev/null
        g++ -std=c++17 -O2 -static -s -o /out/chemfiles_bin_converter /src/chemfiles_bin_converter.cpp -I/tmp/chemfiles/include -L/tmp/chemfiles/lib -lchemfiles
        chown $(id -u):$(id -g) /out/chemfiles_bin_converter
    "

echo "Built $OUTPUT_DIR/chemfiles_bin_converter"
echo "chemfiles fork commit: $(git -C "$CHEMFILES_DIR" rev-parse --short HEAD)"
echo "REST API commit: $(git -C "$API_DIR" rev-parse --short HEAD)$(git -C "$API_DIR" diff --quiet -- assembly/chemfiles_bin_converter.cpp || echo ' (with uncommitted changes in the converter)')"
