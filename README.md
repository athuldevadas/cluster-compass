# Cluster Compass

Cluster Compass is a user-friendly Kubernetes dashboard built with Streamlit. It is meant to feel easier than a typical operator console, while still giving you practical tools for monitoring, troubleshooting, and safe actions inside a cluster.

## What it does

- Connects to your Kubernetes cluster through your local `kubectl`
- Shows a cluster health summary in a simpler business-friendly layout
- Organizes resources into clear sections like Overview, Workloads, Network, Storage, Operations, Governance, and Explorer
- Supports multiple kube contexts from your local kubeconfig
- Supports multi-container pods for both logs and shell access
- Includes demo data so you can review the UI without a live cluster

## Requirements

- Python 3.10+
- `kubectl` installed and available on your `PATH`
- Access to at least one Kubernetes context in your kubeconfig for live mode
- Optional: `helm` installed if you want Helm release data

## How it works

The app is read-mostly and uses standard Kubernetes CLI commands underneath, so it works with the same kubeconfig and permissions you already use.

Examples of what it collects:

- `kubectl get pods -A -o json`
- `kubectl get deployments -A -o json`
- `kubectl get events -A -o json`
- `kubectl top nodes`
- `kubectl logs -c <container>`
- `kubectl exec -c <container> -- /bin/sh`

If `metrics-server` is not installed, the rest of the dashboard still works, but resource usage sections may be empty.

## Setup

```bash
cd Cluster_Compass
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Start the app

Default Streamlit start:

```bash
streamlit run app.py
```

Wrapper script with default port `8501`:

```bash
bash run.sh
```

Open:

```text
http://localhost:8501
```

## Start on a different port

If another app is already using `8501`, you can start Cluster Compass on another port.

Using Streamlit directly:

```bash
streamlit run app.py --server.port 8502
```

Using the wrapper script:

```bash
bash run.sh 8502
```

Open:

```text
http://localhost:8502
```

You can also pass both port and host:

```bash
bash run.sh 8502 0.0.0.0
```

That starts the app on port `8502` and binds it to `0.0.0.0`.

You can also use environment variables:

```bash
PORT=8503 HOST=0.0.0.0 bash run.sh
```

## How to use it

### 1. Choose how to connect

- Use `Use demo data` if you want to inspect the UI without a real cluster
- Turn demo mode off to use your live kube contexts
- Pick the kube context from the sidebar

### 2. Choose the theme and refresh behavior

- `Theme`: `System`, `Light`, or `Dark`
- `Auto refresh cluster snapshot`: off by default so the page stays stable while you read it
- `Refresh now`: reload the cluster snapshot manually

### 3. Read the main sections

- `Overview`: cluster health, pod status, workload readiness, node state, and recent warnings
- `Workloads`: deployments, statefulsets, daemonsets, pods, and pod resource usage
- `Network & Access`: services and ingresses
- `Storage & Config`: PVCs, ConfigMaps, and Secrets inventory
- `Operations`: logs, pod shell, Helm releases, rollout actions, scaling, and delete actions
- `Governance`: security posture and RBAC review
- `Events & Explorer`: recent events and raw resource inspection as YAML or JSON

### 4. Use logs for a pod

In `Operations`:

- choose a pod
- if the pod has multiple containers, choose the container
- choose how many log lines you want
- click `Load logs`

### 5. Open a shell into a pod

In `Operations`:

- choose a pod
- if the pod has multiple containers, choose the container
- choose `/bin/sh` or `/bin/bash`
- click `Start shell`
- enter commands and click `Send command`

This keeps a lightweight shell session open and shows command history in the UI.

### 6. Use safe actions

- `Restart rollout` requires typing the exact workload name first
- `Delete resource` requires typing the exact resource name first
- `Scale resource` is available for Deployments and StatefulSets

## Current features

- Cluster health score and summary cards
- Namespace filtering
- Workload and pod tables
- Node health and node metrics
- Service and ingress inventory
- PVC, ConfigMap, and Secret views
- Event feed
- Resource explorer with YAML and JSON output
- Demo mode for design review and onboarding
- Pod log viewer
- Pod exec command runner for quick in-container checks
- Persistent pod shell session with command history
- Container selector for multi-container pods in logs and shell access
- Rollout status and restart actions for Deployments, StatefulSets, and DaemonSets
- Helm release inventory
- RBAC review for RoleBindings and ClusterRoleBindings
- Simple workload security posture view
- Resource scaling for Deployments and StatefulSets
- Guarded resource deletion with typed confirmation

## Notes

- This version is mostly read-only, with selected safe operator actions
- Destructive actions are intentionally guarded
- The live shell is designed for operational checks, not as a full terminal emulator
- Secret values are not decoded or exposed by the app
- Some resource types may be empty depending on what is installed in your cluster
