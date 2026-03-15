from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
import yaml

from kube_client import KubeClient, humanize_age
from sample_data import build_sample_snapshot
from terminal_manager import TerminalManager


st.set_page_config(
    page_title="Cluster Compass",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_DIR = Path(__file__).resolve().parent
SETTINGS_PATH = APP_DIR / "ui_settings.json"


def load_ui_settings() -> dict[str, Any]:
    if not SETTINGS_PATH.exists():
        return {}
    try:
        return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_ui_settings(settings: dict[str, Any]) -> None:
    try:
        SETTINGS_PATH.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    except OSError:
        pass


def initialize_theme_state() -> None:
    if "theme_mode" in st.session_state:
        return
    settings = load_ui_settings()
    saved_theme_mode = settings.get("theme_mode", "System")
    st.session_state["theme_mode"] = saved_theme_mode if saved_theme_mode in {"System", "Light", "Dark"} else "System"
    st.session_state["theme_selector"] = st.session_state["theme_mode"]


def handle_theme_change() -> None:
    selected = st.session_state.get("theme_selector", "System")
    st.session_state["theme_mode"] = selected
    settings = load_ui_settings()
    settings["theme_mode"] = selected
    save_ui_settings(settings)


def theme_palette(theme_mode: str = "System") -> dict[str, str]:
    light = {
        "ink": "#12343b",
        "muted": "#4c6b72",
        "panel": "#ffffff",
        "accent": "#e5723a",
        "accent_soft": "#fff0e8",
        "good": "#1f8a5b",
        "warn": "#d97706",
        "bad": "#c2410c",
        "line": "rgba(18, 52, 59, 0.12)",
        "app_bg": "radial-gradient(circle at top right, rgba(229, 114, 58, 0.14), transparent 28%), radial-gradient(circle at top left, rgba(31, 138, 91, 0.16), transparent 30%), linear-gradient(180deg, #eef7f1 0%, #f7fbf8 48%, #edf5ef 100%)",
        "sidebar_bg": "linear-gradient(180deg, rgba(217,239,229,0.9), rgba(248,251,246,0.98))",
        "hero_bg": "linear-gradient(135deg, rgba(255,255,255,0.92), rgba(217,239,229,0.88))",
        "guide_bg": "rgba(255,255,255,0.8)",
        "shadow": "0 18px 45px rgba(18, 52, 59, 0.08)",
        "card_shadow": "0 10px 24px rgba(18, 52, 59, 0.06)",
        "table_bg": "rgba(255,255,255,0.94)",
        "table_header": "rgba(217,239,229,0.95)",
        "input_bg": "#ffffff",
        "plot_bg": "rgba(255,255,255,0)",
        "paper_bg": "rgba(255,255,255,0)",
        "color_scheme": "light",
    }
    dark = {
        "ink": "#edf6f1",
        "muted": "#b7ccc4",
        "panel": "rgba(15, 24, 24, 0.94)",
        "accent": "#ff9966",
        "accent_soft": "rgba(255, 153, 102, 0.14)",
        "good": "#4dd19b",
        "warn": "#f2b35e",
        "bad": "#ff8f70",
        "line": "rgba(225, 241, 235, 0.12)",
        "app_bg": "radial-gradient(circle at top right, rgba(255, 153, 102, 0.14), transparent 28%), radial-gradient(circle at top left, rgba(77, 209, 155, 0.12), transparent 30%), linear-gradient(180deg, #081211 0%, #101b1a 42%, #0a1312 100%)",
        "sidebar_bg": "linear-gradient(180deg, rgba(15,24,24,0.98), rgba(23,38,36,0.96))",
        "hero_bg": "linear-gradient(135deg, rgba(18, 31, 30, 0.96), rgba(19, 46, 42, 0.92))",
        "guide_bg": "rgba(17, 29, 28, 0.9)",
        "shadow": "0 18px 45px rgba(0, 0, 0, 0.28)",
        "card_shadow": "0 10px 24px rgba(0, 0, 0, 0.24)",
        "table_bg": "rgba(15,24,24,0.94)",
        "table_header": "rgba(22,51,48,0.98)",
        "input_bg": "rgba(19, 35, 34, 0.98)",
        "plot_bg": "rgba(0,0,0,0)",
        "paper_bg": "rgba(0,0,0,0)",
        "color_scheme": "dark",
    }
    return dark if theme_mode == "Dark" else light


def apply_theme(theme_mode: str = "System") -> None:
    if theme_mode == "System":
        css = """
        <style>
        :root {
            --ink: #12343b;
            --muted: #4c6b72;
            --panel: #ffffff;
            --accent: #e5723a;
            --accent-soft: #fff0e8;
            --good: #1f8a5b;
            --warn: #d97706;
            --bad: #c2410c;
            --line: rgba(18, 52, 59, 0.12);
            --app-bg: radial-gradient(circle at top right, rgba(229, 114, 58, 0.14), transparent 28%), radial-gradient(circle at top left, rgba(31, 138, 91, 0.16), transparent 30%), linear-gradient(180deg, #eef7f1 0%, #f7fbf8 48%, #edf5ef 100%);
            --sidebar-bg: linear-gradient(180deg, rgba(217,239,229,0.9), rgba(248,251,246,0.98));
            --hero-bg: linear-gradient(135deg, rgba(255,255,255,0.92), rgba(217,239,229,0.88));
            --guide-bg: rgba(255,255,255,0.8);
            --shadow: 0 18px 45px rgba(18, 52, 59, 0.08);
            --card-shadow: 0 10px 24px rgba(18, 52, 59, 0.06);
            --table-bg: rgba(255,255,255,0.94);
            --table-header: rgba(217,239,229,0.95);
            --input-bg: #ffffff;
            color-scheme: light;
        }
        @media (prefers-color-scheme: dark) {
            :root {
                --ink: #edf6f1;
                --muted: #b7ccc4;
                --panel: rgba(15, 24, 24, 0.92);
                --accent: #ff9966;
                --accent-soft: rgba(255, 153, 102, 0.14);
                --good: #4dd19b;
                --warn: #f2b35e;
                --bad: #ff8f70;
                --line: rgba(225, 241, 235, 0.12);
                --app-bg:
                    radial-gradient(circle at top right, rgba(255, 153, 102, 0.14), transparent 28%),
                    radial-gradient(circle at top left, rgba(77, 209, 155, 0.12), transparent 30%),
                    linear-gradient(180deg, #081211 0%, #101b1a 42%, #0a1312 100%);
                --sidebar-bg: linear-gradient(180deg, rgba(15,24,24,0.98), rgba(23,38,36,0.96));
                --hero-bg: linear-gradient(135deg, rgba(18, 31, 30, 0.96), rgba(19, 46, 42, 0.92));
                --guide-bg: rgba(17, 29, 28, 0.9);
                --shadow: 0 18px 45px rgba(0, 0, 0, 0.28);
                --card-shadow: 0 10px 24px rgba(0, 0, 0, 0.24);
                --table-bg: rgba(15,24,24,0.94);
                --table-header: rgba(22,51,48,0.98);
                --input-bg: rgba(19, 35, 34, 0.98);
                color-scheme: dark;
            }
        }
        """
    else:
        palette = theme_palette(theme_mode)
        css = f"""
        <style>
        :root {{
            --ink: {palette["ink"]};
            --muted: {palette["muted"]};
            --panel: {palette["panel"]};
            --accent: {palette["accent"]};
            --accent-soft: {palette["accent_soft"]};
            --good: {palette["good"]};
            --warn: {palette["warn"]};
            --bad: {palette["bad"]};
            --line: {palette["line"]};
            --app-bg: {palette["app_bg"]};
            --sidebar-bg: {palette["sidebar_bg"]};
            --hero-bg: {palette["hero_bg"]};
            --guide-bg: {palette["guide_bg"]};
            --shadow: {palette["shadow"]};
            --card-shadow: {palette["card_shadow"]};
            --table-bg: {palette["table_bg"]};
            --table-header: {palette["table_header"]};
            --input-bg: {palette["input_bg"]};
            color-scheme: {palette["color_scheme"]};
        }}
        """

    css += """
        .stApp {
            background: var(--app-bg);
            color: var(--ink);
            font-family: "Avenir Next", "Segoe UI", sans-serif;
        }
        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 2rem;
        }
        .stApp, .stApp p, .stApp span, .stApp label, .stApp div, .stApp h1, .stApp h2, .stApp h3 {
            color: var(--ink);
        }
        [data-testid="stSidebar"] {
            background: var(--sidebar-bg);
            border-right: 1px solid var(--line);
        }
        [data-testid="stSidebar"] * {
            color: var(--ink);
        }
        .hero {
            background: var(--hero-bg);
            border: 1px solid var(--line);
            border-radius: 24px;
            padding: 1.4rem 1.5rem;
            box-shadow: var(--shadow);
            margin-bottom: 1rem;
        }
        .hero h1 {
            font-family: Georgia, "Times New Roman", serif;
            font-size: 2.2rem;
            margin-bottom: 0.2rem;
            color: var(--ink);
        }
        .hero p {
            color: var(--muted);
            margin: 0;
            font-size: 1rem;
        }
        .metric-card {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 20px;
            padding: 1rem;
            min-height: 132px;
            box-shadow: var(--card-shadow);
        }
        .metric-label {
            color: var(--muted);
            font-size: 0.86rem;
            margin-bottom: 0.3rem;
        }
        .metric-value {
            font-size: 1.8rem;
            line-height: 1.1;
            font-weight: 700;
            color: var(--ink);
        }
        .metric-note {
            margin-top: 0.5rem;
            color: var(--muted);
            font-size: 0.9rem;
        }
        .guide {
            background: var(--guide-bg);
            border-left: 4px solid var(--accent);
            padding: 0.9rem 1rem;
            border-radius: 14px;
            margin-bottom: 1rem;
        }
        .guide strong {
            color: var(--ink);
        }
        .section-chip {
            display: inline-block;
            padding: 0.2rem 0.65rem;
            border-radius: 999px;
            background: var(--accent-soft);
            color: var(--accent);
            font-weight: 600;
            font-size: 0.8rem;
            margin-bottom: 0.6rem;
        }
        [data-baseweb="input"] > div,
        [data-baseweb="select"] > div,
        .stTextInput input,
        .stNumberInput input,
        .stTextArea textarea {
            background: var(--input-bg) !important;
            color: var(--ink) !important;
            border-color: var(--line) !important;
        }
        [data-testid="stDataFrame"] {
            background: var(--table-bg);
            border: 1px solid var(--line);
            border-radius: 16px;
            overflow: hidden;
        }
        [data-testid="stDataFrame"] [role="columnheader"] {
            background: var(--table-header) !important;
            color: var(--ink) !important;
        }
        [data-testid="stDataFrame"] [role="gridcell"] {
            background: var(--table-bg) !important;
            color: var(--ink) !important;
            border-color: var(--line) !important;
        }
        [data-testid="stTabs"] button {
            color: var(--muted) !important;
        }
        [data-testid="stTabs"] button[aria-selected="true"] {
            color: var(--accent) !important;
        }
        .stButton > button {
            background: var(--panel) !important;
            color: var(--ink) !important;
            border: 1px solid var(--line) !important;
        }
        .stButton > button p,
        .stButton > button span,
        .stButton > button div {
            color: inherit !important;
        }
        .stButton > button[kind="primary"] {
            background: var(--accent) !important;
            color: #ffffff !important;
            border-color: var(--accent) !important;
        }
        .stButton > button[kind="primary"] p,
        .stButton > button[kind="primary"] span,
        .stButton > button[kind="primary"] div {
            color: #ffffff !important;
        }
        .stButton > button:hover {
            border-color: var(--accent) !important;
        }
        </style>
        """

    st.markdown(
        css,
        unsafe_allow_html=True,
    )


def style_plotly_figure(fig, theme_mode: str) -> None:
    palette = theme_palette("Dark" if theme_mode == "Dark" else "Light")
    fig.update_layout(
        title={"text": ""},
        paper_bgcolor=palette["paper_bg"],
        plot_bgcolor=palette["plot_bg"],
        font_color=palette["ink"],
        title_font_color=palette["ink"],
        legend_font_color=palette["ink"],
        legend_title_text="",
        margin=dict(l=10, r=10, t=20, b=10),
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor=palette["line"],
        zerolinecolor=palette["line"],
        color=palette["ink"],
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=palette["line"],
        zerolinecolor=palette["line"],
        color=palette["ink"],
    )


def metric_card(label: str, value: str, note: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource
def get_terminal_manager() -> TerminalManager:
    return TerminalManager()


def guide(title: str, body: str) -> None:
    st.markdown(
        f'<div class="guide"><strong>{title}</strong><br>{body}</div>',
        unsafe_allow_html=True,
    )


def onboarding_guide() -> None:
    st.markdown(
        """
        <div class="guide" style="padding: 1.1rem 1.15rem;">
            <div class="section-chip">Start here</div>
            <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 0.65rem;">How to read this screen</div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.8rem;">
                <div class="metric-card" style="min-height: 0; padding: 0.9rem;">
                    <div class="metric-label">1. Check the top cards</div>
                    <div class="metric-note">They tell you whether the cluster looks healthy and how many pods or workloads need attention.</div>
                </div>
                <div class="metric-card" style="min-height: 0; padding: 0.9rem;">
                    <div class="metric-label">2. Open Workloads</div>
                    <div class="metric-note">Use this when an app is failing or restarting. It shows which pod or deployment is unhealthy.</div>
                </div>
                <div class="metric-card" style="min-height: 0; padding: 0.9rem;">
                    <div class="metric-label">3. Use Operations</div>
                    <div class="metric-note">Read logs, open a pod shell, or trigger safe actions like restart or scale when needed.</div>
                </div>
                <div class="metric-card" style="min-height: 0; padding: 0.9rem;">
                    <div class="metric-label">4. Investigate deeply</div>
                    <div class="metric-note">Events and Resource Explorer help you inspect exactly what Kubernetes is reporting.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_ready_condition(node: dict[str, Any]) -> str:
    for condition in node.get("status", {}).get("conditions", []):
        if condition.get("type") == "Ready":
            return "Ready" if condition.get("status") == "True" else "Not Ready"
    return "Unknown"


def pod_health(pod: dict[str, Any]) -> str:
    statuses = pod.get("status", {}).get("containerStatuses", [])
    phase = pod.get("status", {}).get("phase", "Unknown")
    if phase not in {"Running", "Succeeded"}:
        return phase
    if any(not item.get("ready", False) for item in statuses):
        return "Degraded"
    return phase


def workload_health(item: dict[str, Any], kind: str) -> str:
    status = item.get("status", {})
    if kind == "Deployment":
        desired = status.get("replicas", 0)
        ready = status.get("readyReplicas", 0)
    elif kind == "StatefulSet":
        desired = status.get("replicas", 0)
        ready = status.get("readyReplicas", 0)
    else:
        desired = status.get("desiredNumberScheduled", 0)
        ready = status.get("numberReady", 0)

    if desired == 0:
        return "Idle"
    if ready >= desired:
        return "Healthy"
    if ready == 0:
        return "Critical"
    return "Degraded"


def filter_namespace(frame: pd.DataFrame, namespace: str) -> pd.DataFrame:
    if frame.empty or namespace == "All namespaces" or "Namespace" not in frame.columns:
        return frame
    return frame[frame["Namespace"] == namespace]


def to_namespace_name(item: dict[str, Any]) -> tuple[str, str]:
    metadata = item.get("metadata", {})
    return metadata.get("namespace", "cluster-wide"), metadata.get("name", "unknown")


def describe_risk(level: str) -> str:
    return {
        "Low": "Looks aligned with safer defaults.",
        "Medium": "Worth reviewing, but not always a problem.",
        "High": "This could be risky and should be checked soon.",
        "Critical": "This grants broad power or weakens workload isolation.",
    }.get(level, "Review recommended.")


def pod_security_risk(pod: dict[str, Any]) -> tuple[str, str]:
    summary = pod.get("security_context_summary", {})
    pod_spec = pod.get("spec", {})
    pod_security = pod_spec.get("securityContext", {})
    containers = pod_spec.get("containers", [])
    run_as_non_root = summary.get("runAsNonRoot")
    if run_as_non_root is None:
        run_as_non_root = pod_security.get("runAsNonRoot")
    if run_as_non_root is None and containers:
        container_values = [container.get("securityContext", {}).get("runAsNonRoot") for container in containers]
        if any(value is False for value in container_values):
            run_as_non_root = False
        elif any(value is True for value in container_values):
            run_as_non_root = True

    automount = summary.get("automountServiceAccountToken")
    if automount is None:
        automount = pod_spec.get("automountServiceAccountToken")
    phase = pod.get("status", {}).get("phase", "Unknown")

    if run_as_non_root is False and automount is True:
        return "High", "Runs with weaker defaults and auto-mounts credentials"
    if run_as_non_root is False:
        return "Medium", "Does not clearly enforce non-root execution"
    if automount is True:
        return "Medium", "Service account token is auto-mounted"
    if phase not in {"Running", "Succeeded"}:
        return "Medium", "Pod is not healthy, review before trusting posture"
    return "Low", "Security defaults look reasonable"


def role_binding_risk(binding: dict[str, Any]) -> tuple[str, str]:
    role_ref = binding.get("roleRef", {})
    role_name = role_ref.get("name", "")
    if role_name == "cluster-admin":
        return "Critical", "Full admin access granted"
    if "admin" in role_name:
        return "High", "Elevated admin-style access granted"
    if role_ref.get("kind") == "ClusterRole":
        return "Medium", "Cluster-wide permissions attached"
    return "Low", "Scoped permissions"


def count_container_restarts(snapshot: dict[str, Any]) -> int:
    total = 0
    for pod in snapshot.get("pods", []):
        for status in pod.get("status", {}).get("containerStatuses", []):
            total += status.get("restartCount", 0)
    return total


def build_frames(snapshot: dict[str, Any]) -> dict[str, pd.DataFrame]:
    pods = []
    total_restarts = 0
    for item in snapshot.get("pods", []):
        metadata = item.get("metadata", {})
        status = item.get("status", {})
        container_statuses = status.get("containerStatuses", [])
        restarts = sum(container.get("restartCount", 0) for container in container_statuses)
        total_restarts += restarts
        pods.append(
            {
                "Namespace": metadata.get("namespace", "default"),
                "Pod": metadata.get("name", ""),
                "Status": pod_health(item),
                "Phase": status.get("phase", "Unknown"),
                "Ready Containers": f"{sum(1 for c in container_statuses if c.get('ready'))}/{len(container_statuses)}",
                "Restarts": restarts,
                "Node": item.get("spec", {}).get("nodeName", "-"),
                "Age": humanize_age(metadata.get("creationTimestamp")),
            }
        )

    workloads = []
    for kind, key in (
        ("Deployment", "deployments"),
        ("StatefulSet", "statefulsets"),
        ("DaemonSet", "daemonsets"),
    ):
        for item in snapshot.get(key, []):
            metadata = item.get("metadata", {})
            status = item.get("status", {})
            if kind == "DaemonSet":
                desired = status.get("desiredNumberScheduled", 0)
                ready = status.get("numberReady", 0)
            else:
                desired = status.get("replicas", 0)
                ready = status.get("readyReplicas", 0)
            workloads.append(
                {
                    "Kind": kind,
                    "Namespace": metadata.get("namespace", "default"),
                    "Name": metadata.get("name", ""),
                    "Ready": f"{ready}/{desired}",
                    "Health": workload_health(item, kind),
                    "Age": humanize_age(metadata.get("creationTimestamp")),
                }
            )

    services = []
    for item in snapshot.get("services", []):
        metadata = item.get("metadata", {})
        spec = item.get("spec", {})
        ports = ", ".join(str(port.get("port")) for port in spec.get("ports", []))
        external = item.get("status", {}).get("loadBalancer", {}).get("ingress", [])
        services.append(
            {
                "Namespace": metadata.get("namespace", "default"),
                "Service": metadata.get("name", ""),
                "Type": spec.get("type", "ClusterIP"),
                "Cluster IP": spec.get("clusterIP", "-"),
                "Ports": ports or "-",
                "External": ", ".join(entry.get("ip") or entry.get("hostname", "-") for entry in external) or "-",
                "Age": humanize_age(metadata.get("creationTimestamp")),
            }
        )

    ingresses = []
    for item in snapshot.get("ingresses", []):
        metadata = item.get("metadata", {})
        hosts = []
        for rule in item.get("spec", {}).get("rules", []):
            if rule.get("host"):
                hosts.append(rule["host"])
        ingresses.append(
            {
                "Namespace": metadata.get("namespace", "default"),
                "Ingress": metadata.get("name", ""),
                "Hosts": ", ".join(hosts) or "-",
                "Age": humanize_age(metadata.get("creationTimestamp")),
            }
        )

    nodes = []
    for item in snapshot.get("nodes", []):
        metadata = item.get("metadata", {})
        status = item.get("status", {})
        nodes.append(
            {
                "Node": metadata.get("name", ""),
                "State": get_ready_condition(item),
                "Kubelet": status.get("nodeInfo", {}).get("kubeletVersion", "-"),
                "Age": humanize_age(metadata.get("creationTimestamp")),
            }
        )

    storage = []
    for item in snapshot.get("persistentvolumeclaims", []):
        metadata = item.get("metadata", {})
        storage.append(
            {
                "Namespace": metadata.get("namespace", "default"),
                "PVC": metadata.get("name", ""),
                "State": item.get("status", {}).get("phase", "Unknown"),
                "Volume": item.get("spec", {}).get("volumeName", "-"),
                "Size": item.get("status", {}).get("capacity", {}).get("storage", "-"),
                "Age": humanize_age(metadata.get("creationTimestamp")),
            }
        )

    config = []
    for key, label in (("configmaps", "ConfigMap"), ("secrets", "Secret")):
        for item in snapshot.get(key, []):
            metadata = item.get("metadata", {})
            config.append(
                {
                    "Kind": label,
                    "Namespace": metadata.get("namespace", "default"),
                    "Name": metadata.get("name", ""),
                    "Details": item.get("type", f"{len(item.get('data', {}))} keys"),
                    "Age": humanize_age(metadata.get("creationTimestamp")),
                }
            )

    events = []
    for item in snapshot.get("events", []):
        metadata = item.get("metadata", {})
        regarding = item.get("regarding", {})
        events.append(
            {
                "Namespace": metadata.get("namespace", "default"),
                "Type": item.get("type", "Normal"),
                "Reason": item.get("reason", "-"),
                "Object": f"{regarding.get('kind', '')}/{regarding.get('name', '')}".strip("/"),
                "Message": item.get("message") or item.get("note", "-"),
                "When": humanize_age(metadata.get("creationTimestamp")),
                "Timestamp": metadata.get("creationTimestamp", ""),
            }
        )

    node_metrics = pd.DataFrame(snapshot.get("node_metrics", []))
    if not node_metrics.empty:
        node_metrics = node_metrics.rename(
            columns={"name": "Node", "cpu": "CPU", "cpu_pct": "CPU %", "memory": "Memory", "memory_pct": "Memory %"}
        )

    pod_metrics = pd.DataFrame(snapshot.get("pod_metrics", []))
    if not pod_metrics.empty:
        pod_metrics = pod_metrics.rename(
            columns={"namespace": "Namespace", "name": "Pod", "cpu": "CPU", "memory": "Memory"}
        )

    pods_frame = pd.DataFrame(pods)
    if not pods_frame.empty:
        pods_frame = pods_frame.sort_values(by=["Status", "Restarts", "Namespace", "Pod"], ascending=[True, False, True, True])

    workloads_frame = pd.DataFrame(workloads)
    if not workloads_frame.empty:
        workloads_frame = workloads_frame.sort_values(by=["Health", "Namespace", "Name"])

    services_frame = pd.DataFrame(services)
    if not services_frame.empty:
        services_frame = services_frame.sort_values(by=["Namespace", "Service"])

    ingresses_frame = pd.DataFrame(ingresses)
    if not ingresses_frame.empty:
        ingresses_frame = ingresses_frame.sort_values(by=["Namespace", "Ingress"])

    nodes_frame = pd.DataFrame(nodes)
    if not nodes_frame.empty:
        nodes_frame = nodes_frame.sort_values(by=["State", "Node"])

    storage_frame = pd.DataFrame(storage)
    if not storage_frame.empty:
        storage_frame = storage_frame.sort_values(by=["Namespace", "PVC"])

    config_frame = pd.DataFrame(config)
    if not config_frame.empty:
        config_frame = config_frame.sort_values(by=["Namespace", "Kind", "Name"])

    events_frame = pd.DataFrame(events)
    if not events_frame.empty:
        events_frame = events_frame.sort_values(by=["Timestamp"], ascending=False)

    helm_frame = pd.DataFrame(snapshot.get("helm_releases", []))
    if not helm_frame.empty:
        helm_frame = helm_frame.rename(
            columns={
                "name": "Release",
                "namespace": "Namespace",
                "revision": "Revision",
                "updated": "Updated",
                "status": "Status",
                "chart": "Chart",
                "app_version": "App Version",
            }
        ).sort_values(by=["Namespace", "Release"])

    rbac_rows = []
    for binding in snapshot.get("rolebindings", []):
        metadata = binding.get("metadata", {})
        subjects = binding.get("subjects", [])
        risk, note = role_binding_risk(binding)
        rbac_rows.append(
            {
                "Scope": "Namespace",
                "Namespace": metadata.get("namespace", "default"),
                "Binding": metadata.get("name", ""),
                "Role": binding.get("roleRef", {}).get("name", ""),
                "Subjects": ", ".join(f"{subject.get('kind')}/{subject.get('name')}" for subject in subjects) or "-",
                "Risk": risk,
                "Why it matters": note,
            }
        )
    for binding in snapshot.get("clusterrolebindings", []):
        metadata = binding.get("metadata", {})
        subjects = binding.get("subjects", [])
        risk, note = role_binding_risk(binding)
        rbac_rows.append(
            {
                "Scope": "Cluster",
                "Namespace": "cluster-wide",
                "Binding": metadata.get("name", ""),
                "Role": binding.get("roleRef", {}).get("name", ""),
                "Subjects": ", ".join(f"{subject.get('kind')}/{subject.get('name')}" for subject in subjects) or "-",
                "Risk": risk,
                "Why it matters": note,
            }
        )
    rbac_frame = pd.DataFrame(rbac_rows)
    if not rbac_frame.empty:
        rbac_frame = rbac_frame.sort_values(by=["Risk", "Scope", "Namespace", "Binding"])

    security_rows = []
    for pod in snapshot.get("pods", []):
        metadata = pod.get("metadata", {})
        risk, note = pod_security_risk(pod)
        security_rows.append(
            {
                "Namespace": metadata.get("namespace", "default"),
                "Pod": metadata.get("name", ""),
                "Risk": risk,
                "Finding": note,
                "Age": humanize_age(metadata.get("creationTimestamp")),
            }
        )
    security_frame = pd.DataFrame(security_rows)
    if not security_frame.empty:
        security_frame = security_frame.sort_values(by=["Risk", "Namespace", "Pod"])

    return {
        "pods": pods_frame,
        "workloads": workloads_frame,
        "services": services_frame,
        "ingresses": ingresses_frame,
        "nodes": nodes_frame,
        "storage": storage_frame,
        "config": config_frame,
        "events": events_frame,
        "node_metrics": node_metrics,
        "pod_metrics": pod_metrics,
        "helm": helm_frame,
        "rbac": rbac_frame,
        "security": security_frame,
        "total_restarts": pd.DataFrame([{"value": total_restarts}]),
    }


def health_summary(frames: dict[str, pd.DataFrame], snapshot: dict[str, Any]) -> dict[str, Any]:
    pods = frames["pods"]
    workloads = frames["workloads"]
    nodes = frames["nodes"]
    warning_events = frames["events"][frames["events"]["Type"] == "Warning"] if not frames["events"].empty else pd.DataFrame()

    bad_pods = 0 if pods.empty else int((~pods["Status"].isin(["Running", "Succeeded"])).sum() + (pods["Status"] == "Degraded").sum())
    bad_workloads = 0 if workloads.empty else int((workloads["Health"] != "Healthy").sum())
    bad_nodes = 0 if nodes.empty else int((nodes["State"] != "Ready").sum())

    score = max(0, 100 - (bad_pods * 7) - (bad_workloads * 10) - (bad_nodes * 15) - (len(warning_events) * 2))
    if score >= 85:
        grade = "Healthy"
    elif score >= 65:
        grade = "Watch closely"
    else:
        grade = "Needs attention"

    captured_at = snapshot.get("captured_at")
    captured_label = "Unknown"
    if captured_at:
        captured_label = datetime.fromisoformat(captured_at).strftime("%d %b %Y, %H:%M")

    return {
        "score": score,
        "grade": grade,
        "captured_label": captured_label,
        "bad_pods": bad_pods,
        "bad_workloads": bad_workloads,
        "bad_nodes": bad_nodes,
        "warnings": len(warning_events),
    }


@st.cache_data(show_spinner=False, ttl=20)
def load_snapshot(context: str | None, use_sample: bool) -> tuple[dict[str, Any], list[str]]:
    if use_sample:
        return build_sample_snapshot(), ["You are viewing bundled sample data, not a live cluster."]

    client = KubeClient()
    snapshot, warnings = client.collect_snapshot(context)
    for key, command in (
        ("serviceaccounts", ["get", "serviceaccounts", "-A", "-o", "json"]),
        ("roles", ["get", "roles", "-A", "-o", "json"]),
        ("rolebindings", ["get", "rolebindings", "-A", "-o", "json"]),
        ("clusterroles", ["get", "clusterroles", "-o", "json"]),
        ("clusterrolebindings", ["get", "clusterrolebindings", "-o", "json"]),
    ):
        args = [*command, *(["--context", context] if context else [])]
        result = client._run(args)
        snapshot[key] = result.data.get("items", []) if result.ok and result.data else []
        if not result.ok and result.error:
            warnings.append(f"{key}: {result.error}")

    helm_releases, helm_error = client.helm_releases(context)
    snapshot["helm_releases"] = helm_releases
    snapshot["sample_logs"] = {}
    if helm_error:
        warnings.append(f"helm: {helm_error}")
    return snapshot, warnings


def maybe_refresh(seconds: int) -> None:
    if seconds <= 0:
        return
    components.html(
        f"""
        <script>
        window.setTimeout(function() {{
            window.parent.location.reload();
        }}, {seconds * 1000});
        </script>
        """,
        height=0,
    )


def resource_catalog(snapshot: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    return {
        "Pod": snapshot.get("pods", []),
        "Deployment": snapshot.get("deployments", []),
        "StatefulSet": snapshot.get("statefulsets", []),
        "DaemonSet": snapshot.get("daemonsets", []),
        "Service": snapshot.get("services", []),
        "Ingress": snapshot.get("ingresses", []),
        "ConfigMap": snapshot.get("configmaps", []),
        "Secret": snapshot.get("secrets", []),
        "PersistentVolumeClaim": snapshot.get("persistentvolumeclaims", []),
        "PersistentVolume": snapshot.get("persistentvolumes", []),
        "Job": snapshot.get("jobs", []),
        "CronJob": snapshot.get("cronjobs", []),
        "Node": snapshot.get("nodes", []),
        "Namespace": snapshot.get("namespaces", []),
        "ServiceAccount": snapshot.get("serviceaccounts", []),
        "Role": snapshot.get("roles", []),
        "RoleBinding": snapshot.get("rolebindings", []),
        "ClusterRole": snapshot.get("clusterroles", []),
        "ClusterRoleBinding": snapshot.get("clusterrolebindings", []),
    }


def available_workloads(snapshot: dict[str, Any], namespace: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for kind, key in (("Deployment", "deployments"), ("StatefulSet", "statefulsets"), ("DaemonSet", "daemonsets")):
        for resource in snapshot.get(key, []):
            metadata = resource.get("metadata", {})
            if namespace != "All namespaces" and metadata.get("namespace") != namespace:
                continue
            items.append({"kind": kind, "namespace": metadata.get("namespace", "default"), "name": metadata.get("name", "")})
    return items


def get_live_logs(client: KubeClient, context: str | None, namespace: str, pod: str, tail_lines: int, use_sample: bool, snapshot: dict[str, Any]) -> tuple[str | None, str | None]:
    return get_live_logs_for_container(client, context, namespace, pod, None, tail_lines, use_sample, snapshot)


def get_pod_containers(snapshot: dict[str, Any], namespace: str, pod: str) -> list[str]:
    for item in snapshot.get("pods", []):
        metadata = item.get("metadata", {})
        if metadata.get("namespace") != namespace or metadata.get("name") != pod:
            continue
        containers = item.get("spec", {}).get("containers", [])
        names = [container.get("name", "") for container in containers if container.get("name")]
        statuses = item.get("status", {}).get("containerStatuses", [])
        status_names = [status.get("name", "") for status in statuses if status.get("name")]
        merged: list[str] = []
        for name in names + status_names:
            if name and name not in merged:
                merged.append(name)
        return merged
    return []


def get_live_logs_for_container(
    client: KubeClient,
    context: str | None,
    namespace: str,
    pod: str,
    container: str | None,
    tail_lines: int,
    use_sample: bool,
    snapshot: dict[str, Any],
) -> tuple[str | None, str | None]:
    if use_sample:
        key = f"{namespace}/{pod}::{container or ''}".rstrip(":")
        sample_logs = snapshot.get("sample_logs", {})
        return sample_logs.get(key, "No sample logs were bundled for this pod/container."), None

    result = client.get_pod_logs(namespace=namespace, pod=pod, context=context, container=container, tail_lines=tail_lines)
    if result.ok and result.data:
        return result.data.get("raw", ""), None
    return None, result.error or "Could not load logs."


def get_exec_output(
    client: KubeClient,
    context: str | None,
    namespace: str,
    pod: str,
    container: str | None,
    command_text: str,
    use_sample: bool,
    snapshot: dict[str, Any],
) -> tuple[str | None, str | None]:
    if use_sample:
        key = f"{namespace}/{pod}::{container or ''}::{command_text.strip()}".replace("::::", "::")
        sample_exec = snapshot.get("sample_exec", {})
        return sample_exec.get(key, "Demo mode: no bundled output for that command."), None

    command = [part for part in command_text.strip().split() if part]
    if not command:
        return None, "Enter a command to run inside the pod."

    result = client.exec_in_pod(namespace=namespace, pod=pod, context=context, container=container, command=command)
    if result.ok and result.data:
        return result.data.get("raw", ""), None
    return None, result.error or "Could not run the command in the pod."


def action_resource_options(snapshot: dict[str, Any], namespace: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    mapping = (
        ("Deployment", "deployments"),
        ("StatefulSet", "statefulsets"),
        ("DaemonSet", "daemonsets"),
        ("Service", "services"),
        ("ConfigMap", "configmaps"),
        ("Secret", "secrets"),
        ("PersistentVolumeClaim", "persistentvolumeclaims"),
        ("Pod", "pods"),
    )
    for kind, key in mapping:
        for resource in snapshot.get(key, []):
            metadata = resource.get("metadata", {})
            resource_namespace = metadata.get("namespace", "cluster-wide")
            if namespace != "All namespaces" and resource_namespace != namespace:
                continue
            items.append({"kind": kind, "namespace": resource_namespace, "name": metadata.get("name", "")})
    return items


def ensure_sample_terminal() -> None:
    st.session_state.setdefault(
        "cluster_compass_sample_terminal",
        {
            "active": False,
            "pod": None,
            "shell": "/bin/sh",
            "history": [],
            "output": "Demo shell is ready.\n",
        },
    )


def start_sample_terminal(pod_label: str, container: str | None, shell: str) -> None:
    ensure_sample_terminal()
    st.session_state["cluster_compass_sample_terminal"] = {
        "active": True,
        "pod": pod_label,
        "container": container,
        "shell": shell,
        "history": [],
        "output": f"Connected to {pod_label}{f' ({container})' if container else ''} using {shell}\n",
    }


def send_sample_terminal_command(snapshot: dict[str, Any], pod_label: str, container: str | None, command_text: str) -> None:
    ensure_sample_terminal()
    sample_terminal = st.session_state["cluster_compass_sample_terminal"]
    key = f"{pod_label}::{container or ''}::{command_text.strip()}".replace("::::", "::")
    sample_exec = snapshot.get("sample_exec", {})
    output = sample_exec.get(key, f"Demo shell executed: {command_text}")
    sample_terminal["history"].append(command_text)
    sample_terminal["output"] += f"$ {command_text}\n{output}\n"
    st.session_state["cluster_compass_sample_terminal"] = sample_terminal


def close_sample_terminal() -> None:
    ensure_sample_terminal()
    sample_terminal = st.session_state["cluster_compass_sample_terminal"]
    sample_terminal["active"] = False
    sample_terminal["output"] += "Session closed.\n"
    st.session_state["cluster_compass_sample_terminal"] = sample_terminal


def main() -> None:
    initialize_theme_state()
    apply_theme(st.session_state["theme_mode"])

    client = KubeClient()
    terminal_manager = get_terminal_manager()
    contexts = client.get_contexts() if client.is_available() else []
    current_context = client.get_current_context()
    theme_options = ["System", "Light", "Dark"]

    with st.sidebar:
        st.markdown("## Cluster Compass")
        st.caption("A simpler way to understand what is happening inside your Kubernetes cluster.")

        live_available = client.is_available()
        use_sample = st.toggle("Use demo data", value=not live_available, help="Turn this on to explore the app without a live cluster.")
        st.selectbox("Theme", theme_options, key="theme_selector", on_change=handle_theme_change)

        selected_context = None
        if contexts and not use_sample:
            default_index = contexts.index(current_context) if current_context in contexts else 0
            selected_context = st.selectbox("Cluster context", contexts, index=default_index)
        elif not use_sample:
            st.info("No kube contexts were found. The app can still open in demo mode.")

        auto_refresh_enabled = st.toggle("Auto refresh cluster snapshot", value=False, help="Leave this off if you want the screen to stay stable while you review it.")
        refresh_seconds = 0
        if auto_refresh_enabled:
            refresh_seconds = st.select_slider("Refresh every", options=[15, 30, 60, 120], value=30 if not use_sample else 60)
        if st.button("Refresh now", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    st.title("")

    snapshot, warnings = load_snapshot(selected_context, use_sample)
    frames = build_frames(snapshot)
    summary = health_summary(frames, snapshot)

    namespaces = sorted(
        {
            item.get("metadata", {}).get("name", "")
            for item in snapshot.get("namespaces", [])
        }
        | {
            item.get("metadata", {}).get("namespace", "")
            for key in ("pods", "deployments", "services", "persistentvolumeclaims", "events")
            for item in snapshot.get(key, [])
        }
    )
    namespaces = [name for name in namespaces if name]
    namespace_choice = st.sidebar.selectbox("Focus on namespace", ["All namespaces", *namespaces]) if namespaces else "All namespaces"

    maybe_refresh(refresh_seconds)

    st.markdown(
        f"""
        <div class="hero">
            <div class="section-chip">Cluster summary</div>
            <h1>{snapshot.get("context", "Unknown cluster")}</h1>
            <p>Kubernetes {snapshot.get("version", "Unknown")} • Snapshot taken {summary["captured_label"]} • Source: {snapshot.get("source", "live").title()}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if warnings:
        with st.expander("Connection notes and warnings", expanded=snapshot.get("source") == "sample"):
            for note in warnings:
                st.write(f"- {note}")

    onboarding_guide()

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        metric_card("Cluster health", f"{summary['score']}/100", summary["grade"])
    with col2:
        metric_card("Namespaces", str(len(snapshot.get("namespaces", []))), "Logical folders for your apps and system tools")
    with col3:
        metric_card("Pods", str(len(snapshot.get("pods", []))), f"{summary['bad_pods']} need attention")
    with col4:
        metric_card("Workloads", str(len(frames["workloads"])), f"{summary['bad_workloads']} not fully healthy")
    with col5:
        total_restarts = int(frames["total_restarts"]["value"].iloc[0]) if not frames["total_restarts"].empty else 0
        metric_card("Container restarts", str(total_restarts), "Repeated restarts often mean app instability")

    overview_tab, workloads_tab, network_tab, storage_tab, operations_tab, governance_tab, explorer_tab = st.tabs(
        ["Overview", "Workloads", "Network & Access", "Storage & Config", "Operations", "Governance", "Events & Explorer"]
    )

    with overview_tab:
        guide(
            "What this means",
            "This page is a bird's-eye view. It helps a non-technical viewer answer: Is the cluster generally healthy, which namespace is busy, and are nodes under pressure?",
        )

        pod_frame = filter_namespace(frames["pods"], namespace_choice)
        workload_frame = filter_namespace(frames["workloads"], namespace_choice)
        event_frame = filter_namespace(frames["events"], namespace_choice)

        left, right = st.columns([1.1, 0.9])
        with left:
            if not pod_frame.empty:
                pod_status_counts = pod_frame["Status"].value_counts().reset_index()
                pod_status_counts.columns = ["Status", "Count"]
                fig = px.pie(
                    pod_status_counts,
                    names="Status",
                    values="Count",
                    hole=0.6,
                    color="Status",
                    color_discrete_map={
                        "Running": "#1f8a5b",
                        "Succeeded": "#7c9f35",
                        "Pending": "#d97706",
                        "Degraded": "#e5723a",
                        "CrashLoopBackOff": "#c2410c",
                    },
                )
                style_plotly_figure(fig, st.session_state["theme_mode"])
                fig.update_layout(height=340)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No pods found for this namespace filter.")

        with right:
            if not workload_frame.empty:
                workload_chart_frame = workload_frame.copy()
                workload_chart_frame["Ready Units"] = workload_chart_frame["Ready"].str.split("/").str[0].astype(int)
                fig = px.bar(
                    workload_chart_frame,
                    x="Name",
                    y="Ready Units",
                    color="Health",
                    hover_data=["Namespace", "Kind", "Ready"],
                    color_discrete_map={"Healthy": "#1f8a5b", "Degraded": "#d97706", "Critical": "#c2410c", "Idle": "#4c6b72"},
                )
                style_plotly_figure(fig, st.session_state["theme_mode"])
                fig.update_layout(height=340, xaxis_title="Workload", yaxis_title="Ready units")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No workloads found for this namespace filter.")

        lower_left, lower_right = st.columns([1.1, 0.9])
        with lower_left:
            if not frames["nodes"].empty:
                st.subheader("Nodes")
                st.dataframe(frames["nodes"], use_container_width=True, hide_index=True)
            if not frames["node_metrics"].empty:
                st.subheader("Node resource usage")
                st.dataframe(frames["node_metrics"], use_container_width=True, hide_index=True)
        with lower_right:
            if not event_frame.empty:
                st.subheader("Recent warning signals")
                warning_only = event_frame[event_frame["Type"] == "Warning"].head(8).drop(columns=["Timestamp"], errors="ignore")
                if warning_only.empty:
                    st.success("No warning events were found in the latest snapshot.")
                else:
                    st.dataframe(warning_only, use_container_width=True, hide_index=True)

    with workloads_tab:
        guide(
            "What lives here",
            "Workloads are the running parts of your applications. Pods are the actual running containers. Deployments, StatefulSets, and DaemonSets describe how Kubernetes should keep them running.",
        )

        search_text = st.text_input("Search workloads or pods", placeholder="Try api, payment, frontend, worker")

        workload_frame = filter_namespace(frames["workloads"], namespace_choice)
        pod_frame = filter_namespace(frames["pods"], namespace_choice)

        if search_text:
            lowered = search_text.lower()
            if not workload_frame.empty:
                workload_frame = workload_frame[
                    workload_frame["Name"].str.lower().str.contains(lowered) | workload_frame["Namespace"].str.lower().str.contains(lowered)
                ]
            if not pod_frame.empty:
                pod_frame = pod_frame[
                    pod_frame["Pod"].str.lower().str.contains(lowered) | pod_frame["Namespace"].str.lower().str.contains(lowered)
                ]

        workload_cols = st.columns([1.2, 1.8])
        with workload_cols[0]:
            st.subheader("Workload health")
            if workload_frame.empty:
                st.info("No workloads matched your filters.")
            else:
                st.dataframe(workload_frame, use_container_width=True, hide_index=True)
        with workload_cols[1]:
            st.subheader("Pods")
            if pod_frame.empty:
                st.info("No pods matched your filters.")
            else:
                st.dataframe(pod_frame, use_container_width=True, hide_index=True)

        if not frames["pod_metrics"].empty:
            st.subheader("Top pod resource usage")
            metrics_frame = filter_namespace(frames["pod_metrics"], namespace_choice)
            if search_text and not metrics_frame.empty:
                metrics_frame = metrics_frame[metrics_frame["Pod"].str.lower().str.contains(search_text.lower())]
            st.dataframe(metrics_frame, use_container_width=True, hide_index=True)

    with network_tab:
        guide(
            "Plain-English view",
            "Services let pods talk to each other or the outside world. Ingresses are the web entry doors, often used for app URLs.",
        )

        service_frame = filter_namespace(frames["services"], namespace_choice)
        ingress_frame = filter_namespace(frames["ingresses"], namespace_choice)

        left, right = st.columns(2)
        with left:
            st.subheader("Services")
            if service_frame.empty:
                st.info("No services found.")
            else:
                st.dataframe(service_frame, use_container_width=True, hide_index=True)
        with right:
            st.subheader("Ingresses")
            if ingress_frame.empty:
                st.info("No ingresses found.")
            else:
                st.dataframe(ingress_frame, use_container_width=True, hide_index=True)

    with storage_tab:
        guide(
            "Why this matters",
            "Persistent storage keeps data safe even if pods restart. ConfigMaps and Secrets hold settings and credentials used by your apps.",
        )

        storage_frame = filter_namespace(frames["storage"], namespace_choice)
        config_frame = filter_namespace(frames["config"], namespace_choice)

        left, right = st.columns(2)
        with left:
            st.subheader("Persistent volume claims")
            if storage_frame.empty:
                st.info("No persistent volume claims found.")
            else:
                st.dataframe(storage_frame, use_container_width=True, hide_index=True)
        with right:
            st.subheader("Config and secrets inventory")
            if config_frame.empty:
                st.info("No ConfigMaps or Secrets found.")
            else:
                st.dataframe(config_frame, use_container_width=True, hide_index=True)

    with operations_tab:
        guide(
            "Operator actions",
            "This section gives you practical tools for day-to-day operations: read logs, run safe pod commands, review Helm releases, and trigger guarded changes when you need them.",
        )

        logs_col, helm_col = st.columns([1.3, 1.1])
        with logs_col:
            st.subheader("Pod logs")
            pod_options = filter_namespace(frames["pods"], namespace_choice)
            if pod_options.empty:
                st.info("No pods available for the current namespace filter.")
            else:
                pod_labels = [f"{row.Namespace}/{row.Pod}" for row in pod_options.itertuples()]
                chosen_pod_label = st.selectbox("Choose a pod", pod_labels)
                chosen_namespace, chosen_pod = chosen_pod_label.split("/", 1)
                log_containers = get_pod_containers(snapshot, chosen_namespace, chosen_pod)
                selected_log_container = None
                if log_containers:
                    selected_log_container = st.selectbox("Choose a container", log_containers, key="logs_container_select")
                tail_lines = st.select_slider("How many log lines", options=[50, 100, 200, 500], value=200)
                if st.button("Load logs", use_container_width=True):
                    logs, error = get_live_logs_for_container(
                        client,
                        selected_context,
                        chosen_namespace,
                        chosen_pod,
                        selected_log_container,
                        tail_lines,
                        use_sample,
                        snapshot,
                    )
                    st.session_state["cluster_compass_logs"] = {
                        "text": logs,
                        "error": error,
                        "pod": chosen_pod_label,
                        "container": selected_log_container,
                    }

                log_state = st.session_state.get("cluster_compass_logs")
                if log_state:
                    container_caption = f" / {log_state['container']}" if log_state.get("container") else ""
                    st.caption(f"Showing logs for {log_state['pod']}{container_caption}")
                    if log_state.get("error"):
                        st.error(log_state["error"])
                    else:
                        st.code(log_state.get("text") or "No log output returned.", language="text")

            st.subheader("Pod terminal")
            st.caption("This keeps a shell session open across reruns, so you can inspect the pod, run several commands, and keep the history in one place.")
            if pod_options.empty:
                st.info("Select a namespace with pods to use the pod terminal.")
            else:
                exec_pod_label = st.selectbox("Pod for shell session", pod_labels, key="exec_pod_select")
                exec_namespace, exec_pod = exec_pod_label.split("/", 1)
                exec_containers = get_pod_containers(snapshot, exec_namespace, exec_pod)
                selected_exec_container = None
                if exec_containers:
                    selected_exec_container = st.selectbox("Container for shell session", exec_containers, key="exec_container_select")
                shell_choice = st.selectbox("Shell", ["/bin/sh", "/bin/bash"], index=0, key="shell_choice")

                if use_sample:
                    ensure_sample_terminal()
                    sample_terminal = st.session_state["cluster_compass_sample_terminal"]
                    sample_active = (
                        sample_terminal.get("active")
                        and sample_terminal.get("pod") == exec_pod_label
                        and sample_terminal.get("container") == selected_exec_container
                    )
                    terminal_status_text = "Connected" if sample_active else "Not connected"
                    terminal_error = None
                else:
                    live_session_id = st.session_state.get("cluster_compass_terminal_session")
                    session_open, terminal_error = terminal_manager.status(live_session_id) if live_session_id else (False, None)
                    session_matches = (
                        bool(live_session_id)
                        and st.session_state.get("cluster_compass_terminal_pod") == exec_pod_label
                        and st.session_state.get("cluster_compass_terminal_container") == selected_exec_container
                    )
                    sample_active = False
                    terminal_status_text = "Connected" if session_open and session_matches else "Not connected"

                start_col, stop_col, poll_col = st.columns([1, 1, 1.2])
                with start_col:
                    if st.button("Start shell", use_container_width=True):
                        if use_sample:
                            start_sample_terminal(exec_pod_label, selected_exec_container, shell_choice)
                        else:
                            existing_session_id = st.session_state.get("cluster_compass_terminal_session")
                            if existing_session_id:
                                terminal_manager.close_session(existing_session_id)
                            session_id, error = terminal_manager.open_session(
                                namespace=exec_namespace,
                                pod=exec_pod,
                                context=selected_context,
                                container=selected_exec_container,
                                shell=shell_choice,
                            )
                            if error:
                                st.session_state["cluster_compass_terminal_error"] = error
                            else:
                                st.session_state["cluster_compass_terminal_session"] = session_id
                                st.session_state["cluster_compass_terminal_pod"] = exec_pod_label
                                st.session_state["cluster_compass_terminal_container"] = selected_exec_container
                                st.session_state["cluster_compass_terminal_error"] = None
                                st.session_state["cluster_compass_terminal_history"] = []
                                st.rerun()
                with stop_col:
                    if st.button("Close shell", use_container_width=True):
                        if use_sample:
                            close_sample_terminal()
                        else:
                            existing_session_id = st.session_state.get("cluster_compass_terminal_session")
                            if existing_session_id:
                                terminal_manager.close_session(existing_session_id)
                            st.session_state["cluster_compass_terminal_session"] = None
                            st.session_state["cluster_compass_terminal_pod"] = None
                            st.session_state["cluster_compass_terminal_container"] = None
                with poll_col:
                    terminal_auto_refresh = st.checkbox("Auto refresh shell output", value=False, key="terminal_auto_refresh")
                    if terminal_auto_refresh:
                        shell_refresh_seconds = st.selectbox("Shell refresh", [3, 5, 10], index=1, key="shell_refresh_seconds")
                        maybe_refresh(shell_refresh_seconds)

                st.caption(f"Shell status: {terminal_status_text}")
                terminal_message = st.session_state.get("cluster_compass_terminal_error") or terminal_error
                if terminal_message:
                    st.error(terminal_message)

                command_text = st.text_input(
                    "Command",
                    value="printenv",
                    placeholder="printenv, ls /app, ps aux, env, cat /etc/os-release",
                    key="terminal_command_text",
                )
                run_disabled = terminal_status_text != "Connected"
                if st.button("Send command", use_container_width=True, disabled=run_disabled):
                    if use_sample:
                        send_sample_terminal_command(snapshot, exec_pod_label, selected_exec_container, command_text)
                    else:
                        session_id = st.session_state.get("cluster_compass_terminal_session")
                        error = terminal_manager.send_command(session_id, command_text) if session_id else "Terminal session not found."
                        if error:
                            st.session_state["cluster_compass_terminal_error"] = error
                        else:
                            history = st.session_state.get("cluster_compass_terminal_history", [])
                            history.append(command_text)
                            st.session_state["cluster_compass_terminal_history"] = history
                            st.rerun()

                if use_sample:
                    sample_terminal = st.session_state["cluster_compass_sample_terminal"]
                    terminal_output = sample_terminal.get("output", "")
                    terminal_history = sample_terminal.get("history", [])
                else:
                    session_id = st.session_state.get("cluster_compass_terminal_session")
                    terminal_output = terminal_manager.get_output(session_id) if session_id else ""
                    terminal_history = terminal_manager.get_history(session_id) if session_id else []

                shell_left, shell_right = st.columns([1.6, 0.8])
                with shell_left:
                    st.code(terminal_output or "No terminal output yet.", language="text")
                with shell_right:
                    st.write("**Command history**")
                    if terminal_history:
                        for item in reversed(terminal_history[-12:]):
                            st.code(item, language="text")
                    else:
                        st.caption("No commands sent yet.")

        with helm_col:
            st.subheader("Helm releases")
            helm_frame = filter_namespace(frames["helm"], namespace_choice)
            if helm_frame.empty:
                st.info("No Helm releases found, or Helm is not installed.")
            else:
                st.dataframe(helm_frame, use_container_width=True, hide_index=True)

        st.subheader("Rollout helper")
        rollout_options = available_workloads(snapshot, namespace_choice)
        if not rollout_options:
            st.info("No deployments, StatefulSets, or DaemonSets are available for rollout actions.")
        else:
            option_labels = [f"{item['namespace']} / {item['kind']} / {item['name']}" for item in rollout_options]
            selected_rollout = st.selectbox("Choose a workload", option_labels)
            selected_item = rollout_options[option_labels.index(selected_rollout)]
            restart_confirmation = st.text_input(
                "Type the workload name to allow restart",
                placeholder=selected_item["name"],
                key="restart_rollout_confirmation",
            )
            restart_enabled = restart_confirmation == selected_item["name"] and bool(selected_item["name"])
            action_col1, action_col2 = st.columns(2)
            with action_col1:
                if st.button("Check rollout status", use_container_width=True):
                    if use_sample:
                        st.session_state["cluster_compass_rollout"] = "Demo mode: rollout status looks healthy for this workload."
                    else:
                        result = client.rollout_status(
                            kind=selected_item["kind"],
                            name=selected_item["name"],
                            namespace=selected_item["namespace"],
                            context=selected_context,
                        )
                        st.session_state["cluster_compass_rollout"] = result.data.get("raw", "") if result.ok and result.data else result.error
            with action_col2:
                if st.button("Restart rollout", use_container_width=True, type="primary", disabled=not restart_enabled):
                    if use_sample:
                        st.session_state["cluster_compass_rollout"] = "Demo mode: rollout restart simulated successfully."
                    else:
                        result = client.rollout_restart(
                            kind=selected_item["kind"],
                            name=selected_item["name"],
                            namespace=selected_item["namespace"],
                            context=selected_context,
                        )
                        st.session_state["cluster_compass_rollout"] = result.data.get("raw", "") if result.ok and result.data else result.error
                if not restart_enabled:
                    st.caption("Restart stays locked until the exact workload name is typed.")

            rollout_message = st.session_state.get("cluster_compass_rollout")
            if rollout_message:
                st.code(rollout_message, language="text")

        st.subheader("Resource actions")
        guide(
            "Safety model",
            "Scaling and restarts happen immediately when your kube permissions allow them. Delete requires a typed confirmation using the exact resource name to reduce mistakes.",
        )

        action_options = action_resource_options(snapshot, namespace_choice)
        if not action_options:
            st.info("No supported resources are available for actions.")
        else:
            action_labels = [f"{item['namespace']} / {item['kind']} / {item['name']}" for item in action_options]
            selected_action_label = st.selectbox("Choose a resource", action_labels, key="resource_action_target")
            selected_action_item = action_options[action_labels.index(selected_action_label)]

            action_kind = selected_action_item["kind"]
            action_namespace = selected_action_item["namespace"]
            action_name = selected_action_item["name"]

            scale_allowed = action_kind in {"Deployment", "StatefulSet"}
            action_col1, action_col2, action_col3 = st.columns(3)

            with action_col1:
                if scale_allowed:
                    desired_replicas = st.number_input("Replicas", min_value=0, max_value=100, value=1, step=1)
                    if st.button("Scale resource", use_container_width=True):
                        if use_sample:
                            st.session_state["cluster_compass_action_result"] = f"Demo mode: scaled {action_kind}/{action_name} to {desired_replicas} replicas."
                        else:
                            result = client.scale_workload(
                                kind=action_kind,
                                name=action_name,
                                namespace=action_namespace,
                                replicas=int(desired_replicas),
                                context=selected_context,
                            )
                            st.session_state["cluster_compass_action_result"] = result.data.get("raw", "") if result.ok and result.data else result.error
                else:
                    st.caption("Scaling is available for Deployments and StatefulSets.")

            with action_col2:
                restart_allowed = action_kind in {"Deployment", "StatefulSet", "DaemonSet"}
                if restart_allowed:
                    if st.button("Restart resource", use_container_width=True):
                        if use_sample:
                            st.session_state["cluster_compass_action_result"] = f"Demo mode: restarted {action_kind}/{action_name}."
                        else:
                            result = client.rollout_restart(
                                kind=action_kind,
                                name=action_name,
                                namespace=action_namespace,
                                context=selected_context,
                            )
                            st.session_state["cluster_compass_action_result"] = result.data.get("raw", "") if result.ok and result.data else result.error
                else:
                    st.caption("Restart is available for workload-style resources.")

            with action_col3:
                typed_confirmation = st.text_input(
                    "Type the exact name to delete",
                    placeholder=action_name,
                    key="delete_confirmation_text",
                )
                delete_enabled = typed_confirmation == action_name and bool(action_name)
                if st.button("Delete resource", use_container_width=True, type="secondary", disabled=not delete_enabled):
                    if use_sample:
                        st.session_state["cluster_compass_action_result"] = f"Demo mode: deleted {action_kind}/{action_name} after confirmation."
                    else:
                        result = client.delete_resource(
                            kind=action_kind,
                            name=action_name,
                            namespace=action_namespace,
                            context=selected_context,
                        )
                        st.session_state["cluster_compass_action_result"] = result.data.get("raw", "") if result.ok and result.data else result.error
                if not delete_enabled:
                    st.caption("Delete stays locked until the exact resource name is typed.")

            action_result = st.session_state.get("cluster_compass_action_result")
            if action_result:
                st.code(action_result, language="text")

    with governance_tab:
        guide(
            "Risk and access view",
            "This page turns low-level security and permission details into a simpler review list. It helps you answer: Which workloads look risky, and who has powerful access?",
        )

        risk_col1, risk_col2, risk_col3 = st.columns(3)
        security_frame = filter_namespace(frames["security"], namespace_choice)
        rbac_frame = frames["rbac"] if namespace_choice == "All namespaces" else frames["rbac"][frames["rbac"]["Namespace"].isin([namespace_choice, "cluster-wide"])]
        with risk_col1:
            high_risk_pods = 0 if security_frame.empty else int(security_frame["Risk"].isin(["High", "Critical"]).sum())
            metric_card("Risky pods", str(high_risk_pods), "Pods with weaker runtime or token defaults")
        with risk_col2:
            elevated_bindings = 0 if rbac_frame.empty else int(rbac_frame["Risk"].isin(["High", "Critical"]).sum())
            metric_card("Elevated bindings", str(elevated_bindings), "Bindings that may grant broad access")
        with risk_col3:
            metric_card("Total restarts", str(count_container_restarts(snapshot)), "Useful context when security and reliability issues overlap")

        left, right = st.columns(2)
        with left:
            st.subheader("Workload security posture")
            if security_frame.empty:
                st.info("No workload security findings available.")
            else:
                st.dataframe(security_frame, use_container_width=True, hide_index=True)

        with right:
            st.subheader("RBAC review")
            if rbac_frame.empty:
                st.info("No RBAC bindings found.")
            else:
                st.dataframe(rbac_frame, use_container_width=True, hide_index=True)

        st.subheader("Simple guidance")
        if not security_frame.empty:
            top_security = security_frame.iloc[0]
            st.write(f"- Pod `{top_security['Pod']}` in `{top_security['Namespace']}`: {describe_risk(top_security['Risk'])} {top_security['Finding']}.")
        if not rbac_frame.empty:
            top_binding = rbac_frame.iloc[0]
            st.write(f"- Binding `{top_binding['Binding']}`: {describe_risk(top_binding['Risk'])} {top_binding['Why it matters']}.")
        if security_frame.empty and rbac_frame.empty:
            st.success("No obvious governance findings were detected from the current snapshot.")

    with explorer_tab:
        guide(
            "Deeper investigation",
            "Events explain what Kubernetes is trying to tell you. Resource Explorer lets you inspect a single object in detail without using command line tools.",
        )

        event_frame = filter_namespace(frames["events"], namespace_choice)
        st.subheader("Recent events")
        if event_frame.empty:
            st.info("No events found.")
        else:
            st.dataframe(event_frame.head(50).drop(columns=["Timestamp"], errors="ignore"), use_container_width=True, hide_index=True)

        st.subheader("Resource explorer")
        catalog = resource_catalog(snapshot)
        kind = st.selectbox("Resource type", list(catalog.keys()))
        namespace_items = catalog[kind]
        namespace_options = sorted({to_namespace_name(item)[0] for item in namespace_items})
        selected_namespace = st.selectbox("Namespace", namespace_options) if namespace_options else "cluster-wide"

        filtered_items = [item for item in namespace_items if to_namespace_name(item)[0] == selected_namespace]
        name_options = sorted({to_namespace_name(item)[1] for item in filtered_items})
        selected_name = st.selectbox("Resource name", name_options) if name_options else None

        selected_item = next((item for item in filtered_items if to_namespace_name(item)[1] == selected_name), None)
        if selected_item:
            details_col, raw_col = st.columns([0.95, 1.05])
            with details_col:
                metadata = selected_item.get("metadata", {})
                st.write(f"**Name:** {metadata.get('name', '-')}")
                st.write(f"**Namespace:** {metadata.get('namespace', 'cluster-wide')}")
                st.write(f"**Created:** {humanize_age(metadata.get('creationTimestamp'))}")
                labels = metadata.get("labels", {})
                if labels:
                    st.write("**Labels:**")
                    st.json(labels)
            with raw_col:
                raw_mode = st.radio("View format", ["YAML", "JSON"], horizontal=True)
                if raw_mode == "YAML":
                    st.code(yaml.safe_dump(selected_item, sort_keys=False), language="yaml")
                else:
                    st.code(json.dumps(selected_item, indent=2), language="json")


if __name__ == "__main__":
    main()
