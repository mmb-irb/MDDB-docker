#!/usr/bin/env python3
"""Get or renew the Let's Encrypt certificate of this node and reload apache when it changes.

Run it from cron as a user in the docker group (twice a day is the usual):

    17 3,15 * * * cd /path/to/MDDB-docker && scripts/renew-certs.py >> ~/renew-certs.log 2>&1

What it does:
  1. certbot (in a container) asks Let's Encrypt for a certificate for CERT_DOMAINS, using the HTTP-01
     challenge in the webroot APACHE_CERTS_VOLUME_PATH/acme (served by apache under /.well-known/acme-challenge/).
     certbot does nothing if the current certificate is not close to expiry.
  2. If the certificate in letsencrypt/ differs from the one apache uses (le_fullchain.pem / le_privkey.pem),
     it copies it there and does a graceful reload of apache.
  3. It checks that apache now serves the new certificate.

Variables read from .env:
  APACHE_CERTS_VOLUME_PATH  folder mounted in apache as /usr/local/apache2/conf/ssl
  CERT_DOMAINS              comma-separated names for the certificate (default: MINIO_URL)
  SSL_CERTIFICATE / SSL_CERT_KEY must be le_fullchain.pem / le_privkey.pem for apache to use it

Any failure raises an error and the script exits with non-zero status.
"""

import argparse
import hashlib
import ssl
import subprocess
import time
from datetime import datetime
from pathlib import Path

CERTBOT_IMAGE = 'certbot/certbot:v4.0.0'
ALPINE_IMAGE = 'alpine:3.24'
LIVE_CERT = 'le_fullchain.pem'
LIVE_KEY = 'le_privkey.pem'


def log(message: str):
    print(f'[{datetime.now().isoformat(timespec="seconds")}] {message}', flush=True)


def run(command: list, capture: bool = False, stdin=None, stderr=None) -> str:
    result = subprocess.run(command, check=True, text=True, stdin=stdin, stderr=stderr,
                            stdout=subprocess.PIPE if capture else None)
    return result.stdout if capture else ''


def read_env(env_path: Path) -> dict:
    env = {}
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def read_root_file(certs_path: str, relative_path: str) -> str:
    """Read a file of the root-owned certs folder through a container."""
    return run(['docker', 'run', '--rm', '-v', f'{certs_path}:/c:ro', ALPINE_IMAGE,
                'sh', '-ec', f'if [ -e "/c/{relative_path}" ]; then cat "/c/{relative_path}"; fi'], capture=True)


def first_cert_fingerprint(pem: str) -> str:
    """sha256 of the first certificate (the leaf) of a PEM chain."""
    begin, end = '-----BEGIN CERTIFICATE-----', '-----END CERTIFICATE-----'
    start = pem.index(begin)
    leaf = pem[start:pem.index(end, start) + len(end)] + '\n'
    return hashlib.sha256(ssl.PEM_cert_to_DER_cert(leaf)).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--stack', default='my_stack', help='docker stack name (default: my_stack)')
    parser.add_argument('--env', default='.env', help='path to the .env file (default: .env)')
    parser.add_argument('certbot_args', nargs='*',
                        help='extra arguments for certbot after "--" (e.g. -- --force-renewal). Do not use --staging: '
                             'the test certificate would be copied to apache. Test with certbot by hand instead.')
    args = parser.parse_args()

    env = read_env(Path(args.env))
    certs_path = env['APACHE_CERTS_VOLUME_PATH']
    domains = [d.strip() for d in (env.get('CERT_DOMAINS') or env['MINIO_URL']).split(',') if d.strip()]
    if not domains:
        raise RuntimeError('No names for the certificate: set CERT_DOMAINS (or MINIO_URL) in .env')
    cert_name = domains[0]
    log(f'Domains: {", ".join(domains)} (certs folder {certs_path})')

    # 1. Get or renew the certificate (certbot keeps it if it is not close to expiry)
    certbot_command = [
        'docker', 'run', '--rm',
        '-v', f'{certs_path}/letsencrypt:/etc/letsencrypt',
        '-v', f'{certs_path}/acme:/webroot',
        CERTBOT_IMAGE, 'certonly',
        '--non-interactive', '--agree-tos', '--register-unsafely-without-email',
        '--webroot', '-w', '/webroot',
        '--cert-name', cert_name, '--keep-until-expiring',
    ]
    for domain in domains:
        certbot_command += ['-d', domain]
    run(certbot_command + args.certbot_args)

    # 2. Copy it to the files apache uses, if it changed
    new_pem = read_root_file(certs_path, f'letsencrypt/live/{cert_name}/fullchain.pem')
    if not new_pem:
        raise RuntimeError(f'certbot finished but there is no letsencrypt/live/{cert_name}/fullchain.pem')
    new_fingerprint = first_cert_fingerprint(new_pem)
    current_pem = read_root_file(certs_path, LIVE_CERT)
    if current_pem and first_cert_fingerprint(current_pem) == new_fingerprint:
        log(f'{LIVE_CERT} is already up to date, nothing to do')
        return

    log(f'New certificate {new_fingerprint}: copying it to {LIVE_CERT} / {LIVE_KEY}')
    run(['docker', 'run', '--rm', '-v', f'{certs_path}:/c', ALPINE_IMAGE, 'sh', '-ec',
         f'cd /c; '
         f'cp -L letsencrypt/live/{cert_name}/privkey.pem {LIVE_KEY}.tmp; chmod 600 {LIVE_KEY}.tmp; '
         f'cp -L letsencrypt/live/{cert_name}/fullchain.pem {LIVE_CERT}.tmp; chmod 644 {LIVE_CERT}.tmp; '
         f'mv {LIVE_KEY}.tmp {LIVE_KEY}; mv {LIVE_CERT}.tmp {LIVE_CERT}'])

    if env.get('SSL_CERTIFICATE') != LIVE_CERT or env.get('SSL_CERT_KEY') != LIVE_KEY:
        raise RuntimeError(f'Certificate copied, but .env has SSL_CERTIFICATE={env.get("SSL_CERTIFICATE")} '
                           f'SSL_CERT_KEY={env.get("SSL_CERT_KEY")}: apache does not use {LIVE_CERT} / {LIVE_KEY}')

    # 3. Graceful reload of every apache container of the stack, then check what is served
    containers = run(['docker', 'ps', '-q', '--filter',
                      f'label=com.docker.swarm.service.name={args.stack}_apache'], capture=True).split()
    if not containers:
        raise RuntimeError(f'No running container of service {args.stack}_apache to reload')
    for container in containers:
        log(f'Reloading apache in container {container}')
        run(['docker', 'exec', container, 'httpd', '-k', 'graceful'])

    served_fingerprint = None
    for _ in range(10):
        time.sleep(2)
        served_pem = run(['openssl', 's_client', '-connect', f'127.0.0.1:{env.get("APACHE_HTTPS_OUTER_PORT", "443")}',
                          '-servername', cert_name], capture=True, stdin=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
        served_fingerprint = first_cert_fingerprint(served_pem)
        if served_fingerprint == new_fingerprint:
            log('apache serves the new certificate')
            return
    raise RuntimeError(f'apache still serves {served_fingerprint}, expected {new_fingerprint}')


if __name__ == '__main__':
    main()
