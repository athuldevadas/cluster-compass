from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import shutil
import subprocess
from typing import Any


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_k8s_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def humanize_age(value: str | None) -> str:
    timestamp = parse_k8s_timestamp(value)
    if not timestamp:
        return "Unknown"

    delta = _utc_now() - timestamp
    minutes = int(delta.total_seconds() // 60)
    if minutes < 1:
        return "Just now"
    if minutes < 60:
        return f"{minutes} min ago"

    hours = minutes // 60
    if hours < 24:
        return f"{hours} hr ago"

    days = hours // 24
    return f"{days} day{'s' if days != 1 else ''} ago"


@dataclass
class KubectlResult:
    ok: bool
    data: dict[str, Any] | None = None
    error: str | None = None


class KubeClient:
    def __init__(self, binary: str = "kubectl") -> None:
        self.binary = binary

    def is_available(self) -> bool:
        return shutil.which(self.binary) is not None

    def _run(self, args: list[str], expect_json: bool = True) -> KubectlResult:
        command = [self.binary, *args]
        try:
            completed = subprocess.run(
                command,
                check=True,
                text=True,
                capture_output=True,
            )
        except FileNotFoundError:
            return KubectlResult(ok=False, error="kubectl is not installed or not on PATH.")
        except subprocess.CalledProcessError as exc:
            message = exc.stderr.strip() or exc.stdout.strip() or "kubectl command failed."
            return KubectlResult(ok=False, error=message)

        if not expect_json:
            return KubectlResult(ok=True, data={"raw": completed.stdout})

        try:
            return KubectlResult(ok=True, data=json.loads(completed.stdout))
        except json.JSONDecodeError:
            return KubectlResult(ok=False, error="kubectl did not return valid JSON.")

    def _run_text(self, args: list[str]) -> KubectlResult:
        return self._run(args, expect_json=False)

    def get_contexts(self) -> list[str]:
        result = self._run(["config", "get-contexts", "-o", "name"], expect_json=False)
        if not result.ok or not result.data:
            return []
        raw = result.data["raw"]
        return [line.strip() for line in raw.splitlines() if line.strip()]

    def get_current_context(self) -> str | None:
        result = self._run(["config", "current-context"], expect_json=False)
        if not result.ok or not result.data:
            return None
        return result.data["raw"].strip() or None

    def get_version(self, context: str | None = None) -> str:
        args = ["version", "-o", "json"]
        if context:
            args.extend(["--context", context])

        result = self._run(args)
        if not result.ok or not result.data:
            return "Unknown"

        server = result.data.get("serverVersion", {})
        git_version = server.get("gitVersion")
        if git_version:
            return str(git_version)
        return "Unknown"

    def collect_snapshot(self, context: str | None = None) -> tuple[dict[str, Any], list[str]]:
        warnings: list[str] = []
        resources = {
            "namespaces": ["get", "namespaces", "-o", "json"],
            "nodes": ["get", "nodes", "-o", "json"],
            "pods": ["get", "pods", "-A", "-o", "json"],
            "deployments": ["get", "deployments", "-A", "-o", "json"],
            "statefulsets": ["get", "statefulsets", "-A", "-o", "json"],
            "daemonsets": ["get", "daemonsets", "-A", "-o", "json"],
            "services": ["get", "services", "-A", "-o", "json"],
            "ingresses": ["get", "ingress", "-A", "-o", "json"],
            "configmaps": ["get", "configmaps", "-A", "-o", "json"],
            "secrets": ["get", "secrets", "-A", "-o", "json"],
            "persistentvolumeclaims": ["get", "pvc", "-A", "-o", "json"],
            "persistentvolumes": ["get", "pv", "-o", "json"],
            "jobs": ["get", "jobs", "-A", "-o", "json"],
            "cronjobs": ["get", "cronjobs", "-A", "-o", "json"],
            "events": ["get", "events", "-A", "-o", "json"],
        }

        snapshot: dict[str, Any] = {
            "source": "live",
            "captured_at": _utc_now().isoformat(),
            "context": context or self.get_current_context() or "Unknown",
            "version": self.get_version(context),
        }

        context_args = ["--context", context] if context else []

        for key, base_args in resources.items():
            result = self._run([*base_args, *context_args])
            if result.ok and result.data is not None:
                snapshot[key] = result.data.get("items", [])
                continue

            snapshot[key] = []
            if result.error:
                warnings.append(f"{key}: {result.error}")

        metrics = self._collect_top_metrics(context)
        snapshot["node_metrics"] = metrics["nodes"]
        snapshot["pod_metrics"] = metrics["pods"]
        warnings.extend(metrics["warnings"])
        return snapshot, warnings

    def get_pod_logs(
        self,
        namespace: str,
        pod: str,
        context: str | None = None,
        container: str | None = None,
        tail_lines: int = 200,
    ) -> KubectlResult:
        args = ["logs", pod, "-n", namespace, "--tail", str(tail_lines)]
        if container:
            args.extend(["-c", container])
        if context:
            args.extend(["--context", context])
        return self._run_text(args)

    def rollout_restart(
        self,
        kind: str,
        name: str,
        namespace: str,
        context: str | None = None,
    ) -> KubectlResult:
        resource = kind.lower()
        args = ["rollout", "restart", f"{resource}/{name}", "-n", namespace]
        if context:
            args.extend(["--context", context])
        return self._run_text(args)

    def rollout_status(
        self,
        kind: str,
        name: str,
        namespace: str,
        context: str | None = None,
        timeout_seconds: int = 60,
    ) -> KubectlResult:
        resource = kind.lower()
        args = ["rollout", "status", f"{resource}/{name}", "-n", namespace, "--timeout", f"{timeout_seconds}s"]
        if context:
            args.extend(["--context", context])
        return self._run_text(args)

    def exec_in_pod(
        self,
        namespace: str,
        pod: str,
        command: list[str],
        context: str | None = None,
        container: str | None = None,
    ) -> KubectlResult:
        args = ["exec", "-n", namespace, pod]
        if container:
            args.extend(["-c", container])
        if context:
            args.extend(["--context", context])
        args.extend(["--", *command])
        return self._run_text(args)

    def scale_workload(
        self,
        kind: str,
        name: str,
        namespace: str,
        replicas: int,
        context: str | None = None,
    ) -> KubectlResult:
        resource = kind.lower()
        args = ["scale", f"{resource}/{name}", "-n", namespace, "--replicas", str(replicas)]
        if context:
            args.extend(["--context", context])
        return self._run_text(args)

    def delete_resource(
        self,
        kind: str,
        name: str,
        namespace: str | None = None,
        context: str | None = None,
    ) -> KubectlResult:
        resource = kind.lower()
        args = ["delete", f"{resource}/{name}"]
        if namespace and namespace != "cluster-wide":
            args.extend(["-n", namespace])
        if context:
            args.extend(["--context", context])
        return self._run_text(args)

    def helm_releases(self, context: str | None = None) -> tuple[list[dict[str, Any]], str | None]:
        if shutil.which("helm") is None:
            return [], "Helm is not installed or not on PATH."

        args = ["list", "-A", "-o", "json"]
        if context:
            args.extend(["--kube-context", context])
        result = self._run_text_with_binary("helm", args)
        if not result.ok:
            return [], result.error

        raw = result.data.get("raw", "") if result.data else ""
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return [], "Helm did not return valid JSON."
        return parsed if isinstance(parsed, list) else [], None

    def _run_text_with_binary(self, binary: str, args: list[str]) -> KubectlResult:
        command = [binary, *args]
        try:
            completed = subprocess.run(
                command,
                check=True,
                text=True,
                capture_output=True,
            )
        except FileNotFoundError:
            return KubectlResult(ok=False, error=f"{binary} is not installed or not on PATH.")
        except subprocess.CalledProcessError as exc:
            message = exc.stderr.strip() or exc.stdout.strip() or f"{binary} command failed."
            return KubectlResult(ok=False, error=message)
        return KubectlResult(ok=True, data={"raw": completed.stdout})

    def _collect_top_metrics(self, context: str | None = None) -> dict[str, Any]:
        context_args = ["--context", context] if context else []
        warnings: list[str] = []

        nodes_result = self._run(["top", "nodes", "--no-headers", *context_args], expect_json=False)
        pods_result = self._run(["top", "pods", "-A", "--no-headers", *context_args], expect_json=False)

        node_rows: list[dict[str, str]] = []
        if nodes_result.ok and nodes_result.data:
            for line in nodes_result.data["raw"].splitlines():
                parts = line.split()
                if len(parts) >= 5:
                    node_rows.append(
                        {
                            "name": parts[0],
                            "cpu": parts[1],
                            "cpu_pct": parts[2],
                            "memory": parts[3],
                            "memory_pct": parts[4],
                        }
                    )
        elif nodes_result.error:
            warnings.append(f"metrics: {nodes_result.error}")

        pod_rows: list[dict[str, str]] = []
        if pods_result.ok and pods_result.data:
            for line in pods_result.data["raw"].splitlines():
                parts = line.split()
                if len(parts) >= 4:
                    pod_rows.append(
                        {
                            "namespace": parts[0],
                            "name": parts[1],
                            "cpu": parts[2],
                            "memory": parts[3],
                        }
                    )
        elif pods_result.error:
            warnings.append(f"pod metrics: {pods_result.error}")

        return {"nodes": node_rows, "pods": pod_rows, "warnings": warnings}
