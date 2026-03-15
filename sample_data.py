from __future__ import annotations

from datetime import datetime, timedelta, timezone


def _ts(hours_ago: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()


def build_sample_snapshot() -> dict:
    return {
        "source": "sample",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "context": "demo-cluster",
        "version": "v1.30.0",
        "namespaces": [
            {"metadata": {"name": "default", "creationTimestamp": _ts(500)}},
            {"metadata": {"name": "kube-system", "creationTimestamp": _ts(500)}},
            {"metadata": {"name": "shop-prod", "creationTimestamp": _ts(240)}},
            {"metadata": {"name": "shop-staging", "creationTimestamp": _ts(200)}},
            {"metadata": {"name": "monitoring", "creationTimestamp": _ts(180)}},
        ],
        "nodes": [
            {
                "metadata": {"name": "node-a", "creationTimestamp": _ts(720)},
                "status": {
                    "conditions": [{"type": "Ready", "status": "True"}],
                    "nodeInfo": {"kubeletVersion": "v1.30.0"},
                },
            },
            {
                "metadata": {"name": "node-b", "creationTimestamp": _ts(720)},
                "status": {
                    "conditions": [{"type": "Ready", "status": "True"}],
                    "nodeInfo": {"kubeletVersion": "v1.30.0"},
                },
            },
            {
                "metadata": {"name": "node-c", "creationTimestamp": _ts(120)},
                "status": {
                    "conditions": [{"type": "Ready", "status": "False"}],
                    "nodeInfo": {"kubeletVersion": "v1.30.0"},
                },
            },
        ],
        "pods": [
            {
                "metadata": {"name": "api-6b749f47cd-jmkq7", "namespace": "shop-prod", "creationTimestamp": _ts(12)},
                "spec": {"nodeName": "node-a", "containers": [{"name": "api"}, {"name": "metrics-sidecar"}]},
                "security_context_summary": {"runAsNonRoot": True, "automountServiceAccountToken": False},
                "status": {
                    "phase": "Running",
                    "containerStatuses": [{"name": "api", "restartCount": 1, "ready": True}, {"name": "metrics-sidecar", "restartCount": 0, "ready": True}],
                },
            },
            {
                "metadata": {"name": "web-59b4f94c96-4pnk6", "namespace": "shop-prod", "creationTimestamp": _ts(6)},
                "spec": {"nodeName": "node-b", "containers": [{"name": "web"}]},
                "security_context_summary": {"runAsNonRoot": True, "automountServiceAccountToken": False},
                "status": {
                    "phase": "Running",
                    "containerStatuses": [{"name": "web", "restartCount": 0, "ready": True}],
                },
            },
            {
                "metadata": {"name": "worker-844dbdfd9b-rq7nb", "namespace": "shop-prod", "creationTimestamp": _ts(3)},
                "spec": {"nodeName": "node-b", "containers": [{"name": "worker"}]},
                "security_context_summary": {"runAsNonRoot": False, "automountServiceAccountToken": True},
                "status": {
                    "phase": "CrashLoopBackOff",
                    "containerStatuses": [{"name": "worker", "restartCount": 7, "ready": False}],
                },
            },
            {
                "metadata": {"name": "payments-api-67759cd8bb-j2fdp", "namespace": "shop-staging", "creationTimestamp": _ts(9)},
                "spec": {"nodeName": "node-c", "containers": [{"name": "payments-api"}, {"name": "istio-proxy"}]},
                "security_context_summary": {"runAsNonRoot": False, "automountServiceAccountToken": True},
                "status": {
                    "phase": "Pending",
                    "containerStatuses": [{"name": "payments-api", "restartCount": 0, "ready": False}, {"name": "istio-proxy", "restartCount": 0, "ready": False}],
                },
            },
            {
                "metadata": {"name": "prometheus-server-0", "namespace": "monitoring", "creationTimestamp": _ts(48)},
                "spec": {"nodeName": "node-a", "containers": [{"name": "prometheus-server"}]},
                "security_context_summary": {"runAsNonRoot": True, "automountServiceAccountToken": True},
                "status": {
                    "phase": "Running",
                    "containerStatuses": [{"name": "prometheus-server", "restartCount": 0, "ready": True}],
                },
            },
        ],
        "deployments": [
            {
                "metadata": {"name": "api", "namespace": "shop-prod", "creationTimestamp": _ts(120)},
                "status": {"replicas": 3, "readyReplicas": 2, "updatedReplicas": 3, "availableReplicas": 2},
            },
            {
                "metadata": {"name": "web", "namespace": "shop-prod", "creationTimestamp": _ts(120)},
                "status": {"replicas": 2, "readyReplicas": 2, "updatedReplicas": 2, "availableReplicas": 2},
            },
            {
                "metadata": {"name": "payments-api", "namespace": "shop-staging", "creationTimestamp": _ts(72)},
                "status": {"replicas": 1, "readyReplicas": 0, "updatedReplicas": 1, "availableReplicas": 0},
            },
        ],
        "statefulsets": [
            {
                "metadata": {"name": "prometheus-server", "namespace": "monitoring", "creationTimestamp": _ts(160)},
                "status": {"replicas": 1, "readyReplicas": 1, "currentReplicas": 1},
            }
        ],
        "daemonsets": [
            {
                "metadata": {"name": "node-exporter", "namespace": "monitoring", "creationTimestamp": _ts(160)},
                "status": {"desiredNumberScheduled": 3, "numberReady": 2},
            }
        ],
        "services": [
            {
                "metadata": {"name": "api", "namespace": "shop-prod", "creationTimestamp": _ts(120)},
                "spec": {"type": "ClusterIP", "clusterIP": "10.0.0.21", "ports": [{"port": 8080}]},
            },
            {
                "metadata": {"name": "web", "namespace": "shop-prod", "creationTimestamp": _ts(120)},
                "spec": {"type": "LoadBalancer", "clusterIP": "10.0.0.22", "ports": [{"port": 80}]},
                "status": {"loadBalancer": {"ingress": [{"ip": "34.84.1.10"}]}},
            },
        ],
        "ingresses": [
            {
                "metadata": {"name": "shop", "namespace": "shop-prod", "creationTimestamp": _ts(110)},
                "spec": {"rules": [{"host": "shop.example.com"}]},
            }
        ],
        "configmaps": [
            {"metadata": {"name": "api-config", "namespace": "shop-prod", "creationTimestamp": _ts(120)}, "data": {"LOG_LEVEL": "info"}},
            {"metadata": {"name": "web-config", "namespace": "shop-prod", "creationTimestamp": _ts(120)}, "data": {"API_BASE_URL": "https://api.example.com"}},
        ],
        "secrets": [
            {"metadata": {"name": "api-secret", "namespace": "shop-prod", "creationTimestamp": _ts(120)}, "type": "Opaque"},
            {"metadata": {"name": "registry-creds", "namespace": "shop-prod", "creationTimestamp": _ts(90)}, "type": "kubernetes.io/dockerconfigjson"},
        ],
        "persistentvolumeclaims": [
            {
                "metadata": {"name": "prometheus-storage", "namespace": "monitoring", "creationTimestamp": _ts(160)},
                "status": {"phase": "Bound", "capacity": {"storage": "50Gi"}},
                "spec": {"volumeName": "pv-prometheus-001"},
            }
        ],
        "persistentvolumes": [
            {
                "metadata": {"name": "pv-prometheus-001", "creationTimestamp": _ts(160)},
                "status": {"phase": "Bound"},
                "spec": {"capacity": {"storage": "50Gi"}},
            }
        ],
        "jobs": [
            {
                "metadata": {"name": "daily-sync-2893912", "namespace": "shop-prod", "creationTimestamp": _ts(8)},
                "status": {"succeeded": 1},
            }
        ],
        "cronjobs": [
            {
                "metadata": {"name": "daily-sync", "namespace": "shop-prod", "creationTimestamp": _ts(170)},
                "spec": {"schedule": "0 3 * * *"},
            }
        ],
        "events": [
            {
                "metadata": {"name": "worker.181e2f", "namespace": "shop-prod", "creationTimestamp": _ts(2)},
                "reason": "BackOff",
                "type": "Warning",
                "note": "Back-off restarting failed container",
                "regarding": {"kind": "Pod", "name": "worker-844dbdfd9b-rq7nb"},
            },
            {
                "metadata": {"name": "payments.181e2f", "namespace": "shop-staging", "creationTimestamp": _ts(4)},
                "reason": "FailedScheduling",
                "type": "Warning",
                "note": "0/3 nodes are available: 1 node not ready.",
                "regarding": {"kind": "Pod", "name": "payments-api-67759cd8bb-j2fdp"},
            },
            {
                "metadata": {"name": "web.181e2f", "namespace": "shop-prod", "creationTimestamp": _ts(1)},
                "reason": "Pulled",
                "type": "Normal",
                "note": "Successfully pulled image",
                "regarding": {"kind": "Pod", "name": "web-59b4f94c96-4pnk6"},
            },
        ],
        "node_metrics": [
            {"name": "node-a", "cpu": "380m", "cpu_pct": "19%", "memory": "2410Mi", "memory_pct": "42%"},
            {"name": "node-b", "cpu": "550m", "cpu_pct": "28%", "memory": "3180Mi", "memory_pct": "57%"},
            {"name": "node-c", "cpu": "120m", "cpu_pct": "6%", "memory": "950Mi", "memory_pct": "17%"},
        ],
        "pod_metrics": [
            {"namespace": "shop-prod", "name": "api-6b749f47cd-jmkq7", "cpu": "55m", "memory": "210Mi"},
            {"namespace": "shop-prod", "name": "web-59b4f94c96-4pnk6", "cpu": "33m", "memory": "160Mi"},
            {"namespace": "shop-prod", "name": "worker-844dbdfd9b-rq7nb", "cpu": "240m", "memory": "380Mi"},
            {"namespace": "monitoring", "name": "prometheus-server-0", "cpu": "180m", "memory": "1120Mi"},
        ],
        "serviceaccounts": [
            {"metadata": {"name": "default", "namespace": "shop-prod", "creationTimestamp": _ts(220)}, "automountServiceAccountToken": True},
            {"metadata": {"name": "api-runner", "namespace": "shop-prod", "creationTimestamp": _ts(120)}, "automountServiceAccountToken": False},
            {"metadata": {"name": "payments-runner", "namespace": "shop-staging", "creationTimestamp": _ts(96)}, "automountServiceAccountToken": True},
        ],
        "roles": [
            {"metadata": {"name": "config-reader", "namespace": "shop-prod", "creationTimestamp": _ts(120)}, "rules": [{"resources": ["configmaps"], "verbs": ["get", "list"]}]},
        ],
        "rolebindings": [
            {
                "metadata": {"name": "api-reader-binding", "namespace": "shop-prod", "creationTimestamp": _ts(120)},
                "subjects": [{"kind": "ServiceAccount", "name": "api-runner", "namespace": "shop-prod"}],
                "roleRef": {"kind": "Role", "name": "config-reader"},
            }
        ],
        "clusterroles": [
            {"metadata": {"name": "view", "creationTimestamp": _ts(500)}, "rules": [{"resources": ["pods"], "verbs": ["get", "list", "watch"]}]},
            {"metadata": {"name": "cluster-admin", "creationTimestamp": _ts(500)}, "rules": [{"resources": ["*"], "verbs": ["*"]}]},
        ],
        "clusterrolebindings": [
            {
                "metadata": {"name": "payments-admin", "creationTimestamp": _ts(80)},
                "subjects": [{"kind": "ServiceAccount", "name": "payments-runner", "namespace": "shop-staging"}],
                "roleRef": {"kind": "ClusterRole", "name": "cluster-admin"},
            }
        ],
        "helm_releases": [
            {"name": "ingress-nginx", "namespace": "ingress-nginx", "revision": "3", "updated": "2026-03-15 17:10:00", "status": "deployed", "chart": "ingress-nginx-4.10.0", "app_version": "1.10.0"},
            {"name": "prometheus", "namespace": "monitoring", "revision": "8", "updated": "2026-03-15 16:50:00", "status": "deployed", "chart": "kube-prometheus-stack-61.3.2", "app_version": "0.75.2"},
        ],
        "sample_logs": {
            "shop-prod/api-6b749f47cd-jmkq7::api": "2026-03-15T17:50:01Z INFO API started\n2026-03-15T17:50:08Z INFO Connected to database\n2026-03-15T17:50:15Z INFO Health check passed",
            "shop-prod/api-6b749f47cd-jmkq7::metrics-sidecar": "2026-03-15T17:50:02Z INFO metrics exporter ready\n2026-03-15T17:50:07Z INFO scraping /metrics",
            "shop-prod/worker-844dbdfd9b-rq7nb::worker": "2026-03-15T17:58:02Z ERROR Failed to connect to queue\n2026-03-15T17:58:05Z ERROR Retrying job processor\n2026-03-15T17:58:09Z FATAL Worker crashed with exit code 1",
        },
        "sample_exec": {
            "shop-prod/api-6b749f47cd-jmkq7::api::printenv": "APP_ENV=production\nLOG_LEVEL=info\nPORT=8080",
            "shop-prod/api-6b749f47cd-jmkq7::api::ls /app": "main.py\nconfig.py\nrequirements.txt\nhandlers/",
            "shop-prod/api-6b749f47cd-jmkq7::metrics-sidecar::printenv": "SCRAPE_PORT=9090\nSCRAPE_PATH=/metrics",
            "shop-prod/worker-844dbdfd9b-rq7nb::worker::ps aux": "PID   USER     TIME  COMMAND\n1     root     0:00  python worker.py\n37    root     0:00  sh -c ps aux",
        },
    }
