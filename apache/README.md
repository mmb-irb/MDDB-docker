# Apache

The Apache HTTP Server, colloquially called Apache, is a **Web server** application notable for playing a key role in the initial growth of the World Wide Web:

https://hub.docker.com/_/httpd

## Dockerfile

The [Dockerfile](Dockerfile) starts from the official `httpd:2.4` image and copies the Apache configuration selected with `APACHE_CONFIG` in the `.env`:

| File | Use |
| --- | --- |
| [apache-config.conf](apache-config.conf) | default: Apache terminates TLS with the certificates of `APACHE_CERTS_VOLUME_PATH` |
| [apache-config-florida.conf](apache-config-florida.conf) | node behind an external proxy that terminates TLS |
| [apache-config-dual.conf](apache-config-dual.conf) | node served under two domain names (the second one, `NEW_SERVER_URL`, is not filled by the build: edit it by hand) |
| [apache-mod-md.conf](apache-mod-md.conf) | added when `CERT_METHOD=mod_md` (Let's Encrypt without port 80, see [certificates](../readme/storage.md#certificates)) |

The configuration has placeholders (`APACHE_HTTPS_OUTER_PORT`, `REST_INNER_PORT`, `SERVER_URL`, `SSL_CERTIFICATE`...) that the build replaces with the values of the `.env`. So **after changing any of these values, rebuild Apache**. The certificates are not copied into the image: they are mounted from `APACHE_CERTS_VOLUME_PATH`.

The default configuration:

* redirects `http` to `https` (and serves `/.well-known/acme-challenge/` for Let's Encrypt),
* serves the website client at `/`, the REST API at `/api/`, VRE lite at `/vre_lite/` and the MinIO console at `/minio/`,
* serves the MinIO API on its own port, `APACHE_MINIO_OUTER_PORT`.

Apache listens inside its container on the **outer** port numbers, so `APACHE_HTTPS_INNER_PORT` must be equal to `APACHE_HTTPS_OUTER_PORT` and `APACHE_MINIO_INNER_PORT` equal to `APACHE_MINIO_OUTER_PORT`.
