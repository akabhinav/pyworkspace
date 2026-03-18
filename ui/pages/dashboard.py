"""Dashboard / Home page — overview metrics and workspace summary."""

from __future__ import annotations

from datetime import datetime, timezone

import plotly.graph_objects as go
import streamlit as st

from api_client import PyWorkspaceClient


def _status_color(status: str) -> str:
    return {
        "running": "#00C853",
        "paused": "#FFC107",
        "provisioning": "#2979FF",
        "error": "#FF5252",
        "destroying": "#FF5252",
    }.get(status, "#666")


def _status_badge(status: str) -> str:
    return f'<span class="status-badge status-{status}">{status}</span>'


def _tier_badge(tier: str) -> str:
    return f'<span class="tier-badge tier-{tier}">{tier}</span>'


def _relative_time(iso_str: str | None) -> str:
    if not iso_str:
        return "—"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = now - dt
        if diff.total_seconds() < 60:
            return "just now"
        if diff.total_seconds() < 3600:
            return f"{int(diff.total_seconds() / 60)}m ago"
        if diff.total_seconds() < 86400:
            return f"{int(diff.total_seconds() / 3600)}h ago"
        return f"{diff.days}d ago"
    except Exception:
        return str(iso_str)[:10]


def render(client: PyWorkspaceClient) -> None:
    # Header
    st.markdown(
        """
        <div class="page-header">
            <h1>Dashboard</h1>
            <p>Overview of your PyWorkspace environment</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    workspaces = client.list_workspaces()
    catalog = client.list_catalog()
    templates = client.list_templates()
    plugins = client.list_plugins()

    # ── Top metrics row ──────────────────────────────────────────────
    running = sum(1 for w in workspaces if w.get("status") == "running")
    paused = sum(1 for w in workspaces if w.get("status") == "paused")
    errors = sum(1 for w in workspaces if w.get("status") == "error")

    cols = st.columns(6)

    metrics = [
        ("Total Workspaces", len(workspaces), "+2 this week", "up"),
        ("Running", running, None, None),
        ("Paused", paused, None, None),
        ("Errors", errors, "needs attention" if errors else None, "down" if errors else None),
        ("Catalog Services", len(catalog), None, None),
        ("Plugins Active", len(plugins), None, None),
    ]

    for col, (label, value, delta_text, delta_dir) in zip(cols, metrics):
        delta_html = ""
        if delta_text:
            delta_html = f'<div class="metric-delta {delta_dir or ""}">{delta_text}</div>'
        col.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
                {delta_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    # ── Charts row ───────────────────────────────────────────────────
    left, right = st.columns([3, 2])

    with left:
        st.markdown("##### Workspace Status Distribution")
        status_counts = {}
        for w in workspaces:
            s = w.get("status", "unknown")
            status_counts[s] = status_counts.get(s, 0) + 1

        if status_counts:
            labels = list(status_counts.keys())
            values = list(status_counts.values())
            colors = [_status_color(s) for s in labels]

            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=labels,
                        values=values,
                        hole=0.55,
                        marker=dict(colors=colors, line=dict(color="#1B1B1B", width=2)),
                        textinfo="label+value",
                        textfont=dict(size=12, color="#DDD"),
                        hovertemplate="%{label}: %{value}<extra></extra>",
                    )
                ]
            )
            fig.update_layout(
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=10, b=10, l=10, r=10),
                height=280,
                font=dict(color="#DDD"),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No workspaces yet")

    with right:
        st.markdown("##### Resource Allocation by Tier")
        tier_counts = {}
        for w in workspaces:
            t = w.get("tier", "standard")
            tier_counts[t] = tier_counts.get(t, 0) + 1

        if tier_counts:
            tier_colors = {"dev": "#888", "standard": "#64B5F6", "enterprise": "#FF6E40"}
            fig2 = go.Figure(
                data=[
                    go.Bar(
                        x=list(tier_counts.keys()),
                        y=list(tier_counts.values()),
                        marker_color=[tier_colors.get(t, "#888") for t in tier_counts],
                        text=list(tier_counts.values()),
                        textposition="auto",
                        textfont=dict(color="#FFF", size=14),
                    )
                ]
            )
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=10, b=30, l=30, r=10),
                height=280,
                xaxis=dict(color="#888", gridcolor="#2A2A2A"),
                yaxis=dict(color="#888", gridcolor="#2A2A2A", dtick=1),
                font=dict(color="#DDD"),
            )
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # ── Recent workspaces table ──────────────────────────────────────
    st.markdown("##### Recent Workspaces")

    if workspaces:
        rows_html = ""
        for w in sorted(workspaces, key=lambda x: x.get("created_at", ""), reverse=True)[:10]:
            rows_html += f"""
            <tr>
                <td class="ws-name">{w.get('name', '')}</td>
                <td>{w.get('owner_id', '')}</td>
                <td>{_tier_badge(w.get('tier', 'standard'))}</td>
                <td>{_status_badge(w.get('status', 'unknown'))}</td>
                <td style="color:#888; font-size:0.8rem">{_relative_time(w.get('created_at'))}</td>
                <td style="color:#888; font-size:0.8rem">{w.get('id', '')[:12]}</td>
            </tr>
            """

        st.markdown(
            f"""
            <table class="workspace-table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Owner</th>
                        <th>Tier</th>
                        <th>Status</th>
                        <th>Created</th>
                        <th>ID</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="empty-state">
                <div class="icon">📦</div>
                <p>No workspaces yet. Create your first workspace to get started.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    # ── Quick links ──────────────────────────────────────────────────
    st.markdown("##### Quick Actions")
    qcols = st.columns(4)
    with qcols[0]:
        if st.button("➕  New Workspace", use_container_width=True, type="primary"):
            st.session_state.current_page = "Workspaces"
            st.session_state["ws_action"] = "create"
            st.rerun()
    with qcols[1]:
        if st.button("📋  Browse Templates", use_container_width=True):
            st.session_state.current_page = "Templates"
            st.rerun()
    with qcols[2]:
        if st.button("🔌  Manage Plugins", use_container_width=True):
            st.session_state.current_page = "Plugins"
            st.rerun()
    with qcols[3]:
        if st.button("📚  Service Catalog", use_container_width=True):
            st.session_state.current_page = "Catalog"
            st.rerun()
