# Cluster Compass

Cluster Compass is a friendly Kubernetes monitoring dashboard built with Streamlit. It is designed for people who want a Lens-style cluster view, but with simpler wording, clearer grouping, and a cleaner experience for non-technical users.

## What it does

- Shows a live snapshot of your cluster through your local `kubectl` access
- Gives a simple health score with high-level warning signals
- Organizes information into friendly sections:
  - Overview
  - Workloads
  - Network and access
  - Storage and configuration
  - Events and resource explorer
- Supports multiple kube contexts from your local kubeconfig
- Includes demo data so you can open and review the UI even before connecting a cluster
- Includes a raw YAML and JSON explorer for deeper inspection

## How it works

The app uses `kubectl` under the hood, so it works with the same kubeconfig and permissions you already use on your machine. No extra Kubernetes API setup is required for the first version.

It collects a read-only snapshot using commands such as:

- `kubectl get pods -A -o json`
- `kubectl get deployments -A -o json`
- `kubectl get events -A -o json`
- `kubectl top nodes`

If metrics are not available because `metrics-server` is missing, the rest of the dashboard still works.

## Local setup

```bash
cd Cluster_Compass
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL shown by Streamlit, usually:

```text
http://localhost:8501
```

## Requirements

- Python 3.10+
- `kubectl` installed and available on your `PATH`
- Access to at least one Kubernetes context in your kubeconfig

## First version features

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

## Good next features to add

- Exec terminal into a pod
- Namespace and resource actions with RBAC awareness
- Deployment rollout history with diff view
- Cost and usage estimation
- Multi-cluster comparison dashboard
- Saved alerts and notification rules
- Custom alerts, SSO, and audit trail

## Notes

- This version is mostly read-only, with one operator action: rollout restart for supported workloads.
- Destructive actions are intentionally guarded. Delete stays locked until the exact resource name is typed.
- The live shell uses `kubectl exec -i` and is designed for quick operational checks, not a full SSH-style terminal emulator.
- If a pod has multiple containers, select the exact container before viewing logs or opening a shell session.
- Under the hood, the app uses the standard Kubernetes container targeting flags like `kubectl logs -c <container>` and `kubectl exec -c <container>`.
- The rollout restart action is available when connected to a live cluster and uses your current `kubectl` permissions.
- Secret values are not decoded or exposed by the app.
- Some resource types may be empty depending on what is installed in your cluster.
