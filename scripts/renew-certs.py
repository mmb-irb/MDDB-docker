#!/usr/bin/env python3
"""Get or renew the Let's Encrypt certificate of this node and reload apache when it changes.

Run it from cron as a user in the docker group (twice a day is the usual):

    17 3,15 * * * cd /path/to/MDDB-docker && scripts/renew-certs.py >> ~/renew-certs.log 2>&1

Two ways to get the certificate (CERT_METHOD in .env):
  certbot (default)  certbot (in a container) asks Let's Encrypt for a certificate for CERT_DOMAINS, using the HTTP-01
                     challenge in the webroot APACHE_CERTS_VOLUME_PATH/acme (served by apache under
                     /.well-known/acme-challenge/). Needs port 80 reachable from the internet. certbot does nothing
                     if the current certificate is not close to expiry.
  mod_md             apache itself (mod_md, built in with CERT_METHOD=mod_md) gets and renews the certificate in
                     APACHE_CERTS_VOLUME_PATH/md with the TLS-ALPN-01 challenge. Needs only port 443. A renewed
                     certificate waits in md/staging/ until apache reloads, so this script reloads apache first.

Then, in both cases:
  1. If the certificate differs from the one apache uses (le_fullchain.pem / le_privkey.pem), it copies it there
     (never a certificate from the Let's Encrypt staging CA) and does a graceful reload of apache.
  2. It checks that apache now serves the new certificate.

Variables read from .env:
  APACHE_CERTS_VOLUME_PATH  folder mounted in apache as /usr/local/apache2/conf/ssl
  CERT_METHOD               certbot (default) or mod_md
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


def run(command: list, capture: bool = False, stdin=None, stderr=None, input_text: str = None) -> str:
    result = subprocess.run(command, check=True, text=True, stdin=stdin, stderr=stderr, input=input_text,
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
    """Read a file of the root-owned certs folder through a container ('' if it does not exist)."""
    return run(['docker', 'run', '--rm', '-v', f'{certs_path}:/c:ro', ALPINE_IMAGE,
                'sh', '-ec', f'if [ -e "/c/{relative_path}" ]; then cat "/c/{relative_path}"; fi'], capture=True)


def first_cert(pem: str) -> str:
    """The first certificate (the leaf) of a PEM chain."""
    begin, end = '-----BEGIN CERTIFICATE-----', '-----END CERTIFICATE-----'
    start = pem.index(begin)
    return pem[start:pem.index(end, start) + len(end)] + '\n'


def first_cert_fingerprint(pem: str) -> str:
    """sha256 of the first certificate (the leaf) of a PEM chain."""
    return hashlib.sha256(ssl.PEM_cert_to_DER_cert(first_cert(pem))).hexdigest()


def cert_issuer(pem: str) -> str:
    return run(['openssl', 'x509', '-noout', '-issuer'], capture=True, input_text=first_cert(pem)).strip()


def apache_containers(stack: str) -> list:
    containers = run(['docker', 'ps', '-q', '--filter',
                      f'label=com.docker.swarm.service.name={stack}_apache'], capture=True).split()
    if not containers:
        raise RuntimeError(f'No running container of service {stack}_apache')
    return containers


def reload_apache(stack: str):
    for container in apache_containers(stack):
        log(f'Reloading apache in container {container}')
        run(['docker', 'exec', container, 'httpd', '-k', 'graceful'])


def get_with_certbot(certs_path: str, domains: list, certbot_args: list) -> tuple:
    """Get or renew the certificate with certbot. Returns the (chain, key) paths inside the certs folder."""
    cert_name = domains[0]
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
    run(certbot_command + certbot_args)
    return f'letsencrypt/live/{cert_name}/fullchain.pem', f'letsencrypt/live/{cert_name}/privkey.pem'


def get_with_mod_md(certs_path: str, domains: list, stack: str) -> tuple:
    """Activate a certificate renewed by mod_md, if any. Returns the (chain, key) paths inside the certs folder."""
    md_name = domains[0]
    staged = f'md/staging/{md_name}/pubcert.pem'
    if read_root_file(certs_path, staged):
        # mod_md moves a renewed certificate from staging/ to domains/ when apache reloads
        log(f'mod_md has a new certificate in {staged}: reloading apache to install it')
        reload_apache(stack)
        for _ in range(15):
            time.sleep(2)
            if not read_root_file(certs_path, staged):
                break
        else:
            raise RuntimeError(f'{staged} is still there after reloading apache: see the apache logs')
    chain = f'md/domains/{md_name}/pubcert.pem'
    if not read_root_file(certs_path, chain):
        raise RuntimeError(f'mod_md has no certificate yet ({chain} does not exist): see the apache logs '
                           f'and md/staging/{md_name}/job.json')
    return chain, f'md/domains/{md_name}/privkey.pem'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--stack', default='my_stack', help='docker stack name (default: my_stack)')
    parser.add_argument('--env', default='.env', help='path to the .env file (default: .env)')
    parser.add_argument('certbot_args', nargs='*',
                        help='extra arguments for certbot after "--" (e.g. -- --force-renewal). Do not use --staging: '
                             'test with certbot by hand instead.')
    args = parser.parse_args()

    env = read_env(Path(args.env))
    certs_path = env['APACHE_CERTS_VOLUME_PATH']
    method = env.get('CERT_METHOD') or 'certbot'
    domains = [d.strip() for d in (env.get('CERT_DOMAINS') or env['MINIO_URL']).split(',') if d.strip()]
    if not domains:
        raise RuntimeError('No names for the certificate: set CERT_DOMAINS (or MINIO_URL) in .env')
    log(f'Domains: {", ".join(domains)} (method {method}, certs folder {certs_path})')

    # 1. Get the current certificate
    if method == 'certbot':
        chain, key = get_with_certbot(certs_path, domains, args.certbot_args)
    elif method == 'mod_md':
        if args.certbot_args:
            raise RuntimeError('certbot arguments make no sense with CERT_METHOD=mod_md')
        chain, key = get_with_mod_md(certs_path, domains, args.stack)
    else:
        raise RuntimeError(f'Unknown CERT_METHOD={method} (certbot or mod_md)')

    # 2. Copy it to the files apache uses, if it changed
    new_pem = read_root_file(certs_path, chain)
    if not new_pem:
        raise RuntimeError(f'There is no {chain}')
    new_fingerprint = first_cert_fingerprint(new_pem)
    current_pem = read_root_file(certs_path, LIVE_CERT)
    if current_pem and first_cert_fingerprint(current_pem) == new_fingerprint:
        log(f'{LIVE_CERT} is already up to date, nothing to do')
        return
    issuer = cert_issuer(new_pem)
    if 'STAGING' in issuer.upper():
        raise RuntimeError(f'{chain} comes from the Let\'s Encrypt staging CA ({issuer}): not installing it')

    log(f'New certificate {new_fingerprint} ({issuer}): copying it to {LIVE_CERT} / {LIVE_KEY}')
    run(['docker', 'run', '--rm', '-v', f'{certs_path}:/c', ALPINE_IMAGE, 'sh', '-ec',
         f'cd /c; '
         f'cp -L {key} {LIVE_KEY}.tmp; chmod 600 {LIVE_KEY}.tmp; '
         f'cp -L {chain} {LIVE_CERT}.tmp; chmod 644 {LIVE_CERT}.tmp; '
         f'mv {LIVE_KEY}.tmp {LIVE_KEY}; mv {LIVE_CERT}.tmp {LIVE_CERT}'])

    if env.get('SSL_CERTIFICATE') != LIVE_CERT or env.get('SSL_CERT_KEY') != LIVE_KEY:
        raise RuntimeError(f'Certificate copied, but .env has SSL_CERTIFICATE={env.get("SSL_CERTIFICATE")} '
                           f'SSL_CERT_KEY={env.get("SSL_CERT_KEY")}: apache does not use {LIVE_CERT} / {LIVE_KEY}')

    # 3. Graceful reload of apache, then check what is served
    reload_apache(args.stack)
    served_fingerprint = None
    for _ in range(10):
        time.sleep(2)
        served_pem = run(['openssl', 's_client', '-connect', f'127.0.0.1:{env.get("APACHE_HTTPS_OUTER_PORT", "443")}',
                          '-servername', domains[0]], capture=True, stdin=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
        served_fingerprint = first_cert_fingerprint(served_pem)
        if served_fingerprint == new_fingerprint:
            log('apache serves the new certificate')
            return
    raise RuntimeError(f'apache still serves {served_fingerprint}, expected {new_fingerprint}')


if __name__ == '__main__':
    main()
