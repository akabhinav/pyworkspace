"""
PyWorkspace — Enterprise Environment-as-a-Service Platform
Streamlit UI inspired by Databricks workspace design.
"""

from __future__ import annotations

import streamlit as st

# Must be the first Streamlit call
st.set_page_config(
    page_title="PyWorkspace",
    page_icon="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>⚡</text></svg>",
    layout="wide",
    initial_sidebar_state="expanded",
)

from api_client import PyWorkspaceClient  # noqa: E402
from pages import catalog, dashboard, plugins, settings, templates, workspaces  # noqa: E402

# ── Initialize session state ────────────────────────────────────────

if "client" not in st.session_state:
    st.session_state.client = PyWorkspaceClient()
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"

# ── Custom CSS: Databricks-inspired dark theme ──────────────────────

st.markdown(
    """
<style>
/* ── Global ─────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Hide default Streamlit top bar and footer */
header[data-testid="stHeader"] {
    background: #1B1B1B !important;
    border-bottom: 1px solid #333 !important;
}
footer { display: none !important; }
#MainMenu { visibility: hidden; }

/* Main content area */
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

/* ── Sidebar ────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: #111111 !important;
    border-right: 1px solid #2A2A2A;
    width: 260px !important;
}
section[data-testid="stSidebar"] .block-container {
    padding-top: 1rem;
}

/* Sidebar brand */
.sidebar-brand {
    padding: 0.75rem 1rem 1.5rem 1rem;
    border-bottom: 1px solid #2A2A2A;
    margin-bottom: 1rem;
}
.sidebar-brand h1 {
    font-size: 1.3rem;
    font-weight: 700;
    color: #FF3621;
    margin: 0;
    letter-spacing: -0.02em;
}
.sidebar-brand p {
    font-size: 0.72rem;
    color: #888;
    margin: 0.15rem 0 0 0;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* Nav buttons in sidebar */
div[data-testid="stSidebar"] button[kind="secondary"],
div[data-testid="stSidebar"] .stButton > button {
    width: 100% !important;
    text-align: left !important;
    justify-content: flex-start !important;
    background: transparent !important;
    border: none !important;
    color: #CCC !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    padding: 0.55rem 1rem !important;
    border-radius: 6px !important;
    margin: 1px 0 !important;
    transition: all 0.15s ease !important;
}
div[data-testid="stSidebar"] button[kind="secondary"]:hover,
div[data-testid="stSidebar"] .stButton > button:hover {
    background: #2A2A2A !important;
    color: #FFF !important;
}

/* Active nav item */
.nav-active button {
    background: #FF362115 !important;
    color: #FF3621 !important;
    border-left: 3px solid #FF3621 !important;
}

/* ── Cards ──────────────────────────────────────── */
.metric-card {
    background: #242424;
    border: 1px solid #333;
    border-radius: 10px;
    padding: 1.25rem;
    transition: all 0.2s ease;
}
.metric-card:hover {
    border-color: #FF3621;
    box-shadow: 0 0 20px rgba(255, 54, 33, 0.08);
}
.metric-card .metric-value {
    font-size: 2rem;
    font-weight: 700;
    color: #FFF;
    line-height: 1.1;
}
.metric-card .metric-label {
    font-size: 0.78rem;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-top: 0.35rem;
}
.metric-card .metric-delta {
    font-size: 0.78rem;
    margin-top: 0.25rem;
}
.metric-delta.up { color: #00C853; }
.metric-delta.down { color: #FF5252; }

/* ── Status badges ──────────────────────────────── */
.status-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.status-running { background: #00C85320; color: #00C853; border: 1px solid #00C85340; }
.status-paused { background: #FFC10720; color: #FFC107; border: 1px solid #FFC10740; }
.status-provisioning { background: #2979FF20; color: #2979FF; border: 1px solid #2979FF40; }
.status-error { background: #FF525220; color: #FF5252; border: 1px solid #FF525240; }
.status-destroying { background: #FF525220; color: #FF5252; border: 1px solid #FF525240; }
.status-destroyed { background: #66666620; color: #999; border: 1px solid #66666640; }

/* ── Tier badges ────────────────────────────────── */
.tier-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.68rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.tier-dev { background: #66666630; color: #AAA; }
.tier-standard { background: #2979FF25; color: #64B5F6; }
.tier-enterprise { background: #FF362120; color: #FF6E40; }

/* ── Service/catalog cards ──────────────────────── */
.service-card {
    background: #242424;
    border: 1px solid #333;
    border-radius: 10px;
    padding: 1.2rem;
    height: 100%;
    transition: all 0.2s ease;
    cursor: default;
}
.service-card:hover {
    border-color: #555;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}
.service-card .svc-icon {
    font-size: 1.8rem;
    margin-bottom: 0.6rem;
}
.service-card h4 {
    margin: 0 0 0.3rem 0;
    font-size: 0.95rem;
    font-weight: 600;
    color: #FFF;
}
.service-card p {
    margin: 0;
    font-size: 0.78rem;
    color: #999;
    line-height: 1.4;
}
.service-card .svc-meta {
    margin-top: 0.7rem;
    font-size: 0.7rem;
    color: #666;
}
.svc-tag {
    display: inline-block;
    background: #333;
    color: #AAA;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 0.65rem;
    margin-right: 4px;
    margin-top: 4px;
}

/* ── Template gallery cards ─────────────────────── */
.template-card {
    background: #242424;
    border: 1px solid #333;
    border-radius: 10px;
    padding: 1.4rem;
    transition: all 0.2s ease;
    cursor: pointer;
    height: 100%;
}
.template-card:hover {
    border-color: #FF3621;
    box-shadow: 0 0 15px rgba(255, 54, 33, 0.1);
}
.template-card h4 {
    margin: 0 0 0.4rem 0;
    font-size: 1rem;
    font-weight: 600;
    color: #FFF;
}
.template-card p {
    margin: 0 0 0.6rem 0;
    font-size: 0.8rem;
    color: #999;
    line-height: 1.4;
}
.template-usage {
    font-size: 0.72rem;
    color: #666;
}

/* ── Data tables ────────────────────────────────── */
.workspace-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
}
.workspace-table th {
    text-align: left;
    padding: 0.65rem 1rem;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #888;
    border-bottom: 1px solid #333;
    background: #1E1E1E;
}
.workspace-table th:first-child { border-radius: 8px 0 0 0; }
.workspace-table th:last-child { border-radius: 0 8px 0 0; }
.workspace-table td {
    padding: 0.75rem 1rem;
    font-size: 0.85rem;
    color: #DDD;
    border-bottom: 1px solid #2A2A2A;
    vertical-align: middle;
}
.workspace-table tr:hover td {
    background: #2A2A2A;
}
.ws-name {
    font-weight: 600;
    color: #FFF;
}
.ws-name a {
    color: #64B5F6;
    text-decoration: none;
}
.ws-name a:hover {
    text-decoration: underline;
}

/* ── Plugin cards ───────────────────────────────── */
.plugin-card {
    background: #242424;
    border: 1px solid #333;
    border-radius: 10px;
    padding: 1.4rem;
    transition: all 0.2s ease;
}
.plugin-card:hover {
    border-color: #555;
}
.plugin-header {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    margin-bottom: 0.6rem;
}
.plugin-icon {
    font-size: 1.6rem;
}
.plugin-title {
    font-size: 1rem;
    font-weight: 600;
    color: #FFF;
    margin: 0;
}
.plugin-version {
    font-size: 0.7rem;
    color: #888;
    background: #333;
    padding: 2px 6px;
    border-radius: 4px;
}

/* ── Page headers ───────────────────────────────── */
.page-header {
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #2A2A2A;
}
.page-header h1 {
    font-size: 1.6rem;
    font-weight: 700;
    color: #FFF;
    margin: 0 0 0.3rem 0;
    letter-spacing: -0.02em;
}
.page-header p {
    font-size: 0.85rem;
    color: #888;
    margin: 0;
}

/* ── Streamlit overrides ────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    border-bottom: 1px solid #333;
}
.stTabs [data-baseweb="tab"] {
    padding: 0.6rem 1.2rem;
    font-size: 0.85rem;
    font-weight: 500;
    color: #888;
    border-bottom: 2px solid transparent;
}
.stTabs [aria-selected="true"] {
    color: #FF3621 !important;
    border-bottom-color: #FF3621 !important;
    background: transparent !important;
}

/* Expander styling */
.streamlit-expanderHeader {
    font-size: 0.9rem;
    font-weight: 600;
    color: #DDD;
}

/* Button styling */
.stButton > button {
    border-radius: 6px;
    font-weight: 500;
    font-size: 0.82rem;
    transition: all 0.15s ease;
}
button[kind="primary"] {
    background: #FF3621 !important;
    border: none !important;
    color: #FFF !important;
}
button[kind="primary"]:hover {
    background: #E02E1A !important;
    box-shadow: 0 2px 8px rgba(255, 54, 33, 0.3) !important;
}

/* selectbox / input styling */
.stSelectbox > div > div,
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    background: #2D2D2D !important;
    border: 1px solid #444 !important;
    border-radius: 6px !important;
    color: #FFF !important;
}

/* Dataframe styling */
.stDataFrame {
    border: 1px solid #333;
    border-radius: 8px;
    overflow: hidden;
}

/* ── Scrollbar ──────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #1B1B1B; }
::-webkit-scrollbar-thumb { background: #444; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #555; }

/* ── Misc ───────────────────────────────────────── */
.separator {
    border-top: 1px solid #2A2A2A;
    margin: 1rem 0;
}
.empty-state {
    text-align: center;
    padding: 3rem 1rem;
    color: #666;
}
.empty-state .icon { font-size: 2.5rem; margin-bottom: 0.5rem; }
.empty-state p { font-size: 0.9rem; }
</style>
""",
    unsafe_allow_html=True,
)

# ── Navigation icons mapping ────────────────────────────────────────

NAV_ITEMS = {
    "Dashboard": "grid-3x3-gap-fill",
    "Workspaces": "hdd-stack-fill",
    "Catalog": "collection-fill",
    "Templates": "file-earmark-code-fill",
    "Plugins": "puzzle-fill",
    "Settings": "gear-fill",
}

# ── Sidebar ─────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <h1>⚡ PyWorkspace</h1>
            <p>Environment-as-a-Service</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Backend status
    health = st.session_state.client.health()
    if health.get("status") == "healthy":
        st.success("API Connected", icon="🟢")
    else:
        st.warning("Demo Mode (API offline)", icon="🟡")

    st.markdown("---")

    # Navigation
    for page_name, icon in NAV_ITEMS.items():
        is_active = st.session_state.current_page == page_name
        if is_active:
            st.markdown('<div class="nav-active">', unsafe_allow_html=True)

        if st.button(f"  {page_name}", key=f"nav_{page_name}", use_container_width=True):
            st.session_state.current_page = page_name
            st.rerun()

        if is_active:
            st.markdown("</div>", unsafe_allow_html=True)

    # Bottom section
    st.markdown("---")
    st.markdown(
        """
        <div style="padding: 0.5rem 1rem; font-size: 0.72rem; color: #555;">
            <div style="margin-bottom: 0.3rem;">Org: <span style="color:#AAA">acme-corp</span></div>
            <div style="margin-bottom: 0.3rem;">User: <span style="color:#AAA">admin@acme.com</span></div>
            <div>v1.0.0</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Page routing ────────────────────────────────────────────────────

page = st.session_state.current_page
client = st.session_state.client

if page == "Dashboard":
    dashboard.render(client)
elif page == "Workspaces":
    workspaces.render(client)
elif page == "Catalog":
    catalog.render(client)
elif page == "Templates":
    templates.render(client)
elif page == "Plugins":
    plugins.render(client)
elif page == "Settings":
    settings.render(client)
