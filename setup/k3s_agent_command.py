"""Setup commands for K3s agent

Import with the main script in task setup: `install -m 755 /r2/setup/k3s_agent*`
"""

import os
import subprocess
from k3s_agent_manifest import host_service_template


def run(command: list[str] | str, shell=False):
    """Run a shell command from a list of strings, unless shell=True:
    i.e. command is a string and special characters are interpreted in a shell"""
    try:
        output = subprocess.run(
            command, shell=shell, check=True, capture_output=True, text=True
        )
        # commands like `systemctl restart` don't produce output unless they error out
        if output.stdout:
            print("STDOUT:", output.stdout)
    except subprocess.CalledProcessError as e:
        print("STDERR:", e.stderr)
        raise e


def set_k3s_dns_on_host():
    """Set up kubernetes nameserver for cluster endpoints on the host"""
    conf_dir = "/etc/systemd/resolved.conf.d/"
    content = "[Resolve]\nDNS=10.43.0.10\nDomains=~cluster.local\n"
    os.makedirs(conf_dir, exist_ok=True)
    with open(conf_dir + "k3s-dns.conf", "w", encoding="utf-8") as file:
        file.write(content)
    run(["systemctl", "restart", "systemd-resolved"])


def host_service(host_label: str, port: int, namespace: str):
    """Expose a host service to the K3s cluster on specified port"""
    service_yaml = (
        host_service_template.replace("<LABEL>", host_label)
        .replace("<PORT>", str(port))
        .replace("<NAMESPACE>", namespace)
    )
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
    print(f"Exposing a {host_label} host service to the K3s cluster on port {port}..")
    run(f'echo "{service_yaml}" | kubectl apply -f -', shell=True)


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
