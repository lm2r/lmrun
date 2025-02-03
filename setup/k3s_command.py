"""Setup commands for K3s nodes"""

import subprocess
import argparse
import socket
from k3s_host_service import build_manifest

K3S_VERSION = "v1.32.1+k3s1"


def run(command: list[str] | str, shell=False, print_stderr=True):
    """Run a shell command from a list of strings, unless shell=True:
    command is a string and special characters are interpreted in a shell"""
    with subprocess.Popen(
        command,
        shell=shell,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        # override default /bin/sh to interpret more syntax like [[ .. ]]
        executable="/bin/bash" if shell else None,
    ) as process:
        for line in process.stdout:
            print(line.strip())
        process.wait()
        if process.returncode != 0:
            if print_stderr:
                print("STDERR:", process.stderr.read())
            raise subprocess.CalledProcessError(process.returncode, command)


def apt_setup():
    run(["apt-get", "update"])
    auto = "DEBIAN_FRONTEND=noninteractive"  # bypass prompt to save iptables rules
    run(
        " ".join(
            [auto, "apt-get", "install", "-y", "python3-boto3", "iptables-persistent"]
        ),
        shell=True,  # shell to inject DEBIAN_FRONTEND, otherwise treated as a file
    )


def get_private_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(("10.254.254.254", 1))
        private_ip = s.getsockname()[0]
    finally:
        s.close()
    return private_ip


def firewall_filter(main_node: bool):
    """Drop unexpected source traffic (TCP) + allow VPN
    These rules don't apply to K3s node ports, you still need the network policy"""
    conn_state = "ESTABLISHED,RELATED"  # allow request replies
    run(["iptables", "-AINPUT", "-mconntrack", "--ctstate", conn_state, "-jACCEPT"])
    if main_node:  # allow ingress to K3s server and Kube API (require certificate)
        run(["iptables", "-AINPUT", "-ptcp", "--dport=6443", "-jACCEPT"])
    for chain in ["INPUT", "FORWARD"]:
        run(
            [
                "iptables",
                "-A",
                chain,
                "-ptcp",
                "!",
                "-s10.0.0.0/8",  # includes LMRun AWS subnets + pod & services
                "!",
                "--dport=22",  # SSH
                "!",
                "-ilo",  # loopback interface
                "-jDROP",  # block all other TCP traffic
            ]
        )
    run(["iptables", "-AINPUT", "-pudp", "--dport=51820", "-jACCEPT"])  # VPN
    run(["netfilter-persistent", "save"])


def host_service(
    host_label: str, private_ip: str, app_ports: str, node_ports: str, namespace: str
):
    """Expose a host service to the K3s cluster on specified ports"""
    app_ports, node_ports = app_ports.split(","), node_ports.split(",")
    service_yaml = build_manifest(
        host_label, private_ip, app_ports, node_ports, namespace
    )

    # existing namespaced objects would be updated but other namespaces block the port
    print(f"Deleting duplicate {host_label} service & statefulset in any namespace..")
    run(
        [
            "kubectl",
            "delete",
            "cm,sts,svc",
            "-l",
            "lmrun=" + host_label,
            "--all-namespaces",
        ]
    )

    print(f"Scanning for requested node ports {node_ports}")
    scan = "/tmp/nodeport-scan.tsv"
    head = ":.metadata.namespace,:.spec.type,:.metadata.name,:.spec.ports[*].nodePort"
    run(
        f"""kubectl get svc -A --no-headers -o custom-columns={head} |
        awk -v OFS="\\t" '$1!="kube-system" && $2=="NodePort"{{print $1,$3,$4}}' > \
        {scan}""",
        shell=True,
    )
    with open(scan, "r", encoding="utf-8") as file:
        for line in file:
            namespace, service, scanned_ports = line.strip().split("\t")
            for scanned_port in scanned_ports.split(","):
                if scanned_port in node_ports:
                    ns_svc = f"{namespace}/{service}"
                    print(
                        "Checking endpoint of conflicting service",
                        f"{ns_svc} blocking node port {scanned_port}..",
                    )
                    # - throw ValueError if endpoint has an IP
                    # - catch ProcessError if it doesn't to free the dead port
                    try:
                        run(
                            f"""[[ `kubectl get endpoints {service} -n {namespace} \
                            -o jsonpath='{{.subsets[0].addresses[0].ip}}'` ]]""",
                            shell=True,
                            print_stderr=False,
                        )
                        raise ValueError(
                            f"Port {scanned_port} is already assigned to {ns_svc}"
                        )
                    except subprocess.CalledProcessError:
                        print("Cleaning orphaned resources with no IP to unlock port")
                        run(
                            [
                                "kubectl",
                                "delete",
                                "cm,sts,svc",
                                service,
                                "-n",
                                namespace,
                            ]
                        )

    print(f"Exposing {host_label} service from {app_ports} to {node_ports} host ports")
    run(f'echo "{service_yaml}" | kubectl apply -f -', shell=True)


def service_config(label: str, private_ip: str):
    """Parse arguments --port & --namespace to install optional service"""
    parser = argparse.ArgumentParser()
    # nullish default value ("") to apply a service when set after if condition below
    parser.add_argument("--app-port", "--app-ports", "-ap", type=str, default="")
    parser.add_argument("--node-port", "--node-ports", "-np", type=str, default="")
    parser.add_argument("--namespace", "-n", type=str, default="default")
    args = parser.parse_args()
    if args.app_port:
        if not args.node_port:
            parser.error("--node-port(s) is required when an app port is specified")
        host_service(label, private_ip, args.app_port, args.node_port, args.namespace)
    else:
        print("Skipping service creation: --app-port(s) isn't defined")
