"""Plugins page — manage external components (PySandbox, PyGate, PyMem, etc.)."""

from __future__ import annotations

import streamlit as st

from api_client import PyWorkspaceClient

PLUGIN_ICONS = {
    "pysandbox": "🔒",
    "pygate": "🤖",
    "pymem": "🧠",
    "pytrace": "🔭",
    "pytool": "🔧",
    "pyreview": "📝",
}


def render(client: PyWorkspaceClient) -> None:
    st.markdown(
        """
        <div class="page-header">
            <h1>Plugins</h1>
            <p>External components that extend PyWorkspace capabilities</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    plugins = client.list_plugins()

    # ── Stats bar ────────────────────────────────────────────────────
    total_tools = sum(len(p.get("tools", [])) for p in plugins)
    sc = st.columns(4)
    sc[0].markdown(f"**{len(plugins)}** plugins registered")
    sc[1].markdown(f"🔧 {total_tools} tools available")
    all_cats = set()
    for p in plugins:
        for c in p.get("categories", []):
            all_cats.add(c)
    sc[2].markdown(f"📂 {len(all_cats)} categories")
    sc[3].markdown("")

    # ── Toolbar ──────────────────────────────────────────────────────
    tc = st.columns([3, 1])
    with tc[0]:
        search = st.text_input("Search plugins", placeholder="Filter by name...", label_visibility="collapsed")
    with tc[1]:
        if st.button("🔍 Discover Plugins", use_container_width=True, type="primary"):
            st.session_state["show_discover"] = True

    if search:
        plugins = [
            p for p in plugins
            if search.lower() in p.get("name", "").lower()
            or search.lower() in p.get("display_name", "").lower()
            or search.lower() in p.get("description", "").lower()
        ]

    # ── Discover dialog ──────────────────────────────────────────────
    if st.session_state.get("show_discover"):
        with st.expander("Discover Plugins from URLs", expanded=True):
            urls = st.text_area(
                "Plugin URLs (one per line)",
                placeholder="http://pysandbox.internal:8080\nhttp://pygate.internal:8443",
                height=100,
            )
            dc = st.columns(2)
            with dc[0]:
                if st.button("Discover", type="primary", use_container_width=True):
                    st.success(f"Discovery started for {len(urls.strip().splitlines())} URLs")
                    st.session_state.pop("show_discover", None)
            with dc[1]:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.pop("show_discover", None)
                    st.rerun()

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # ── Plugin cards ─────────────────────────────────────────────────
    if not plugins:
        st.markdown(
            """
            <div class="empty-state">
                <div class="icon">🔌</div>
                <p>No plugins registered. Use "Discover Plugins" to find and register external components.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for plugin in plugins:
        name = plugin.get("name", "")
        display = plugin.get("display_name", name)
        version = plugin.get("version", "0.0.0")
        desc = plugin.get("description", "")
        base_url = plugin.get("base_url", "")
        team = plugin.get("team", "")
        categories = plugin.get("categories", [])
        tools = plugin.get("tools", [])
        events = plugin.get("events", {})
        icon = PLUGIN_ICONS.get(name, "🔌")

        cat_tags = "".join(f'<span class="svc-tag">{c}</span>' for c in categories)
        tool_names = [t.get("name", t) if isinstance(t, dict) else t for t in tools]

        with st.container():
            st.markdown(
                f"""
                <div class="plugin-card">
                    <div class="plugin-header">
                        <span class="plugin-icon">{icon}</span>
                        <span class="plugin-title">{display}</span>
                        <span class="plugin-version">v{version}</span>
                    </div>
                    <p style="color:#999; font-size:0.85rem; margin:0 0 0.5rem 0">{desc}</p>
                    <div style="margin-bottom:0.5rem">{cat_tags}</div>
                    <div style="font-size:0.75rem; color:#666">
                        <strong>Team:</strong> {team or '—'} &nbsp;|&nbsp;
                        <strong>URL:</strong> <code>{base_url}</code> &nbsp;|&nbsp;
                        <strong>Tools:</strong> {len(tools)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Expandable details
            with st.expander(f"Details — {display}"):
                tab_tools, tab_events, tab_config = st.tabs(["Tools", "Events", "Configuration"])

                with tab_tools:
                    if tool_names:
                        for tname in tool_names:
                            st.markdown(f"- `{tname}`")
                    else:
                        st.info("No tools exposed")

                with tab_events:
                    publishes = events.get("publishes", [])
                    subscribes = events.get("subscribes", [])

                    ec = st.columns(2)
                    with ec[0]:
                        st.markdown("**Publishes**")
                        if publishes:
                            for e in publishes:
                                st.markdown(f"- 📤 `{e}`")
                        else:
                            st.caption("None")
                    with ec[1]:
                        st.markdown("**Subscribes**")
                        if subscribes:
                            for e in subscribes:
                                st.markdown(f"- 📥 `{e}`")
                        else:
                            st.caption("None")

                    if events.get("callback_url"):
                        st.markdown(f"**Callback URL:** `{events['callback_url']}`")

                with tab_config:
                    st.markdown(f"**Base URL:** `{base_url}`")
                    st.markdown(f"**Version:** {version}")
                    st.markdown(f"**Team:** {team or '—'}")

                    # Unregister button
                    if st.button(f"Unregister {display}", key=f"unreg_{name}", type="primary"):
                        st.warning(f"Plugin **{display}** would be unregistered.")

        st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    # ── Register new plugin ──────────────────────────────────────────
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    with st.expander("Register Plugin Manually"):
        rc = st.columns(2)
        with rc[0]:
            reg_name = st.text_input("Plugin Name", placeholder="myplugin")
            reg_version = st.text_input("Version", placeholder="1.0.0")
            reg_url = st.text_input("Base URL", placeholder="http://myplugin:8080")
        with rc[1]:
            reg_display = st.text_input("Display Name", placeholder="My Plugin")
            reg_desc = st.text_area("Description", placeholder="What does this plugin do?")
            reg_team = st.text_input("Team", placeholder="platform-team")

        if st.button("Register Plugin", type="primary"):
            if reg_name and reg_url:
                st.success(f"Plugin **{reg_display or reg_name}** registered!")
            else:
                st.error("Name and Base URL are required")
