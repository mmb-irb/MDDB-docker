# Update services

This section explains in detail how to **update** one or more **services** of the docker swarm.

## Check & update

An **update script** is provided for checking the **versions** of all the running services and see if there are **updates** available. This same script, located in [**scripts/update.py**](../scripts/update.py), allows to **update** one or all the updatable services.

How to execute the script from the root of this repository:

```sh
python3 scripts/update.py
```

Example of output:

```sh
============================================================
📊 VERSION SUMMARY
============================================================
Service         Current      Latest       Status         
------------------------------------------------------------
client          0.0.2        0.0.2        ✅ Up to date   
rest            0.0.1        0.0.1        ✅ Up to date   
vre_lite        0.0.1        0.0.1        ✅ Up to date   
loader          0.0.1        0.0.1        ✅ Up to date   
workflow        0.1.1        0.1.4        🆙 Updatable    

============================================================
🎯 1 service(s) can be updated:
   • workflow: 0.1.1 -> 0.1.4

============================================================
🛠️  INTERACTIVE UPDATE MENU
============================================================
Available actions:
1. Update all services
2. Update specific service
3. Show version summary
4. Re-check versions
5. Exit
```

In this case, the workflow service is **updatable**, so after selecting options 1 or 2, the **service** is updated and the following output is shown:

```sh
============================================================
📊 VERSION SUMMARY
============================================================
Service         Current      Latest       Status         
------------------------------------------------------------
client          0.0.2        0.0.2        ✅ Up to date   
rest            0.0.1        0.0.1        ✅ Up to date   
vre_lite        0.0.1        0.0.1        ✅ Up to date   
loader          0.0.1        0.0.1        ✅ Up to date   
workflow        0.1.4        0.1.4        ✅ Up to date   

============================================================
✅ All services are up to date!

============================================================
🛠️  INTERACTIVE UPDATE MENU
============================================================
✅ No services need updating!
```

The script recognises the **services in development** and marks them as non-updatable:

```sh
============================================================
📊 VERSION SUMMARY
============================================================
Service         Current      Latest       Status         
------------------------------------------------------------
client          0.0.2        0.0.2        ✅ Up to date   
rest            0.0.1        0.0.1        ✅ Up to date   
vre_lite        dev          0.0.2        📦 Development  
loader          0.0.1        0.0.1        ✅ Up to date   
workflow        0.1.4        0.1.4        ✅ Up to date   

============================================================
✅ All services are up to date!

============================================================
🛠️  INTERACTIVE UPDATE MENU
============================================================
✅ No services need updating!

1. Re-check versions
2. Exit
```

## Rebuild service(s)

A **rebuild script** is provided for rebuilding **one or more services** in an **automatic** way. Please execute the script, located in [**scripts/rebuild.py**](../scripts/rebuild.py). 

How to execute the help script from the root of this repository:

```sh
python3 scripts/rebuild.py -h
```

Example for rebuilding the **client** and **vre_lite** services from the **my_stack** stack: 

```sh
python3 scripts/rebuild.py -s client vre_lite -t my_stack
```

Note that this script will **rebuild the service** to the **latest** available **version**.

For performing the same process step by step:

1. **Rebuild the Service Image Without Cache:** Use docker-compose to rebuild the image locally, targeting only the service you want to update:

    ```sh
    docker-compose build --no-cache <service_name>
    ```

2. **Update the Service in the Swarm:** In Docker Swarm, you can force the service to use the updated image by running:

    ```sh
    docker service update --force <stack_name>_<service_name>
    ```

3. **Remove Stopped Container(s):** After updating the service, the old container remains stopped, execute the following instruction for removing it:

    ```sh
    docker container prune -f
    ````

4. **Remove Unused Image(s):** After rebuilding the image, the old image remains unused, execute the following instruction for removing it:

    ```sh
    docker image prune -f
    ```

A **rollback script** is provided for rebuilding an old version of **one service** in an **automatic** way. Please execute the script, located in [**scripts/rebuild-legacy.py**](../scripts/rebuild-legacy.py). 

How to execute the help script from the root of this repository:

```sh
python3 scripts/rebuild-legacy.py -h
```

Example for rollback to the **version 0.0.1** of the **client** service from the **my_stack** stack: 

```sh
python3 scripts/rebuild-legacy.py -s client vre_lite -v 0.0.1 -t my_stack
```

## Update services versions

The versions for **each service** of the stack are stored into a database. The **status** of these services is shown in the **VRE lite service**. Though this script is **integrated** into the automatic **deploy** script, located in [**scripts/update-services-versions.py**](../scripts/update-services-versions.py), it can be used **separately** for updating all the versions in a single call:

```sh
python3 scripts/update-services-versions.py 
```

## Troubleshooting

### Builds fail to fetch/download from GitHub

When rebuilding a service (`docker-compose build`, `docker service update`, or any build that runs `git clone` / `pip install` / `curl` against GitHub inside a container), the download may **hang and time out** even though the host itself has working internet. A typical symptom is a build step or a container that stalls and eventually fails with something like:

```sh
curl: (28) Connection timed out after 5003 milliseconds
fatal: unable to access 'https://github.com/...': Failed to connect
```

Note that **DNS resolves fine** and the **TCP connection is established** — it only stalls while waiting for the first large response packet (e.g. the TLS certificate). This is the signature of an **MTU mismatch** between Docker and the host network, which is common on **cloud/OpenStack VMs** where the physical interface uses a reduced MTU (typically **1450**) for its VXLAN overlay, while Docker bridges default to **1500**. Oversized packets are silently dropped and, because Path-MTU discovery (ICMP) is usually filtered in these networks, the connection just hangs.

**Confirm it.** Compare the host NIC MTU against the Docker bridges:

```sh
ip link show | grep -E 'mtu|ens|eth|docker'
```

If the physical interface (e.g. `ens3`) shows `mtu 1450` while `docker0` / `docker_gwbridge` show `mtu 1500`, that is the problem. You can also verify by running the same download on the host network, which bypasses the Docker bridge:

```sh
docker run --rm --network host alpine sh -lc "apk add --no-cache curl && curl -Is --max-time 15 https://github.com | head -1"
```

If this succeeds while a normal `docker run` times out, the bridge MTU is confirmed as the cause.

**Fix the default bridge.** Set Docker's MTU to match the host interface in `/etc/docker/daemon.json`:

```json
{
  "mtu": 1450
}
```

Then restart Docker and re-test:

```sh
sudo systemctl restart docker
docker run --rm alpine sh -lc "apk add --no-cache curl && curl -Is --max-time 15 https://github.com | head -1"
```
