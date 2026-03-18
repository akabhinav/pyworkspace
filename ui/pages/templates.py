"""Templates page — gallery of workspace templates."""

from __future__ import annotations

import streamlit as st

from api_client import PyWorkspaceClient

TEMPLATE_ICONS = {
    "blank": "📄",
    "fastapi-full-stack": "⚡",
    "django-postgres-redis": "🎸",
    "ml-platform": "🧠",
    "microservices-full": "🔗",
    "data-engineering": "🔧",
    "ecommerce-full": "🛒",
    "spring-boot-enterprise": "🍃",
    "fintech-banking": "🏦",
}

CATEGORY_COLORS = {
    "general": "#888",
    "backend": "#2979FF",
    "data-science": "#00C853",
    "enterprise": "#FF6E40",
    "frontend": "#E040FB",
}


def render(client: PyWorkspaceClient) -> None:
    st.markdown(
        """
        <div class="page-header">
            <h1>Templates</h1>
            <p>Pre-configured workspace blueprints — start building in seconds</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    templates = client.list_templates()

    # ── Toolbar ──────────────────────────────────────────────────────
    tc = st.columns([3, 1, 1])
    with tc[0]:
        search = st.text_input(
            "Search templates",
            placeholder="Search by name or description...",
            label_visibility="collapsed",
        )
    with tc[1]:
        all_cats = sorted(set(t.get("category", "general") for t in templates))
        cat_filter = st.selectbox("Category", ["All"] + all_cats, label_visibility="collapsed")
    with tc[2]:
        sort_by = st.selectbox("Sort by", ["Most Popular", "Name A-Z", "Name Z-A"], label_visibility="collapsed")

    # Filters
    if search:
        templates = [
            t for t in templates
            if search.lower() in t.get("name", "").lower()
            or search.lower() in t.get("display_name", "").lower()
            or search.lower() in t.get("description", "").lower()
        ]
    if cat_filter != "All":
        templates = [t for t in templates if t.get("category") == cat_filter]

    if sort_by == "Most Popular":
        templates.sort(key=lambda t: t.get("usage_count", 0), reverse=True)
    elif sort_by == "Name A-Z":
        templates.sort(key=lambda t: t.get("display_name", ""))
    elif sort_by == "Name Z-A":
        templates.sort(key=lambda t: t.get("display_name", ""), reverse=True)

    # ── Stats ────────────────────────────────────────────────────────
    total_usage = sum(t.get("usage_count", 0) for t in templates)
    sc = st.columns(3)
    sc[0].markdown(f"**{len(templates)}** templates")
    sc[1].markdown(f"📊 {total_usage:,} total deployments")
    sc[2].markdown(f"📂 {len(all_cats)} categories")

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # ── Template grid ────────────────────────────────────────────────
    if not templates:
        st.markdown(
            """
            <div class="empty-state">
                <div class="icon">📋</div>
                <p>No templates match your search criteria.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    cols_per_row = 3
    for i in range(0, len(templates), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            idx = i + j
            if idx >= len(templates):
                break
            t = templates[idx]
            name = t.get("name", "")
            display_name = t.get("display_name", name)
            desc = t.get("description", "")
            category = t.get("category", "general")
            usage = t.get("usage_count", 0)
            is_builtin = t.get("is_builtin", False)
            icon = TEMPLATE_ICONS.get(name, "📋")
            cat_color = CATEGORY_COLORS.get(category, "#888")

            builtin_badge = (
                '<span class="svc-tag" style="border-left:2px solid #00C853">built-in</span>'
                if is_builtin
                else '<span class="svc-tag" style="border-left:2px solid #FFC107">custom</span>'
            )

            with col:
                st.markdown(
                    f"""
                    <div class="template-card">
                        <div style="font-size:2rem; margin-bottom:0.5rem">{icon}</div>
                        <h4>{display_name}</h4>
                        <p>{desc}</p>
                        <div style="margin-bottom:0.5rem">
                            <span class="svc-tag" style="border-left:2px solid {cat_color}">{category}</span>
                            {builtin_badge}
                        </div>
                        <div class="template-usage">
                            🚀 {usage:,} deployments
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                tc2 = st.columns(2)
                with tc2[0]:
                    if st.button("Use Template", key=f"use_{name}", use_container_width=True, type="primary"):
                        st.session_state.current_page = "Workspaces"
                        st.session_state["ws_show_create"] = True
                        st.rerun()
                with tc2[1]:
                    if st.button("Details", key=f"det_{name}", use_container_width=True):
                        st.session_state["tmpl_detail"] = name

    # ── Template detail ──────────────────────────────────────────────
    detail_name = st.session_state.get("tmpl_detail")
    if detail_name:
        st.markdown("---")
        tmpl = next((t for t in client.list_templates() if t.get("name") == detail_name), None)
        if tmpl:
            st.markdown(f"### {TEMPLATE_ICONS.get(detail_name, '📋')} {tmpl.get('display_name', detail_name)}")
            st.markdown(tmpl.get("description", ""))

            dc = st.columns(3)
            dc[0].metric("Category", tmpl.get("category", "general"))
            dc[1].metric("Deployments", f"{tmpl.get('usage_count', 0):,}")
            dc[2].metric("Type", "Built-in" if tmpl.get("is_builtin") else "Custom")

            if st.button("Close Details"):
                st.session_state.pop("tmpl_detail", None)
                st.rerun()

    # ── Create custom template ───────────────────────────────────────
    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    with st.expander("Create Custom Template"):
        c1, c2 = st.columns(2)
        with c1:
            tmpl_name = st.text_input("Template Name", placeholder="my-template")
            tmpl_display = st.text_input("Display Name", placeholder="My Custom Template")
            tmpl_cat = st.selectbox("Category", ["general", "backend", "data-science", "enterprise", "frontend"])
        with c2:
            tmpl_desc = st.text_area("Description", placeholder="Describe this template...")
            tmpl_yaml = st.text_area(
                "Spec (YAML)",
                placeholder="services:\n  - name: postgres\n    type: postgres\n    version: '16'",
                height=120,
            )
        if st.button("Create Template", type="primary"):
            if tmpl_name and tmpl_display:
                st.success(f"Template **{tmpl_display}** created!")
            else:
                st.error("Name and display name are required")
