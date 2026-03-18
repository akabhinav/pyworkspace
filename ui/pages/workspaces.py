"""Workspaces page — CRUD, lifecycle management, and workspace detail views."""

from __future__ import annotations

from datetime import datetime, timezone

import plotly.graph_objects as go
import streamlit as st

from api_client import PyWorkspaceClient

# ── Service icons ────────────────────────────────────────────────────

SERVICE_ICONS = {
    "postgres": "🐘", "redis": "🔴", "kafka": "📡", "mongodb": "🍃",
    "elasticsearch": "🔍", "mysql": "🐬", "rabbitmq": "🐰", "minio": "📦",
    "prometheus": "🔥", "grafana": "📊", "neo4j": "🕸️", "cassandra": "👁️",
    "localstack": "☁️", "jaeger": "🔭", "nats": "⚡", "jupyter": "📓",
    "clickhouse": "🏠", "loki": "📜", "memcached": "💾", "opensearch": "🔎",
    "sqlite": "📄", "docker": "🐳", "code_executor": "⚙️",
}


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
        return str(iso_str)[:16]


def render(client: PyWorkspaceClient) -> None:
    st.markdown(
        """
        <div class="page-header">
            <h1>Workspaces</h1>
            <p>Manage your development environments</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Check if we should show a detail view
    if "ws_detail_id" in st.session_state and st.session_state.ws_detail_id:
        _render_detail(client, st.session_state.ws_detail_id)
        return

    # ── Toolbar ──────────────────────────────────────────────────────
    tool_cols = st.columns([2, 1, 1, 1])
    with tool_cols[0]:
        search = st.text_input("Search workspaces", placeholder="Filter by name...", label_visibility="collapsed")
    with tool_cols[1]:
        status_filter = st.selectbox("Status", ["All", "running", "paused", "provisioning", "error"], label_visibility="collapsed")
    with tool_cols[2]:
        tier_filter = st.selectbox("Tier", ["All", "dev", "standard", "enterprise"], label_visibility="collapsed")
    with tool_cols[3]:
        if st.button("➕  Create Workspace", type="primary", use_container_width=True):
            st.session_state["ws_show_create"] = True

    # ── Create workspace dialog ──────────────────────────────────────
    if st.session_state.get("ws_show_create"):
        _render_create_form(client)

    # ── Workspace list ───────────────────────────────────────────────
    workspaces = client.list_workspaces()

    # Apply filters
    if search:
        workspaces = [w for w in workspaces if search.lower() in w.get("name", "").lower()]
    if status_filter != "All":
        workspaces = [w for w in workspaces if w.get("status") == status_filter]
    if tier_filter != "All":
        workspaces = [w for w in workspaces if w.get("tier") == tier_filter]

    if not workspaces:
        st.markdown(
            """
            <div class="empty-state">
                <div class="icon">📦</div>
                <p>No workspaces match your filters. Create one to get started.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # ── Render as cards ──────────────────────────────────────────────
    for w in sorted(workspaces, key=lambda x: x.get("created_at", ""), reverse=True):
        wid = w.get("id", "")
        status = w.get("status", "unknown")
        tier = w.get("tier", "standard")

        with st.container():
            cols = st.columns([3, 1, 1, 1, 2])

            with cols[0]:
                st.markdown(
                    f"""
                    <div style="padding: 0.3rem 0">
                        <span class="ws-name" style="font-size: 0.95rem">{w.get('name', '')}</span>
                        <span style="color: #666; font-size: 0.75rem; margin-left: 0.5rem">{wid[:12]}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with cols[1]:
                st.markdown(_tier_badge(tier), unsafe_allow_html=True)
            with cols[2]:
                st.markdown(_status_badge(status), unsafe_allow_html=True)
            with cols[3]:
                st.markdown(
                    f'<span style="color:#888; font-size:0.8rem">{_relative_time(w.get("created_at"))}</span>',
                    unsafe_allow_html=True,
                )
            with cols[4]:
                bcols = st.columns(4)
                with bcols[0]:
                    if st.button("👁️", key=f"view_{wid}", help="View details"):
                        st.session_state.ws_detail_id = wid
                        st.rerun()
                with bcols[1]:
                    if status == "running":
                        if st.button("⏸️", key=f"pause_{wid}", help="Pause"):
                            client.pause_workspace(wid)
                            st.toast(f"Pausing {w['name']}...")
                            st.rerun()
                    elif status == "paused":
                        if st.button("▶️", key=f"resume_{wid}", help="Resume"):
                            client.resume_workspace(wid)
                            st.toast(f"Resuming {w['name']}...")
                            st.rerun()
                with bcols[2]:
                    if st.button("📸", key=f"snap_{wid}", help="Snapshot"):
                        st.toast(f"Creating snapshot for {w['name']}...")
                with bcols[3]:
                    if st.button("🗑️", key=f"del_{wid}", help="Delete"):
                        st.session_state[f"confirm_del_{wid}"] = True

                # Delete confirmation
                if st.session_state.get(f"confirm_del_{wid}"):
                    st.warning(f"Delete **{w['name']}**? This cannot be undone.")
                    dc = st.columns(2)
                    with dc[0]:
                        if st.button("Yes, Delete", key=f"confirm_yes_{wid}", type="primary"):
                            client.delete_workspace(wid)
                            st.session_state.pop(f"confirm_del_{wid}", None)
                            st.toast(f"Destroying {w['name']}...")
                            st.rerun()
                    with dc[1]:
                        if st.button("Cancel", key=f"confirm_no_{wid}"):
                            st.session_state.pop(f"confirm_del_{wid}", None)
                            st.rerun()

            # Error message
            if w.get("error_message"):
                st.error(w["error_message"], icon="⚠️")

        st.markdown("<div class='separator'></div>", unsafe_allow_html=True)


def _render_create_form(client: PyWorkspaceClient) -> None:
    """Render the create workspace form."""
    with st.expander("Create New Workspace", expanded=True):
        templates = client.list_templates()

        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Workspace Name", placeholder="my-workspace")
            owner = st.text_input("Owner ID", value="admin")
            org = st.text_input("Org ID", value="acme-corp")
        with c2:
            template_names = ["(none)"] + [t["name"] for t in templates]
            template = st.selectbox("Template", template_names)
            tier = st.selectbox("Tier", ["dev", "standard", "enterprise"], index=1)
            ttl = st.number_input("TTL (hours)", min_value=1, max_value=720, value=24)

        st.markdown("**Resources**")
        rc1, rc2, rc3 = st.columns(3)
        with rc1:
            cpu = st.selectbox("CPU", ["1", "2", "4", "8", "16"], index=2)
        with rc2:
            memory = st.selectbox("Memory", ["1Gi", "2Gi", "4Gi", "8Gi", "16Gi", "32Gi"], index=3)
        with rc3:
            disk = st.selectbox("Disk", ["10Gi", "20Gi", "50Gi", "100Gi", "200Gi"], index=2)

        # Services selection
        st.markdown("**Services**")
        catalog = client.list_catalog()
        selected_services = st.multiselect(
            "Add services",
            [s["type"] for s in catalog],
            format_func=lambda x: f"{SERVICE_ICONS.get(x, '📦')} {x}",
        )

        fc1, fc2 = st.columns(2)
        with fc1:
            if st.button("Create", type="primary", use_container_width=True):
                if not name:
                    st.error("Workspace name is required")
                else:
                    payload = {
                        "name": name,
                        "owner_id": owner,
                        "org_id": org,
                        "tier": tier,
                        "template": template if template != "(none)" else None,
                        "ttl_hours": ttl,
                        "resources": {"cpu": cpu, "memory": memory, "disk": disk},
                        "services": [
                            {"name": s, "type": s, "version": "latest"} for s in selected_services
                        ],
                    }
                    result = client.create_workspace(payload)
                    st.session_state.pop("ws_show_create", None)
                    st.success(f"Workspace **{name}** created! ID: {result.get('id', 'N/A')}")
                    st.rerun()
        with fc2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.pop("ws_show_create", None)
                st.rerun()


def _render_detail(client: PyWorkspaceClient, wid: str) -> None:
    """Render workspace detail view."""
    # Back button
    if st.button("← Back to Workspaces"):
        st.session_state.ws_detail_id = None
        st.rerun()

    ws = client.get_workspace(wid)
    if not ws:
        st.error("Workspace not found")
        return

    status = ws.get("status", "unknown")
    tier = ws.get("tier", "standard")

    # Header
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; gap:1rem; margin-bottom:1.5rem">
            <div>
                <h2 style="margin:0; color:#FFF">{ws.get('name', '')}</h2>
                <span style="color:#888; font-size:0.8rem">{wid}</span>
            </div>
            <div style="margin-left:auto">
                {_tier_badge(tier)} &nbsp; {_status_badge(status)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Tabs
    tab_overview, tab_services, tab_snapshots, tab_usage, tab_agent = st.tabs(
        ["Overview", "Services", "Snapshots", "Usage & Cost", "Agent"]
    )

    with tab_overview:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Details**")
            st.markdown(f"- **Owner:** {ws.get('owner_id', '—')}")
            st.markdown(f"- **Organization:** {ws.get('org_id', '—')}")
            st.markdown(f"- **Namespace:** `{ws.get('k8s_namespace', '—')}`")
            st.markdown(f"- **DNS Zone:** `{ws.get('dns_zone', '—')}`")
            st.markdown(f"- **Created:** {_relative_time(ws.get('created_at'))}")
        with c2:
            st.markdown("**Lifecycle Actions**")
            ac = st.columns(3)
            with ac[0]:
                if status == "running":
                    if st.button("⏸️ Pause", use_container_width=True):
                        client.pause_workspace(wid)
                        st.rerun()
                elif status == "paused":
                    if st.button("▶️ Resume", use_container_width=True, type="primary"):
                        client.resume_workspace(wid)
                        st.rerun()
            with ac[1]:
                if st.button("📸 Snapshot", use_container_width=True):
                    st.toast("Snapshot created")
            with ac[2]:
                if st.button("🗑️ Delete", use_container_width=True):
                    client.delete_workspace(wid)
                    st.session_state.ws_detail_id = None
                    st.rerun()

            if ws.get("error_message"):
                st.error(ws["error_message"])

    with tab_services:
        # For demo, derive from known templates
        demo_services = [
            {"name": "postgres", "type": "postgres", "status": "healthy"},
            {"name": "redis", "type": "redis", "status": "healthy"},
            {"name": "kafka", "type": "kafka", "status": "healthy"},
        ]
        if demo_services:
            for svc in demo_services:
                sc = st.columns([1, 3, 1, 1])
                with sc[0]:
                    st.markdown(f"### {SERVICE_ICONS.get(svc['type'], '📦')}")
                with sc[1]:
                    st.markdown(f"**{svc['name']}** ({svc['type']})")
                    st.caption(f"DNS: `{svc['name']}.{ws.get('dns_zone', 'internal')}`")
                with sc[2]:
                    st.markdown(
                        '<span class="status-badge status-running">healthy</span>',
                        unsafe_allow_html=True,
                    )
                with sc[3]:
                    st.button("Configure", key=f"cfg_{svc['name']}")
                st.markdown("<div class='separator'></div>", unsafe_allow_html=True)
        else:
            st.info("No services provisioned yet")

    with tab_snapshots:
        snapshots = client.list_snapshots(wid)
        if snapshots:
            for snap in snapshots:
                sc = st.columns([2, 1, 1, 1, 1])
                with sc[0]:
                    st.markdown(f"**{snap.get('name', '')}**")
                    st.caption(snap.get("type", "manual"))
                with sc[1]:
                    size_mb = snap.get("size_bytes", 0) / (1024 * 1024)
                    st.metric("Size", f"{size_mb:.0f} MB")
                with sc[2]:
                    svcs = snap.get("services_included") or []
                    st.caption(", ".join(svcs) if svcs else "all")
                with sc[3]:
                    st.markdown(
                        f'<span class="status-badge status-running">{snap.get("status", "ready")}</span>',
                        unsafe_allow_html=True,
                    )
                with sc[4]:
                    st.button("Restore", key=f"restore_{snap.get('id')}")
                st.markdown("<div class='separator'></div>", unsafe_allow_html=True)
        else:
            st.info("No snapshots available")

        if st.button("📸 Create New Snapshot", type="primary"):
            st.toast("Snapshot creation started")

    with tab_usage:
        usage = client.get_workspace_usage(wid)
        cost = client.get_workspace_cost(wid)

        uc = st.columns(4)
        uc[0].metric("CPU Hours", f"{usage.get('cpu_core_hours', 0):.1f}")
        uc[1].metric("Memory GiB-Hours", f"{usage.get('memory_gib_hours', 0):.1f}")
        uc[2].metric("Disk GiB-Hours", f"{usage.get('disk_gib_hours', 0):.1f}")
        uc[3].metric("Network Egress", f"{usage.get('network_egress_gb', 0):.2f} GB")

        st.markdown("---")
        cc = st.columns(2)
        cc[0].metric("Estimated Cost", f"${cost.get('estimated_cost_usd', 0):.2f}")
        cc[1].metric("Actual Cost", f"${cost.get('actual_cost_usd', 0):.2f}")

        # Simple usage chart
        fig = go.Figure()
        categories = ["CPU", "Memory", "Disk", "Network"]
        values = [
            usage.get("cpu_core_hours", 0),
            usage.get("memory_gib_hours", 0),
            usage.get("disk_gib_hours", 0),
            usage.get("network_egress_gb", 0) * 10,
        ]
        fig.add_trace(
            go.Bar(
                x=categories,
                y=values,
                marker_color=["#FF3621", "#2979FF", "#FFC107", "#00C853"],
                text=[f"{v:.1f}" for v in values],
                textposition="auto",
                textfont=dict(color="#FFF"),
            )
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=10, b=30, l=30, r=10),
            height=250,
            xaxis=dict(color="#888", gridcolor="#2A2A2A"),
            yaxis=dict(color="#888", gridcolor="#2A2A2A"),
            font=dict(color="#DDD"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab_agent:
        st.markdown("**AI Agent**")
        st.markdown(
            """
            The PyOz agent has access to all workspace services and can execute
            tasks on your behalf.
            """
        )
        prompt = st.text_area("Send a prompt to the agent", placeholder="e.g., Create a users table in PostgreSQL")
        if st.button("Execute", type="primary"):
            if prompt:
                st.info(f"Agent task submitted: *{prompt}*")
            else:
                st.warning("Enter a prompt first")

        st.markdown("---")
        st.markdown("**Agent Status:** 🟢 Idle")
        st.markdown("**Execution History:** No recent tasks")
