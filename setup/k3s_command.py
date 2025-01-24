"""Setup commands for K3s nodes"""

import os
import subprocess
import argparse
from k3s_host_service import build_manifest


def run(command: list[str] | str, shell=False):
    """Run a shell command from a list of strings, unless shell=True:
    i.e. command is a string and special characters are interpreted in a shell"""
    with subprocess.Popen(
        command,
        shell=shell,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    ) as process:
        for line in process.stdout:
            print(line.strip())
        process.wait()
        if process.returncode != 0:
            print("STDERR:", process.stderr.read())
            raise subprocess.CalledProcessError(process.returncode, command)


def set_k3s_dns_on_host():
    """Set up kubernetes nameserver for cluster endpoints on the host"""
    conf_dir = "/etc/systemd/resolved.conf.d/"
    content = "[Resolve]\nDNS=10.43.0.10\nDomains=~lm.run\n"
    os.makedirs(conf_dir, exist_ok=True)
    with open(conf_dir + "k3s-dns.conf", "w", encoding="utf-8") as file:
        file.write(content)
    run(["systemctl", "restart", "systemd-resolved"])


def host_service(host_label: str, ports: str, namespace: str):
    """Expose a host service to the K3s cluster on specified port"""
    service_yaml = build_manifest(host_label, ports, namespace)
    # existing namespaced objects would be updated but other namespaces block the port
    print(f"Deleting duplicate {host_label} service & statefulset in any namespace..")
    run(
        [
            "kubectl",
            "delete",
            "sts,svc",
            "-l",
            "lmrun=" + host_label,
            "--all-namespaces",
        ]
    )
    print(f"Exposing a {host_label} host service to the K3s cluster on ports {ports}")
    run(f'echo "{service_yaml}" | kubectl apply -f -', shell=True)


def service_config(label: str):
    """Parse arguments --port & --namespace to install optional service"""
    parser = argparse.ArgumentParser()
    # nullish default value ("") to apply a service when set after if condition below
    parser.add_argument("--port", "-p", "--ports", type=str, default="")
    parser.add_argument("--namespace", "-n", type=str, default="default")
    args = parser.parse_args()
    if args.port:
        host_service(label, args.port, args.namespace)
    else:
        print("Skipping service creation: --port(s) isn't defined")


def dupe_node_cleanup(label: str):
    """
    - Get nodes tagged with the label, sorted by creation timestamp
    - Select all nodes but the most recent (head -n -1)
    - Delete them if status is NotReady
    - If no duplicate node, silence the error (2>&-) and catch code 123
    """
    run(
        f"""kubectl get nodes -l lmrun={label} \
        --no-headers \
        --sort-by=.metadata.creationTimestamp | 
        head -n -1 | 
        awk '$2=="NotReady"{{print $1}}' | 
        xargs kubectl delete node 2>&- || 
        ([ $? = 123 ] && echo no duplicate node)""",
        shell=True,
    )
