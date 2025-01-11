# Sky Services
multi-cloud MLOps services

- `sky launch -c main main.yaml` to launch the main K3s cluster node connecting all others
    - `ssh main` and then `journalctl -u k3s -f` to tail service logs