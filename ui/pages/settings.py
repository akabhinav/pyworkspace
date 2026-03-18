"""Settings & Admin page — billing, auth, quotas, and platform configuration."""

from __future__ import annotations

import streamlit as st

from api_client import PyWorkspaceClient


def render(client: PyWorkspaceClient) -> None:
    st.markdown(
        """
        <div class="page-header">
            <h1>Settings</h1>
            <p>Platform configuration, billing, quotas, and administration</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_general, tab_billing, tab_quotas, tab_auth, tab_network, tab_api = st.tabs(
        ["General", "Billing & Usage", "Resource Quotas", "Auth & Security", "Networking", "API Status"]
    )

    # ── General ──────────────────────────────────────────────────────
    with tab_general:
        st.markdown("##### Organization Settings")
        gc = st.columns(2)
        with gc[0]:
            st.text_input("Organization Name", value="acme-corp")
            st.text_input("Admin Email", value="admin@acme.com")
            st.selectbox("Default Tier", ["dev", "standard", "enterprise"], index=1)
        with gc[1]:
            st.number_input("Default TTL (hours)", min_value=1, max_value=720, value=24)
            st.selectbox("Auto-Snapshot", ["Enabled", "Disabled"], index=0)
            st.selectbox("Default Region", ["us-east-1", "us-west-2", "eu-west-1"])

        st.markdown("---")
        st.markdown("##### Workspace Defaults")
        dc = st.columns(3)
        with dc[0]:
            st.selectbox("Default CPU", ["1", "2", "4", "8"], index=2, key="def_cpu")
        with dc[1]:
            st.selectbox("Default Memory", ["2Gi", "4Gi", "8Gi", "16Gi"], index=2, key="def_mem")
        with dc[2]:
            st.selectbox("Default Disk", ["10Gi", "20Gi", "50Gi", "100Gi"], index=2, key="def_disk")

        if st.button("Save General Settings", type="primary"):
            st.success("Settings saved successfully")

    # ── Billing ──────────────────────────────────────────────────────
    with tab_billing:
        st.markdown("##### Organization Usage Summary")

        mc = st.columns(4)
        mc[0].markdown(
            """
            <div class="metric-card">
                <div class="metric-value">$2,847</div>
                <div class="metric-label">Current Month Cost</div>
                <div class="metric-delta up">+12% vs last month</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        mc[1].markdown(
            """
            <div class="metric-card">
                <div class="metric-value">342.5</div>
                <div class="metric-label">CPU Core-Hours</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        mc[2].markdown(
            """
            <div class="metric-card">
                <div class="metric-value">1,024</div>
                <div class="metric-label">Memory GiB-Hours</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        mc[3].markdown(
            """
            <div class="metric-card">
                <div class="metric-value">15.2 GB</div>
                <div class="metric-label">Network Egress</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        st.markdown("##### Per-Workspace Cost Breakdown")

        workspaces = client.list_workspaces()
        for ws in workspaces[:5]:
            cost = client.get_workspace_cost(ws["id"])
            wc = st.columns([3, 1, 1, 1])
            with wc[0]:
                st.markdown(f"**{ws['name']}**")
            with wc[1]:
                st.markdown(f"`{ws.get('tier', 'standard')}`")
            with wc[2]:
                st.markdown(f"Est: **${cost.get('estimated_cost_usd', 0):.2f}**")
            with wc[3]:
                st.markdown(f"Actual: **${cost.get('actual_cost_usd', 0):.2f}**")
            st.markdown("<div class='separator'></div>", unsafe_allow_html=True)

    # ── Resource Quotas ──────────────────────────────────────────────
    with tab_quotas:
        st.markdown("##### Tier Quotas")

        tiers = {
            "dev": {"max_services": 3, "max_cpu": "4", "max_memory": "8Gi", "max_disk": "50Gi", "max_workspaces": 5},
            "standard": {"max_services": 8, "max_cpu": "16", "max_memory": "32Gi", "max_disk": "200Gi", "max_workspaces": 20},
            "enterprise": {"max_services": 25, "max_cpu": "64", "max_memory": "128Gi", "max_disk": "1Ti", "max_workspaces": 100},
        }

        for tier_name, limits in tiers.items():
            badge_class = f"tier-{tier_name}"
            st.markdown(
                f'<span class="tier-badge {badge_class}" style="font-size:0.85rem; padding:4px 12px">{tier_name.upper()}</span>',
                unsafe_allow_html=True,
            )

            qc = st.columns(5)
            qc[0].metric("Max Services", limits["max_services"])
            qc[1].metric("Max CPU", limits["max_cpu"])
            qc[2].metric("Max Memory", limits["max_memory"])
            qc[3].metric("Max Disk", limits["max_disk"])
            qc[4].metric("Max Workspaces", limits["max_workspaces"])
            st.markdown("<div class='separator'></div>", unsafe_allow_html=True)

    # ── Auth & Security ──────────────────────────────────────────────
    with tab_auth:
        st.markdown("##### Authentication Configuration")

        ac = st.columns(2)
        with ac[0]:
            st.selectbox("Auth Method", ["JWT (default)", "mTLS", "API Key", "OAuth2"])
            st.text_input("JWT Secret", value="••••••••••••••••", type="password")
            st.number_input("Token Expiry (minutes)", value=60, min_value=5, max_value=1440)
        with ac[1]:
            st.selectbox("RBAC Mode", ["Standard (admin/member/viewer)", "Custom Roles"])
            st.checkbox("Enforce MFA", value=False)
            st.checkbox("Audit Logging", value=True)

        st.markdown("---")
        st.markdown("##### Users & Roles")

        users = [
            {"email": "admin@acme.com", "role": "admin", "status": "active"},
            {"email": "alice@acme.com", "role": "member", "status": "active"},
            {"email": "bob@acme.com", "role": "member", "status": "active"},
            {"email": "carol@acme.com", "role": "viewer", "status": "active"},
            {"email": "dave@acme.com", "role": "member", "status": "inactive"},
        ]

        rows = ""
        for u in users:
            role_color = {"admin": "#FF6E40", "member": "#64B5F6", "viewer": "#888"}.get(u["role"], "#888")
            status_color = "#00C853" if u["status"] == "active" else "#666"
            rows += f"""
            <tr>
                <td>{u['email']}</td>
                <td><span style="color:{role_color}; font-weight:600">{u['role']}</span></td>
                <td><span style="color:{status_color}">{u['status']}</span></td>
            </tr>
            """

        st.markdown(
            f"""
            <table class="workspace-table">
                <thead>
                    <tr><th>Email</th><th>Role</th><th>Status</th></tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Save Auth Settings", type="primary"):
            st.success("Auth settings saved")

    # ── Networking ───────────────────────────────────────────────────
    with tab_network:
        st.markdown("##### DNS Configuration")
        nc = st.columns(2)
        with nc[0]:
            st.text_input("Base Domain", value="pyworkspace.internal")
            st.text_input("DNS Provider", value="CoreDNS (internal)")
        with nc[1]:
            st.checkbox("Auto-create DNS entries", value=True)
            st.checkbox("Enable egress filtering", value=True)

        st.markdown("---")
        st.markdown("##### Port Allocation")
        st.markdown("Port range: `30000 - 32767`")

        ports = [
            {"workspace": "ml-training-pipeline", "service": "postgres", "port": 30001},
            {"workspace": "ml-training-pipeline", "service": "redis", "port": 30002},
            {"workspace": "ecommerce-staging", "service": "postgres", "port": 30003},
            {"workspace": "ecommerce-staging", "service": "kafka", "port": 30004},
        ]

        rows = ""
        for p in ports:
            rows += f"""
            <tr>
                <td>{p['workspace']}</td>
                <td>{p['service']}</td>
                <td><code>{p['port']}</code></td>
            </tr>
            """

        st.markdown(
            f"""
            <table class="workspace-table">
                <thead>
                    <tr><th>Workspace</th><th>Service</th><th>Port</th></tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.markdown("##### Network Policies")
        st.checkbox("Isolate workspace namespaces", value=True)
        st.checkbox("Allow inter-workspace communication", value=False)
        st.checkbox("Enable Ingress controller", value=True)

        if st.button("Save Network Settings", type="primary"):
            st.success("Network settings saved")

    # ── API Status ───────────────────────────────────────────────────
    with tab_api:
        st.markdown("##### Backend API Status")

        health = client.health()
        if health.get("status") == "healthy":
            st.success("API is healthy and responding", icon="🟢")
        elif health.get("status") == "ready":
            st.info("API is ready", icon="🔵")
        else:
            st.warning("API is unreachable — UI is running in demo mode", icon="🟡")

        st.json(health)

        st.markdown("---")
        st.markdown("##### API Endpoints")

        endpoints = [
            ("GET", "/health", "Health check"),
            ("GET", "/ready", "Readiness check"),
            ("GET", "/v1/workspaces", "List workspaces"),
            ("POST", "/v1/workspaces", "Create workspace"),
            ("GET", "/v1/workspaces/{id}", "Get workspace"),
            ("PATCH", "/v1/workspaces/{id}", "Update workspace"),
            ("DELETE", "/v1/workspaces/{id}", "Delete workspace"),
            ("POST", "/v1/workspaces/{id}/pause", "Pause workspace"),
            ("POST", "/v1/workspaces/{id}/resume", "Resume workspace"),
            ("POST", "/v1/workspaces/{id}/clone", "Clone workspace"),
            ("GET", "/v1/catalog", "List catalog services"),
            ("GET", "/v1/catalog/{type}", "Get service details"),
            ("GET", "/v1/templates", "List templates"),
            ("POST", "/v1/templates", "Create template"),
            ("GET", "/v1/plugins", "List plugins"),
            ("POST", "/v1/plugins/register", "Register plugin"),
            ("DELETE", "/v1/plugins/{name}", "Unregister plugin"),
            ("POST", "/v1/plugins/discover", "Discover plugins"),
            ("GET", "/v1/workspaces/{id}/snapshots", "List snapshots"),
            ("POST", "/v1/workspaces/{id}/snapshots", "Create snapshot"),
            ("GET", "/v1/workspaces/{id}/usage", "Get usage"),
            ("GET", "/v1/workspaces/{id}/cost", "Get cost"),
            ("POST", "/v1/workspaces/{id}/agent/execute", "Execute agent prompt"),
        ]

        rows = ""
        for method, path, desc in endpoints:
            method_color = {
                "GET": "#00C853",
                "POST": "#2979FF",
                "PATCH": "#FFC107",
                "DELETE": "#FF5252",
            }.get(method, "#888")
            rows += f"""
            <tr>
                <td><span style="color:{method_color}; font-weight:700; font-size:0.75rem">{method}</span></td>
                <td><code style="font-size:0.8rem">{path}</code></td>
                <td style="color:#999">{desc}</td>
            </tr>
            """

        st.markdown(
            f"""
            <table class="workspace-table">
                <thead>
                    <tr><th>Method</th><th>Endpoint</th><th>Description</th></tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
            """,
            unsafe_allow_html=True,
        )
