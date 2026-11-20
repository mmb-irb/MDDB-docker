# Apache

The Apache HTTP Server, colloquially called Apache, is a **Web server** application notable for playing a key role in the initial growth of the World Wide Web:

https://hub.docker.com/_/httpd

## Dockerfile

The [Dockerfile](Dockerfile) starts from the official `httpd:2.4` image and copies the Apache configuration selected with `APACHE_CONFIG` in the `.env`:

| File | Use |
| --- | --- |
| [apache-config.conf](apache-config.conf) | default: Apache terminates TLS with its own Let's Encrypt certificate |
| [apache-config-florida.conf](apache-config-florida.conf) | node behind an external proxy that terminates TLS |
| [apache-config-dual.conf](apache-config-dual.conf) | node served under two domain names (the second one, `NEW_SERVER_URL`, is not filled by the build: edit it by hand, and add it to `CERT_DOMAINS`) |
| [apache-mod-md.conf](apache-mod-md.conf) | added to every configuration that terminates TLS: mod_md gets, serves and renews the Let's Encrypt certificate ([certificates](../readme/storage.md#certificates)) |
| [httpd-md-foreground](httpd-md-foreground) | container command: apache, plus a graceful restart whenever mod_md has a new certificate |

The configuration has placeholders (`APACHE_HTTPS_OUTER_PORT`, `REST_INNER_PORT`, `SERVER_URL`, `CERT_DOMAINS`...) that the build replaces with the values of the `.env`. So **after changing any of these values, rebuild Apache**. The build stops if `CERT_EMAIL` is empty or a name of the certificate is an IP address. mod_md keeps the certificates in `APACHE_CERTS_VOLUME_PATH/md/`, outside the image.

The default configuration:

* redirects `http` to `https` (mod_md answers the Let's Encrypt challenges),
* serves the website client at `/`, the REST API at `/api/`, VRE lite at `/vre_lite/` and the MinIO console at `/minio/`,
* serves the MinIO API on its own port, `APACHE_MINIO_OUTER_PORT`.

Apache listens inside its container on the **outer** port numbers, so `APACHE_HTTPS_INNER_PORT` must be equal to `APACHE_HTTPS_OUTER_PORT` and `APACHE_MINIO_INNER_PORT` equal to `APACHE_MINIO_OUTER_PORT`.
