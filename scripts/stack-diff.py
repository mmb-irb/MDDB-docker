#!/usr/bin/env python3
"""Show what 'docker stack deploy' would change in the services that are running now.

'docker stack deploy' rewrites every service from the compose files. Whatever was changed by hand
with 'docker service update' (a published port, a mount, an environment variable, the number of
replicas, the stop grace period...) is lost. Run this before deploying, with the same compose files:

    python3 scripts/stack-diff.py -t my_stack
    python3 scripts/stack-diff.py -t my_stack -c docker-compose.yml -c extensions/mcp.yml

The node's own file, docker-compose.node.yml (not in git), is always added last when it exists, as
scripts/stack-deploy.py does (--no-node-file to leave it out). It reads the .env file itself
(like 'set -a; source .env; set +a'). Nothing is changed.

For what exists only in the running service (REMOVE lines) it prints the YAML to add to
docker-compose.node.yml if it was done on purpose and must stay.

Service sets:
  * in the compose files but not running (never deployed, or removed after a failure): the deploy
    creates it. Reported as information, not as a difference.
  * running but in none of the compose files: the deploy leaves it alone (it is only removed with
    'docker stack deploy --prune'). Reported as a warning: maybe an extension file is missing in -c.
  * running with fewer tasks than wanted (something failed): a deploy does not restart a service whose
    spec does not change; reported with the 'docker service update --force' to use.

Exit code: 0 when the deploy would not change any running service, 1 when it would.
"""

import argparse
import json
import os
import re
import subprocess
import sys

DEFAULT_GRACE_NS = 10 * 10**9
NODE_FILE = "docker-compose.node.yml"
STACK_LABEL_PREFIX = "com.docker.stack."


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw).stdout


def compose_config(compose_files, env_file, stack):
    """The merged compose files, interpolated with env_file, as 'docker stack deploy' would read them."""
    files = " ".join(f"-f {sh_quote(f)}" for f in compose_files)
    cmd = (f"set -a && source {sh_quote(env_file)} && set +a && "
           f"exec docker compose -p {sh_quote(stack)} {files} config --format json")
    # stderr is not captured: if docker compose fails, its message is shown
    out = subprocess.run(["bash", "-c", cmd], stdout=subprocess.PIPE, text=True)
    if out.returncode != 0:
        sys.exit("Error: 'docker compose config' failed (message above); 'docker stack deploy' would fail too.")
    return json.loads(out.stdout)


def compose_files(files, node_file=True):
    """The -c files, plus the node's own file (last, so it wins) when it exists."""
    files = list(files or ["docker-compose.yml"])
    if node_file and os.path.isfile(NODE_FILE) and NODE_FILE not in files:
        files.append(NODE_FILE)
    return files


def sh_quote(s):
    return "'" + str(s).replace("'", "'\\''") + "'"


# ---------- normalisation helpers ----------

def norm_image(image):
    image = image.split("@", 1)[0]
    for prefix in ("docker.io/library/", "docker.io/", "library/"):
        if image.startswith(prefix):
            image = image[len(prefix):]
    last = image.rsplit("/", 1)[-1]
    if ":" not in last:
        image += ":latest"
    return image


def go_duration_ns(value):
    """'30m', '1m30s', '10s', '1h' or a number of nanoseconds -> nanoseconds."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value)
    if text.isdigit():
        return int(text)
    units = {"h": 3600e9, "m": 60e9, "s": 1e9, "ms": 1e6, "us": 1e3, "µs": 1e3, "ns": 1}
    parts = re.findall(r"(\d+(?:\.\d+)?)(h|ms|us|µs|ns|m|s)", text)
    if not parts or "".join(n + u for n, u in parts) != text:
        raise ValueError(f"cannot read the duration {value!r}")
    return int(sum(float(n) * units[u] for n, u in parts))


def memory_bytes(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip().lower().rstrip("b")
    m = re.fullmatch(r"(\d+(?:\.\d+)?)([kmgt]?)", text)
    if not m:
        raise ValueError(f"cannot read the memory size {value!r}")
    return int(float(m.group(1)) * 1024 ** "_kmgt".index(m.group(2) or "_"))


def nano_cpus(value):
    if value is None:
        return None
    return int(round(float(value) * 1e9))


def norm_caps(caps):
    """Docker stores capabilities as CAP_SYS_ADMIN; compose files usually say SYS_ADMIN."""
    return {c if c.upper().startswith("CAP_") else "CAP_" + c for c in caps or []}


def fmt_ns(ns):
    if ns is None:
        return "default"
    s = ns / 1e9
    return f"{int(s // 60)}m{int(s % 60)}s" if s >= 60 else f"{s:g}s"


# ---------- what the compose files ask for ----------

def wanted(name, svc, cfg):
    deploy = svc.get("deploy") or {}
    res = deploy.get("resources") or {}
    lim, rsv = res.get("limits") or {}, res.get("reservations") or {}
    placement = deploy.get("placement") or {}
    top_vols = cfg.get("volumes") or {}
    top_nets = cfg.get("networks") or {}

    mounts = set()
    for v in svc.get("volumes") or []:
        source = v.get("source", "")
        if v.get("type") == "volume" and source in top_vols:
            source = top_vols[source].get("name") or source
        mounts.add((v.get("type"), source, v["target"], bool(v.get("read_only"))))

    ports = set()
    for p in svc.get("ports") or []:
        published = p.get("published")
        ports.add((int(p["target"]), int(published) if published not in (None, "") else None,
                   p.get("protocol", "tcp"), p.get("mode", "ingress")))

    networks = set()
    for key in (svc.get("networks") or {}):
        networks.add((top_nets.get(key) or {}).get("name") or key)

    health = svc.get("healthcheck") or {}
    mode = deploy.get("mode", "replicated")
    return {
        "image": norm_image(svc["image"]),
        "mode": mode,
        "replicas": None if mode == "global" else int(deploy.get("replicas", 1)),
        "env": {k: (None if v is None else str(v)) for k, v in (svc.get("environment") or {}).items()},
        "mounts": mounts,
        "ports": ports,
        "networks": networks,
        "labels": {k: str(v) for k, v in (deploy.get("labels") or {}).items()},
        "container_labels": {k: str(v) for k, v in (svc.get("labels") or {}).items()},
        "constraints": set(placement.get("constraints") or []),
        "max_replicas_per_node": placement.get("max_replicas_per_node") or None,
        "cpu_limit": nano_cpus(lim.get("cpus")),
        "memory_limit": memory_bytes(lim.get("memory")),
        "cpu_reservation": nano_cpus(rsv.get("cpus")),
        "memory_reservation": memory_bytes(rsv.get("memory")),
        "restart_condition": (deploy.get("restart_policy") or {}).get("condition", "any"),
        "update_order": (deploy.get("update_config") or {}).get("order", "stop-first"),
        "stop_grace": go_duration_ns(svc.get("stop_grace_period")) or DEFAULT_GRACE_NS,
        "user": svc.get("user") or None,
        "hostname": svc.get("hostname") or None,
        "entrypoint": svc.get("entrypoint") or None,
        "command": svc.get("command") or None,
        "healthcheck": health.get("test") or None,
        "cap_add": norm_caps(svc.get("cap_add")),
    }


# ---------- what is running ----------

def running(spec, net_names):
    task = spec["TaskTemplate"]
    cs = task["ContainerSpec"]
    res = task.get("Resources") or {}
    lim, rsv = res.get("Limits") or {}, res.get("Reservations") or {}
    placement = task.get("Placement") or {}
    mode = "global" if "Global" in spec.get("Mode", {}) else "replicated"
    env = {}
    for e in cs.get("Env") or []:
        k, _, v = e.partition("=")
        env[k] = v
    return {
        "image": norm_image(cs["Image"]),
        "mode": mode,
        "replicas": None if mode == "global" else spec["Mode"]["Replicated"].get("Replicas", 1),
        "env": env,
        "mounts": {(m.get("Type"), m.get("Source", ""), m["Target"], bool(m.get("ReadOnly")))
                   for m in cs.get("Mounts") or []},
        "ports": {(p["TargetPort"], p.get("PublishedPort"), p.get("Protocol", "tcp"), p.get("PublishMode", "ingress"))
                  for p in (spec.get("EndpointSpec") or {}).get("Ports") or []},
        "networks": {net_names.get(n["Target"], n["Target"]) for n in task.get("Networks") or []},
        "labels": {k: v for k, v in (spec.get("Labels") or {}).items() if not k.startswith(STACK_LABEL_PREFIX)},
        "container_labels": {k: v for k, v in (cs.get("Labels") or {}).items() if not k.startswith(STACK_LABEL_PREFIX)},
        "constraints": set(placement.get("Constraints") or []),
        "max_replicas_per_node": placement.get("MaxReplicas") or None,
        "cpu_limit": lim.get("NanoCPUs") or None,
        "memory_limit": lim.get("MemoryBytes") or None,
        "cpu_reservation": rsv.get("NanoCPUs") or None,
        "memory_reservation": rsv.get("MemoryBytes") or None,
        "restart_condition": (task.get("RestartPolicy") or {}).get("Condition", "any"),
        "update_order": (spec.get("UpdateConfig") or {}).get("Order", "stop-first"),
        "stop_grace": cs.get("StopGracePeriod") or DEFAULT_GRACE_NS,
        "user": cs.get("User") or None,
        "hostname": cs.get("Hostname") or None,
        "entrypoint": cs.get("Command") or None,
        "command": cs.get("Args") or None,
        "healthcheck": (cs.get("Healthcheck") or {}).get("Test") or None,
        "cap_add": norm_caps(cs.get("CapabilityAdd")),
    }


# ---------- comparison ----------

def fmt_port(p):
    target, published, proto, mode = p
    return f"{published}:{target}/{proto} ({mode})"


def fmt_mount(m):
    kind, source, target, ro = m
    return f"{source}:{target}{':ro' if ro else ''} ({kind})"


def compare(now, want, stack):
    """(lines, keep): lines describe what the deploy would change; 'REMOVE' marks what exists only in
    the running service (hand-made?). keep holds those settings as compose keys, to suggest them."""
    lines = []
    keep = {}

    def sets(key, fmt=str):
        for item in sorted(now[key] - want[key], key=str):
            lines.append(f"REMOVE {key[:-1] if key.endswith('s') else key}: {fmt(item)}")
        for item in sorted(want[key] - now[key], key=str):
            lines.append(f"add    {key[:-1] if key.endswith('s') else key}: {fmt(item)}")

    sets("ports", fmt_port)
    sets("mounts", fmt_mount)
    sets("networks")
    sets("constraints")
    sets("cap_add")

    for target, published, proto, mode in sorted(now["ports"] - want["ports"], key=str):
        keep.setdefault("ports", []).append({"target": target, "published": published, "protocol": proto, "mode": mode})
    for kind, source, target, ro in sorted(now["mounts"] - want["mounts"], key=str):
        if kind == "volume":
            source = source.removeprefix(stack + "_")   # declared under the top-level 'volumes:' too
        m = {"type": kind, "source": source, "target": target}
        if ro:
            m["read_only"] = True
        keep.setdefault("volumes", []).append(m)
    for c in sorted(now["constraints"] - want["constraints"]):
        keep.setdefault("deploy", {}).setdefault("placement", {}).setdefault("constraints", []).append(c)
    for c in sorted(now["cap_add"] - want["cap_add"]):
        keep.setdefault("cap_add", []).append(c)
    for n in sorted(now["networks"] - want["networks"]):
        keep.setdefault("# networks (declare them under the top-level 'networks:' too)", []).append(n)

    # environment: values may be secrets, show only the names
    for k in sorted(set(now["env"]) - set(want["env"])):
        lines.append(f"REMOVE env: {k}")
        keep.setdefault("environment", {})[k] = "<value: see 'docker service inspect'>"
    for k in sorted(set(want["env"]) - set(now["env"])):
        lines.append(f"add    env: {k}")
    for k in sorted(set(now["env"]) & set(want["env"])):
        if want["env"][k] is not None and now["env"][k] != want["env"][k]:
            lines.append(f"change env: {k} (value differs, not shown)")

    for key in ("labels", "container_labels"):
        for k in sorted(set(now[key]) - set(want[key])):
            lines.append(f"REMOVE {key[:-1]}: {k}")
            if key == "labels":
                keep.setdefault("deploy", {}).setdefault("labels", {})[k] = now[key][k]
            else:
                keep.setdefault("labels", {})[k] = now[key][k]
        for k in sorted(set(want[key]) - set(now[key])):
            lines.append(f"add    {key[:-1]}: {k}")
        for k in sorted(set(now[key]) & set(want[key])):
            if now[key][k] != want[key][k]:
                lines.append(f"change {key[:-1]}: {k} {now[key][k]!r} -> {want[key][k]!r}")

    scalars = {
        "image": str, "mode": str, "replicas": str, "max_replicas_per_node": str,
        "cpu_limit": lambda v: "none" if v is None else f"{v / 1e9:g} CPUs",
        "cpu_reservation": lambda v: "none" if v is None else f"{v / 1e9:g} CPUs",
        "memory_limit": lambda v: "none" if v is None else f"{v / 2**30:g} GiB",
        "memory_reservation": lambda v: "none" if v is None else f"{v / 2**30:g} GiB",
        "restart_condition": str, "update_order": str, "stop_grace": fmt_ns,
        "user": str, "hostname": str, "entrypoint": str, "command": str, "healthcheck": str,
    }
    for key, fmt in scalars.items():
        if now[key] != want[key]:
            lines.append(f"change {key}: {fmt(now[key])} -> {fmt(want[key])}")

    # scalar settings that are often changed by hand (scale, resources, grace period)
    deploy = {}
    if now["replicas"] != want["replicas"] and now["replicas"] is not None:
        deploy["replicas"] = now["replicas"]
    if now["max_replicas_per_node"] != want["max_replicas_per_node"] and now["max_replicas_per_node"]:
        deploy.setdefault("placement", {})["max_replicas_per_node"] = now["max_replicas_per_node"]
    for key, section, field, conv in (("cpu_limit", "limits", "cpus", lambda v: f"{v / 1e9:g}"),
                                      ("memory_limit", "limits", "memory", lambda v: f"{v // 2**20}M"),
                                      ("cpu_reservation", "reservations", "cpus", lambda v: f"{v / 1e9:g}"),
                                      ("memory_reservation", "reservations", "memory", lambda v: f"{v // 2**20}M")):
        if now[key] != want[key] and now[key] is not None:
            deploy.setdefault("resources", {}).setdefault(section, {})[field] = conv(now[key])
    if deploy:
        for k, v in deploy.items():
            if isinstance(v, dict):
                keep.setdefault("deploy", {}).setdefault(k, {}).update(v)
            else:
                keep.setdefault("deploy", {})[k] = v
    if now["stop_grace"] != want["stop_grace"] and now["stop_grace"] != DEFAULT_GRACE_NS:
        keep["stop_grace_period"] = fmt_ns(now["stop_grace"])
    return lines, keep


def to_yaml(value, indent):
    """A small YAML writer for the suggestion (strings quoted as JSON, which is valid YAML)."""
    pad = " " * indent
    out = []
    if isinstance(value, dict):
        for k, v in value.items():
            if isinstance(v, (dict, list)):
                out.append(f"{pad}{k}:")
                out.extend(to_yaml(v, indent + 2))
            else:
                out.append(f"{pad}{k}: {scalar(v)}")
    else:
        for item in value:
            if isinstance(item, dict):
                first = True
                for k, v in item.items():
                    out.append(f"{pad}{'- ' if first else '  '}{k}: {scalar(v)}")
                    first = False
            else:
                out.append(f"{pad}- {scalar(item)}")
    return out


def scalar(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    return json.dumps(str(v))


def is_down(replicas):
    """'1/2' or '0/1 (max 1 per node)' -> True when fewer tasks run than wanted."""
    m = re.match(r"(\d+)/(\d+)", replicas)
    return bool(m) and int(m.group(1)) < int(m.group(2))


def add_arguments(parser):
    parser.add_argument("-t", "--stack", default=os.environ.get("STACK_NAME") or "my_stack",
                        help="stack name (default: $STACK_NAME or my_stack)")
    parser.add_argument("-c", "--compose-file", action="append", dest="files",
                        help="compose file, as many as 'docker stack deploy' gets (default: docker-compose.yml); "
                             f"{NODE_FILE} is added last when it exists")
    parser.add_argument("--no-node-file", action="store_true", help=f"do not add {NODE_FILE}")
    parser.add_argument("--env-file", default=".env", help="file with the variables (default: .env)")


def check_files(files, env_file):
    for f in files + [env_file]:
        if not os.path.isfile(f):
            sys.exit(f"Error: {f} not found (run from the repository root)")


def diff(stack, files, env_file, suggest=True):
    """Print the comparison; return the number of running services that the deploy would change."""
    cfg = compose_config(files, env_file, stack)
    services = cfg.get("services") or {}

    net_names = {}
    for line in run(["docker", "network", "ls", "--no-trunc", "--format", "{{.ID}} {{.Name}}"]).splitlines():
        nid, name = line.split(" ", 1)
        net_names[nid] = name

    stack_services = run(["docker", "service", "ls", "--filter", f"label=com.docker.stack.namespace={stack}",
                          "--format", "{{.Name}}"]).split()
    tasks = {}
    for line in run(["docker", "service", "ls", "--filter", f"label=com.docker.stack.namespace={stack}",
                     "--format", "{{.Name}} {{.Replicas}}"]).splitlines():
        name, replicas = line.split(" ", 1)
        tasks[name] = replicas

    print(f"Stack {stack}, compose files: {', '.join(files)}\n")
    changed = 0
    down = []
    to_keep = {}
    for name in sorted(services):
        full = f"{stack}_{name}"
        want = wanted(name, services[name], cfg)
        if full not in stack_services:
            print(f"[new]     {name}: not running now; the deploy will create it ({want['image']})")
            continue
        spec = json.loads(run(["docker", "service", "inspect", full, "--format", "{{json .Spec}}"]))
        lines, keep = compare(running(spec, net_names), want, stack)
        if keep:
            to_keep[name] = keep
        state = tasks.get(full, "?")
        if lines:
            changed += 1
            print(f"[CHANGES] {name} ({state}):")
            for line in lines:
                print(f"            {line}")
        else:
            print(f"[same]    {name} ({state})")
        if is_down(state):
            down.append(full)

    extra = sorted(s for s in stack_services if s.removeprefix(stack + "_") not in services)
    for full in extra:
        print(f"[warning] {full}: running but in none of the compose files; the deploy leaves it alone "
              f"(only --prune removes it). Missing an extension file in -c?")

    for full in down:
        print(f"[down]    {full}: fewer tasks running than wanted. If its spec does not change, the deploy does not "
              f"restart it: use 'docker service update --force {full}' (or look at 'docker service ps {full}').")

    print()
    if changed:
        print(f"{changed} running service(s) would change. Lines with REMOVE exist only in the running service: "
              "probably done by hand, and the deploy would lose them.")
    else:
        print("The deploy would not change any running service.")
    if to_keep and suggest:
        print(f"\nTo keep what exists only in the running services, add this to {NODE_FILE} "
              "(merge it with what is already there) and run this script again:\n")
        print("services:")
        print("\n".join(to_yaml(to_keep, 2)))
    return changed


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_arguments(parser)
    args = parser.parse_args()
    files = compose_files(args.files, not args.no_node_file)
    check_files(files, args.env_file)
    sys.exit(1 if diff(args.stack, files, args.env_file) else 0)


if __name__ == "__main__":
    main()
