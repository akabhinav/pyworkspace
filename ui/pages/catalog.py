"""Service Catalog page — browse and explore available services."""

from __future__ import annotations

import streamlit as st

from api_client import PyWorkspaceClient

SERVICE_ICONS = {
    "postgres": "🐘", "redis": "🔴", "kafka": "📡", "mongodb": "🍃",
    "elasticsearch": "🔍", "mysql": "🐬", "rabbitmq": "🐰", "minio": "📦",
    "prometheus": "🔥", "grafana": "📊", "neo4j": "🕸️", "cassandra": "👁️",
    "localstack": "☁️", "jaeger": "🔭", "nats": "⚡", "jupyter": "📓",
    "clickhouse": "🏠", "loki": "📜", "memcached": "💾", "opensearch": "🔎",
    "sqlite": "📄", "docker": "🐳", "code_executor": "⚙️",
}

CATEGORY_COLORS = {
    "database": "#2979FF",
    "cache": "#FF6E40",
    "messaging": "#00C853",
    "monitoring": "#FFC107",
    "cloud": "#7C4DFF",
    "storage": "#7C4DFF",
    "search": "#00BCD4",
    "runtime": "#E040FB",
}


def render(client: PyWorkspaceClient) -> None:
    st.markdown(
        """
        <div class="page-header">
            <h1>Service Catalog</h1>
            <p>Browse and provision infrastructure services for your workspaces</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    catalog = client.list_catalog()

    # ── Toolbar ──────────────────────────────────────────────────────
    tc = st.columns([3, 1, 1])
    with tc[0]:
        search = st.text_input(
            "Search services",
            placeholder="Search by name, type, or category...",
            label_visibility="collapsed",
        )
    with tc[1]:
        # Collect all categories
        all_cats = set()
        for svc in catalog:
            for c in svc.get("categories", []):
                all_cats.add(c)
        cat_filter = st.selectbox(
            "Category",
            ["All"] + sorted(all_cats),
            label_visibility="collapsed",
        )
    with tc[2]:
        source_filter = st.selectbox(
            "Source",
            ["All", "builtin", "plugin"],
            label_visibility="collapsed",
        )

    # Apply filters
    if search:
        catalog = [
            s for s in catalog
            if search.lower() in s.get("type", "").lower()
            or search.lower() in s.get("display_name", "").lower()
            or search.lower() in s.get("description", "").lower()
        ]
    if cat_filter != "All":
        catalog = [s for s in catalog if cat_filter in s.get("categories", [])]
    if source_filter != "All":
        catalog = [s for s in catalog if s.get("source") == source_filter]

    # ── Stats bar ────────────────────────────────────────────────────
    sc = st.columns(4)
    sc[0].markdown(f"**{len(catalog)}** services available")
    builtin_ct = sum(1 for s in catalog if s.get("source") == "builtin")
    plugin_ct = sum(1 for s in catalog if s.get("source") == "plugin")
    sc[1].markdown(f"🔧 {builtin_ct} built-in")
    sc[2].markdown(f"🔌 {plugin_ct} from plugins")
    sc[3].markdown(f"📂 {len(all_cats)} categories")

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # ── Service cards grid ───────────────────────────────────────────
    if not catalog:
        st.markdown(
            """
            <div class="empty-state">
                <div class="icon">🔍</div>
                <p>No services match your search criteria.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    cols_per_row = 3
    for i in range(0, len(catalog), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            idx = i + j
            if idx >= len(catalog):
                break
            svc = catalog[idx]
            stype = svc.get("type", "")
            icon = SERVICE_ICONS.get(stype, "📦")
            categories = svc.get("categories", [])
            versions = svc.get("versions", [])
            source = svc.get("source", "builtin")

            cat_tags = "".join(
                f'<span class="svc-tag" style="border-left:2px solid {CATEGORY_COLORS.get(c, "#666")}">{c}</span>'
                for c in categories
            )
            version_list = ", ".join(versions[:4])
            source_label = "🔧 Built-in" if source == "builtin" else "🔌 Plugin"

            with col:
                st.markdown(
                    f"""
                    <div class="service-card">
                        <div class="svc-icon">{icon}</div>
                        <h4>{svc.get('display_name', stype)}</h4>
                        <p>{svc.get('description', '')}</p>
                        <div>{cat_tags}</div>
                        <div class="svc-meta">
                            <div>Versions: {version_list}</div>
                            <div>Default: <strong>{svc.get('default_version', 'latest')}</strong></div>
                            <div>{source_label}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ── Service detail expander ──────────────────────────────────────
    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    st.markdown("##### Service Details")

    selected = st.selectbox(
        "Select a service to view details",
        [s["type"] for s in catalog],
        format_func=lambda x: f"{SERVICE_ICONS.get(x, '📦')} {x}",
    )

    if selected:
        detail = client.get_catalog_service(selected)
        if detail:
            dc = st.columns(2)
            with dc[0]:
                st.markdown(f"### {SERVICE_ICONS.get(selected, '📦')} {detail.get('display_name', selected)}")
                st.markdown(detail.get("description", ""))
                st.markdown(f"**Default version:** `{detail.get('default_version', 'latest')}`")
                st.markdown(f"**Supported versions:** {', '.join(detail.get('versions', detail.get('supported_versions', [])))}")
                st.markdown(f"**Default port:** `{detail.get('default_port', 'N/A')}`")
            with dc[1]:
                st.markdown("**Categories**")
                for c in detail.get("categories", []):
                    color = CATEGORY_COLORS.get(c, "#666")
                    st.markdown(f'<span class="svc-tag" style="border-left:2px solid {color}; font-size:0.8rem; padding:4px 10px">{c}</span>', unsafe_allow_html=True)

                if detail.get("agent_tools"):
                    st.markdown("**Agent Tools**")
                    for tool in detail["agent_tools"]:
                        st.code(tool, language=None)

                if detail.get("default_resources"):
                    st.markdown("**Default Resources**")
                    res = detail["default_resources"]
                    st.markdown(f"CPU: `{res.get('cpu', '1')}` | Memory: `{res.get('memory', '1Gi')}` | Disk: `{res.get('disk', '10Gi')}`")
