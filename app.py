"""
app.py — Main Entry Point for Fraud Detection System
Handles: Authentication UI, Session Management, Page Navigation.
Styled with Bonsai-inspired clean SaaS UI.
"""

import streamlit as st
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.auth import (
    init_database, login_user, register_user,
    check_session_timeout, log_activity, get_user_settings
)

# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Fraud Detection System",
    page_icon=" ",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------------------------
# Initialize Database
# ---------------------------------------------------------------------------
init_database()

# ---------------------------------------------------------------------------
# Bonsai-Inspired CSS — Clean Light Theme
# ---------------------------------------------------------------------------
def inject_bonsai_css():
    st.markdown("""
    <style>
        /* ===== Google Font ===== */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        /* ===== Global ===== */
        html, body, [class*="css"] {
            font-family: 'Inter', system-ui, sans-serif;
        }

        /* ===== Light Background ===== */
        .stApp {
            background-color: #F7F7F5;
        }

        /* ===== Hide Streamlit defaults (keep sidebar toggle visible) ===== */
        #MainMenu {display: none !important;}
        footer {display: none !important;}
        [data-testid="stToolbar"] {display: none !important;}
        [data-testid="stDecoration"] {display: none !important;}
        [data-testid="stStatusWidget"] {display: none !important;}

        /* Header: minimal but visible for sidebar toggle */
        header[data-testid="stHeader"] {
            background: transparent !important;
            border: none !important;
            height: 2.5rem !important;
            min-height: 2.5rem !important;
        }

        /* Reduce default top padding on main content */
        .stMainBlockContainer,
        [data-testid="stAppViewBlockContainer"] {
            padding-top: 1rem !important;
        }

        /* ===== Sidebar — Bonsai Collapsible ===== */
        [data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            border-right: 1px solid #E5E5E5 !important;
            transition: margin-left 0.3s ease, transform 0.3s ease !important;
        }

        [data-testid="stSidebar"][aria-expanded="true"] {
            min-width: 260px !important;
            width: 260px !important;
        }

        /* Hide Streamlit's native toggle buttons - we use custom JS button */
        [data-testid="collapsedControl"],
        [data-testid="stSidebarCollapseButton"] {
            display: none !important;
        }

        /* Custom toggle button (injected via JS) */
        #bonsai-sidebar-toggle {
            position: fixed !important;
            left: 12px !important;
            top: 12px !important;
            z-index: 999999 !important;
            background: #FFFFFF !important;
            border: 1px solid #E5E5E5 !important;
            border-radius: 8px !important;
            width: 40px !important;
            height: 40px !important;
            cursor: pointer !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
            font-size: 18px !important;
            color: #333 !important;
            transition: all 0.2s ease !important;
        }

        #bonsai-sidebar-toggle:hover {
            background: #F0F0F0 !important;
            box-shadow: 0 2px 12px rgba(0,0,0,0.15) !important;
        }

        [data-testid="stSidebar"] [data-testid="stMarkdown"] {
            color: #111111;
        }

        /* ===== Sidebar Nav Links ===== */
        [data-testid="stSidebar"] .stRadio > div {
            gap: 2px !important;
        }

        [data-testid="stSidebar"] .stRadio > div > label {
            background: transparent !important;
            border-radius: 8px !important;
            padding: 10px 16px !important;
            color: #6B6B6B !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
            border: none !important;
        }

        [data-testid="stSidebar"] .stRadio > div > label:hover {
            background: #F7F7F5 !important;
            color: #111111 !important;
        }

        [data-testid="stSidebar"] .stRadio > div > label[data-checked="true"],
        [data-testid="stSidebar"] .stRadio > div > label[aria-checked="true"] {
            background: #F0FDF4 !important;
            color: #16A34A !important;
            font-weight: 600 !important;
        }

        /* Hide radio circles in sidebar */
        [data-testid="stSidebar"] .stRadio > div > label > div:first-child {
            display: none !important;
        }

        /* ===== Input Styling (aggressive override) ===== */
        input, .stTextInput input, [data-testid="stTextInput"] input {
            background-color: #FAFAFA !important;
            border: 1px solid #E5E5E5 !important;
            border-radius: 8px !important;
            color: #111111 !important;
            padding: 12px 16px !important;
            font-size: 14px !important;
            transition: border-color 0.2s ease !important;
            -webkit-text-fill-color: #111111 !important;
        }

        input::placeholder {
            color: #9CA3AF !important;
            opacity: 1 !important;
            -webkit-text-fill-color: #9CA3AF !important;
        }

        input:focus {
            border-color: #16A34A !important;
            box-shadow: 0 0 0 2px rgba(22, 163, 74, 0.1) !important;
            background-color: #FFFFFF !important;
            caret-color: #111111 !important;
        }

        .stSelectbox > div > div, [data-testid="stSelectbox"] > div > div {
            background-color: #FAFAFA !important;
            border: 1px solid #E5E5E5 !important;
            border-radius: 8px !important;
            color: #111111 !important;
        }

        /* Remove searchable input from selectbox — make it a simple dropdown */
        [data-baseweb="select"] input {
            caret-color: transparent !important;
            color: transparent !important;
            width: 1px !important;
            min-width: 1px !important;
            padding: 0 !important;
            cursor: pointer !important;
        }

        [data-baseweb="select"],
        [data-baseweb="select"] * {
            cursor: pointer !important;
        }

        /* ===== Label styling ===== */
        label, .stTextInput > label, .stSelectbox > label {
            color: #111111 !important;
            font-size: 14px !important;
            font-weight: 500 !important;
        }

        /* ===== ALL Buttons (Green) ===== */
        .stButton > button,
        .stFormSubmitButton > button,
        [data-testid="stFormSubmitButton"] > button,
        button[kind="primaryFormSubmit"],
        button[kind="primary"] {
            width: 100%;
            background-color: #16A34A !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 12px 24px !important;
            font-size: 15px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease !important;
            -webkit-text-fill-color: white !important;
        }

        .stButton > button:hover,
        .stFormSubmitButton > button:hover,
        [data-testid="stFormSubmitButton"] > button:hover {
            background-color: #15803D !important;
            transform: translateY(-1px) !important;
            color: white !important;
        }

        .stButton > button:focus,
        .stFormSubmitButton > button:focus {
            background-color: #16A34A !important;
            color: white !important;
            box-shadow: none !important;
        }

        /* ===== Tabs Styling ===== */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0px;
            background-color: #F7F7F5 !important;
            border-radius: 10px;
            padding: 4px;
            border: 1px solid #E5E5E5;
            justify-content: center;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 8px !important;
            color: #6B6B6B !important;
            font-weight: 500 !important;
            padding: 10px 24px !important;
            font-size: 14px !important;
            background-color: transparent !important;
        }

        .stTabs [data-baseweb="tab"]:hover {
            color: #111111 !important;
            background-color: #FFFFFF !important;
        }

        .stTabs [aria-selected="true"] {
            background-color: #16A34A !important;
            color: white !important;
            font-weight: 600 !important;
            -webkit-text-fill-color: white !important;
        }

        .stTabs [aria-selected="true"]:hover {
            background-color: #15803D !important;
            color: white !important;
            -webkit-text-fill-color: white !important;
        }

        /* Tab bottom indicator — hide it */
        .stTabs [data-baseweb="tab-highlight"],
        .stTabs [data-baseweb="tab-border"] {
            display: none !important;
        }

        /* ===== Hide 'Press Enter to submit' ===== */
        [data-testid="stForm"] small,
        [data-testid="InputInstructions"],
        .st-emotion-cache-1n76uvr {
            display: none !important;
        }

        /* ===== Metric cards override ===== */
        [data-testid="stMetric"] {
            background: #FFFFFF;
            border: 1px solid #E5E5E5;
            border-radius: 12px;
            padding: 16px 20px;
        }
    </style>
    """, unsafe_allow_html=True)



# ---------------------------------------------------------------------------
# Sidebar Toggle (only for authenticated pages)
# ---------------------------------------------------------------------------
def inject_sidebar_toggle():
    import streamlit.components.v1 as components
    components.html("""
    <script>
    (function() {
        var parent = window.parent.document;
        if (parent.getElementById('bonsai-sidebar-toggle')) return;

        function createToggle() {
            var btn = parent.createElement('div');
            btn.id = 'bonsai-sidebar-toggle';
            btn.innerHTML = '&#9776;';
            btn.title = 'Toggle sidebar';
            parent.body.appendChild(btn);

            var appView = parent.querySelector('[data-testid="stAppViewContainer"]');
            if (appView) appView.style.transition = 'margin-left 0.3s ease';
            var mainBlock = parent.querySelector('.main');
            if (mainBlock) mainBlock.style.transition = 'margin-left 0.3s ease';

            btn.addEventListener('click', function() {
                var sidebar = parent.querySelector('[data-testid="stSidebar"]');
                if (!sidebar) return;

                var expanded = sidebar.getAttribute('aria-expanded');
                if (expanded === 'true') {
                    sidebar.setAttribute('aria-expanded', 'false');
                    sidebar.style.marginLeft = '-260px';
                    sidebar.style.transform = 'translateX(-260px)';
                    sidebar.style.width = '260px';
                    sidebar.style.minWidth = '260px';
                    btn.innerHTML = '&#9776;';
                    if (appView) appView.style.marginLeft = '0px';
                    if (mainBlock) mainBlock.style.marginLeft = '0px';
                } else {
                    sidebar.setAttribute('aria-expanded', 'true');
                    sidebar.style.marginLeft = '0px';
                    sidebar.style.transform = 'translateX(0)';
                    sidebar.style.width = '260px';
                    sidebar.style.minWidth = '260px';
                    btn.innerHTML = '&#10005;';
                    if (appView) appView.style.marginLeft = '';
                    if (mainBlock) mainBlock.style.marginLeft = '';
                }
            });

            var sidebar = parent.querySelector('[data-testid="stSidebar"]');
            if (sidebar && sidebar.getAttribute('aria-expanded') === 'true') {
                btn.innerHTML = '&#10005;';
            }
        }

        setTimeout(createToggle, 800);
    })();
    </script>
    """, height=0)


# ---------------------------------------------------------------------------
# Session State
# ---------------------------------------------------------------------------
def init_session_state():
    defaults = {
        "authenticated": False,
        "user": None,
        "last_activity": None,
        "current_page": "Dashboard",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ---------------------------------------------------------------------------
# Auth Screen — Bonsai Style
# ---------------------------------------------------------------------------
def render_auth_screen():
    # Center the auth card
    col_left, col_center, col_right = st.columns([1, 1.2, 1])

    with col_center:
        # Brand
        st.markdown("""
        <div style="text-align: center; margin-top: 60px; margin-bottom: 32px;">
            <div style="font-size: 28px; font-weight: 700; color: #111111; letter-spacing: -0.5px;">
                Fraud Detection
            </div>
            <div style="font-size: 13px; color: #6B6B6B; margin-top: 4px; letter-spacing: 1px; text-transform: uppercase;">
                In Financial Transactions Using Machine Learning
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Spacer
        st.markdown("<div style='height: 4px'></div>", unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["Sign In", "Create Account"])

        with tab_login:
            st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)
            with st.form("login_form", clear_on_submit=False):
                login_user_input = st.text_input(
                    "Username", placeholder="Enter your username", key="login_username"
                )
                login_pass_input = st.text_input(
                    "Password", placeholder="Enter your password",
                    type="password", key="login_password"
                )
                st.markdown("<div style='height: 4px'></div>", unsafe_allow_html=True)
                login_submitted = st.form_submit_button("Sign In", use_container_width=True)

            if login_submitted:
                result = login_user(login_user_input, login_pass_input)
                if result["success"]:
                    st.session_state["authenticated"] = True
                    st.session_state["user"] = result["user"]
                    st.session_state["last_activity"] = datetime.now()
                    log_activity(result["user"]["id"], "Login")
                    st.rerun()
                else:
                    st.markdown(
                        f'<div style="background: #FEF2F2; border: 1px solid #FECACA; border-radius: 8px; '
                        f'padding: 12px 16px; color: #DC2626; font-size: 13px; font-weight: 500; '
                        f'text-align: center; margin-top: 8px;">⚠️ {result["message"]}</div>',
                        unsafe_allow_html=True
                    )

        with tab_register:
            st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)
            with st.form("register_form", clear_on_submit=False):
                reg_name = st.text_input(
                    "Full Name", placeholder="Enter your full name", key="reg_name"
                )
                reg_user = st.text_input(
                    "Username", placeholder="Choose a username", key="reg_username"
                )
                reg_pass = st.text_input(
                    "Password", placeholder="Min 6 characters",
                    type="password", key="reg_password"
                )
                st.markdown("<div style='height: 4px'></div>", unsafe_allow_html=True)
                reg_submitted = st.form_submit_button("Create Account", use_container_width=True)

            if reg_submitted:
                # Default all new open registrations to 'Analyst'
                result = register_user(reg_name, reg_user, reg_pass, "Analyst")
                if result["success"]:
                    st.markdown(
                        f'<div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; '
                        f'padding: 12px 16px; color: #16A34A; font-size: 13px; font-weight: 500; '
                        f'text-align: center; margin-top: 8px;">{result["message"]} You can now sign in.</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f'<div style="background: #FEF2F2; border: 1px solid #FECACA; border-radius: 8px; '
                        f'padding: 12px 16px; color: #DC2626; font-size: 13px; font-weight: 500; '
                        f'text-align: center; margin-top: 8px;">{result["message"]}</div>',
                        unsafe_allow_html=True
                    )

        st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar — Bonsai Minimal
# ---------------------------------------------------------------------------
def render_sidebar():
    user = st.session_state["user"]
    settings = get_user_settings(user["id"])

    with st.sidebar:
        # Brand
        st.markdown("""
        <div style="text-align: center; padding: 16px 0 12px;">
            <div style="font-size: 18px; font-weight: 700; color: #111111;">
                Fraud Detection
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Divider
        st.markdown('<div style="height: 1px; background: #E5E5E5; margin: 8px 0 16px;"></div>',
                    unsafe_allow_html=True)

        # User info card
        st.markdown(f"""
        <div style="padding: 12px 16px; background: #F7F7F5; border-radius: 8px;
                    border: 1px solid #E5E5E5; margin-bottom: 16px;">
            <div style="font-size: 14px; font-weight: 600; color: #111111;">
                {user['full_name']}
            </div>
            <div style="font-size: 12px; color: #6B6B6B; margin-top: 2px;">
                {user['role']} · @{user['username']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Navigation
        pages = [
            "Dashboard",
            "Dataset",
            "Models",
            "Predictor",
            "Profile",
            "Settings",
            "Reports"
        ]

        st.markdown('<div style="height: 1px; background: #E5E5E5; margin: 8px 0 12px;"></div>',
                    unsafe_allow_html=True)

        st.markdown("""
        <div style="font-size: 11px; font-weight: 600; color: #9CA3AF; text-transform: uppercase;
                    letter-spacing: 1px; padding: 0 16px; margin-bottom: 8px;">Navigation</div>
        """, unsafe_allow_html=True)

        selected = st.radio(
            "nav",
            pages,
            index=pages.index(st.session_state['current_page']) if st.session_state['current_page'] in pages else 0,
            label_visibility="collapsed",
            key="nav_radio"
        )

        st.session_state["current_page"] = selected

        # Quick stats
        st.markdown('<div style="height: 1px; background: #E5E5E5; margin: 16px 0 12px;"></div>',
                    unsafe_allow_html=True)

        st.markdown(f"""
        <div style="padding: 10px 16px; background: #F7F7F5; border-radius: 8px;
                    border: 1px solid #E5E5E5; font-size: 12px; color: #6B6B6B;">
            Model: <span style="color: #16A34A; font-weight: 600;">{settings['active_model']}</span><br>
            Threshold: <span style="color: #16A34A; font-weight: 600;">{settings['default_threshold']}</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)

        # Logout
        if st.button("Logout", use_container_width=True, key="logout_btn"):
            log_activity(user["id"], "Logout")
            st.session_state["authenticated"] = False
            st.session_state["user"] = None
            st.session_state["last_activity"] = None
            st.rerun()


# ---------------------------------------------------------------------------
# Dashboard — Full Data-Driven Page
# ---------------------------------------------------------------------------
def render_dashboard():
    import json
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go

    user = st.session_state["user"]
    st.session_state["last_activity"] = datetime.now()

    # --- Header ---
    st.markdown(f"""
    <div style="padding: 8px 0 20px;">
        <h1 style="font-size: 28px; font-weight: 700; color: #111111; margin-bottom: 4px;">
            Dashboard
        </h1>
        <p style="font-size: 14px; color: #6B6B6B; margin-top: 0;">
            Welcome back, {user['full_name']}. Here's your system overview.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # --- Load data ---
    DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "sample_data.csv")
    METRICS_PATH = os.path.join(os.path.dirname(__file__), "models", "model_metrics.json")

    has_data = os.path.exists(DATA_PATH)
    has_metrics = os.path.exists(METRICS_PATH)

    df = None
    metrics = None

    if has_data:
        df = pd.read_csv(DATA_PATH)
    if has_metrics:
        with open(METRICS_PATH, "r") as f:
            metrics = json.load(f)

    # --- KPI Cards ---
    card_template = """
    <div style="background: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 12px;
                padding: 16px 18px; height: 120px;">
        <div style="font-size: 10px; color: #6B6B6B; text-transform: uppercase;
                    letter-spacing: 0.8px; font-weight: 600; white-space: nowrap;">{label}</div>
        <div style="font-size: 24px; font-weight: 700; color: {color}; margin-top: 6px;
                    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{value}</div>
        <div style="font-size: 11px; color: #9CA3AF; margin-top: 4px; white-space: nowrap;">{sub}</div>
    </div>
    """

    if df is not None and metrics is not None:
        total_txn = len(df)
        fraud_count = int(df["Class"].sum())
        legit_count = total_txn - fraud_count
        fraud_rate = (fraud_count / total_txn * 100) if total_txn > 0 else 0
        avg_amount = df["Amount"].mean()

        # Get best model metrics (values already stored as percentages)
        best_model = metrics.get("_metadata", {}).get("best_model", "Random Forest")
        best_metrics = metrics.get(best_model, {})
        accuracy = best_metrics.get("accuracy", 0)
        f1 = best_metrics.get("f1_score", 0)

        col1, col2, col3, col4, col5, col6 = st.columns(6)

        with col1:
            st.markdown(card_template.format(
                label="Total Transactions", value=f"{total_txn:,}",
                color="#111111", sub="In dataset"), unsafe_allow_html=True)
        with col2:
            st.markdown(card_template.format(
                label="Fraud Detected", value=f"{fraud_count}",
                color="#DC2626", sub=f"{fraud_rate:.1f}% of total"), unsafe_allow_html=True)
        with col3:
            st.markdown(card_template.format(
                label="Legitimate", value=f"{legit_count:,}",
                color="#16A34A", sub=f"{100 - fraud_rate:.1f}% of total"), unsafe_allow_html=True)
        with col4:
            st.markdown(card_template.format(
                label="Model Accuracy", value=f"{accuracy:.1f}%",
                color="#16A34A", sub=f"Best: {best_model}"), unsafe_allow_html=True)
        with col5:
            st.markdown(card_template.format(
                label="Avg Amount", value=f"${avg_amount:.2f}",
                color="#2563EB", sub="Per transaction"), unsafe_allow_html=True)
        with col6:
            st.markdown(card_template.format(
                label="F1 Score", value=f"{f1:.1f}%",
                color="#F59E0B", sub=f"{best_model}"), unsafe_allow_html=True)
    else:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(card_template.format(label="Transactions", value="--", color="#111111", sub="No data loaded"), unsafe_allow_html=True)
        with col2:
            st.markdown(card_template.format(label="Fraud Blocked", value="--", color="#DC2626", sub="Awaiting analysis"), unsafe_allow_html=True)
        with col3:
            st.markdown(card_template.format(label="Accuracy", value="--", color="#16A34A", sub="Train model first"), unsafe_allow_html=True)
        with col4:
            st.markdown(card_template.format(label="F1 Score", value="--", color="#F59E0B", sub="No data yet"), unsafe_allow_html=True)

    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)

    # --- Charts Section ---
    if df is not None:
        chart_col1, chart_col2 = st.columns([2, 1])

        with chart_col1:
            st.markdown("""
            <div style="background: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 12px; padding: 20px;">
                <div style="font-size: 16px; font-weight: 600; color: #111111; margin-bottom: 4px;">
                    Transaction Volume Over Time
                </div>
                <div style="font-size: 12px; color: #6B6B6B; margin-bottom: 12px;">
                    Distribution of transactions across time periods
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Create time bins
            df_chart = df.copy()
            df_chart["Time_Hour"] = (df_chart["Time"] / 3600).astype(int)
            time_dist = df_chart.groupby(["Time_Hour", "Class"]).size().reset_index(name="Count")
            time_dist["Label"] = time_dist["Class"].map({0: "Legitimate", 1: "Fraud"})

            fig_line = px.area(
                time_dist, x="Time_Hour", y="Count", color="Label",
                color_discrete_map={"Legitimate": "rgba(22,163,74,0.5)", "Fraud": "rgba(220,38,38,0.5)"},
                labels={"Time_Hour": "Hour", "Count": "Transactions"}
            )
            fig_line.update_layout(
                plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
                font=dict(family="Inter, sans-serif", color="#6B6B6B", size=12),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=40, r=10, t=10, b=40),
                height=300,
                xaxis=dict(gridcolor="#F5F5F5", title="Hour", showline=False),
                yaxis=dict(gridcolor="#F5F5F5", title="Count", showline=False)
            )
            st.plotly_chart(fig_line, use_container_width=True, config={'displayModeBar': False})

        with chart_col2:
            st.markdown("""
            <div style="background: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 12px; padding: 20px;">
                <div style="font-size: 16px; font-weight: 600; color: #111111; margin-bottom: 4px;">
                    Fraud Distribution
                </div>
                <div style="font-size: 12px; color: #6B6B6B; margin-bottom: 12px;">
                    Class imbalance overview
                </div>
            </div>
            """, unsafe_allow_html=True)

            fraud_counts = df["Class"].value_counts().reset_index()
            fraud_counts.columns = ["Class", "Count"]
            fraud_counts["Label"] = fraud_counts["Class"].map({0: "Legitimate", 1: "Fraud"})

            fig_donut = px.pie(
                fraud_counts, values="Count", names="Label",
                color="Label",
                color_discrete_map={"Legitimate": "#22C55E", "Fraud": "#EF4444"},
                hole=0.6
            )
            fig_donut.update_traces(textposition="outside", textinfo="label+percent",
                                     marker=dict(line=dict(color='#FFFFFF', width=2)))
            fig_donut.update_layout(
                plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
                font=dict(family="Inter, sans-serif", color="#6B6B6B", size=12),
                showlegend=False,
                margin=dict(l=10, r=10, t=10, b=10),
                height=300
            )
            st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})

        st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)

        # --- Hourly Fraud Bar Chart ---
        st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 12px; padding: 20px;">
            <div style="font-size: 16px; font-weight: 600; color: #111111; margin-bottom: 4px;">
                Fraud vs Legitimate by Hour
            </div>
            <div style="font-size: 12px; color: #6B6B6B; margin-bottom: 12px;">
                Hourly comparison of transaction types
            </div>
        </div>
        """, unsafe_allow_html=True)

        hourly = df_chart.groupby(["Time_Hour", "Class"]).size().reset_index(name="Count")
        hourly["Label"] = hourly["Class"].map({0: "Legitimate", 1: "Fraud"})

        fig_bar = px.bar(
            hourly, x="Time_Hour", y="Count", color="Label",
            barmode="group",
            color_discrete_map={"Legitimate": "rgba(22,163,74,0.7)", "Fraud": "rgba(220,38,38,0.7)"},
            labels={"Time_Hour": "Hour", "Count": "Transactions"}
        )
        fig_bar.update_layout(
            plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
            font=dict(family="Inter, sans-serif", color="#6B6B6B", size=12),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=40, r=10, t=10, b=40),
            height=280,
            xaxis=dict(gridcolor="#F5F5F5", showline=False),
            yaxis=dict(gridcolor="#F5F5F5", showline=False),
            bargap=0.3
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

        st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)

        # --- Data Feed Table ---
        st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 12px; padding: 20px;">
            <div style="font-size: 16px; font-weight: 600; color: #111111; margin-bottom: 4px;">
                Transaction Feed
            </div>
            <div style="font-size: 12px; color: #6B6B6B; margin-bottom: 12px;">
                Recent transactions with fraud indicators
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Filters
        filter_col1, filter_col2, filter_col3 = st.columns([2, 1, 1])

        with filter_col1:
            search_term = st.text_input("Search by amount", placeholder="e.g. 150.00", key="dash_search")
        with filter_col2:
            class_filter = st.selectbox("Class", ["All", "Fraud", "Legitimate"], key="dash_class_filter")
        with filter_col3:
            n_rows = st.selectbox("Show rows", [25, 50, 100, 200], index=0, key="dash_n_rows")

        display_df = df[["Time", "Amount", "Class"]].copy()
        display_df["Status"] = display_df["Class"].map({0: "Legitimate", 1: "Fraud"})
        display_df["Time_Formatted"] = (display_df["Time"] / 3600).round(1).astype(str) + "h"
        display_df["Amount"] = display_df["Amount"].round(2)
        display_df = display_df[["Time_Formatted", "Amount", "Status"]]
        display_df.columns = ["Time", "Amount ($)", "Status"]

        if class_filter == "Fraud":
            display_df = display_df[display_df["Status"] == "Fraud"]
        elif class_filter == "Legitimate":
            display_df = display_df[display_df["Status"] == "Legitimate"]

        if search_term:
            try:
                amt = float(search_term)
                display_df = display_df[display_df["Amount ($)"].between(amt - 10, amt + 10)]
            except ValueError:
                pass

        st.dataframe(
            display_df.head(n_rows),
            use_container_width=True,
            height=400,
            column_config={
                "Time": st.column_config.TextColumn("Time", width="small"),
                "Amount ($)": st.column_config.NumberColumn("Amount ($)", format="$%.2f", width="medium"),
                "Status": st.column_config.TextColumn("Status", width="small")
            }
        )

        st.markdown(f"""
        <div style="font-size: 12px; color: #9CA3AF; margin-top: 8px; text-align: right;">
            Showing {min(n_rows, len(display_df))} of {len(display_df)} transactions
        </div>
        """, unsafe_allow_html=True)

    else:
        # No data state
        st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #E5E5E5;
                    border-radius: 12px; padding: 32px; text-align: center;">
            <div style="font-size: 18px; font-weight: 600; color: #111111; margin-bottom: 8px;">
                System Standing By
            </div>
            <div style="font-size: 14px; color: #6B6B6B; max-width: 460px; margin: 0 auto;">
                Navigate to <strong style="color: #16A34A;">Dataset</strong> to load your transaction data,
                or use the <strong style="color: #16A34A;">Predictor</strong> to test individual transactions.
            </div>
        </div>
        """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Dataset Page — Upload, Preview, EDA
# ---------------------------------------------------------------------------
def render_dataset():
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from src.data_engine import load_dataset, validate_dataset

    st.session_state["last_activity"] = datetime.now()

    st.markdown("""
    <div style="padding: 8px 0 20px;">
        <h1 style="font-size: 28px; font-weight: 700; color: #111111; margin-bottom: 4px;">Dataset</h1>
        <p style="font-size: 14px; color: #6B6B6B; margin-top: 0;">Upload, preview, and explore your transaction data.</p>
    </div>
    """, unsafe_allow_html=True)

    DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
    DATA_PATH = os.path.join(DATA_DIR, "sample_data.csv")
    os.makedirs(DATA_DIR, exist_ok=True)

    # --- Upload Section ---
    st.markdown("""
    <div style="background: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
        <div style="font-size: 16px; font-weight: 600; color: #111111; margin-bottom: 4px;">Upload Dataset</div>
        <div style="font-size: 12px; color: #6B6B6B; margin-bottom: 12px;">Upload a CSV file with columns: Time, V1-V28, Amount, Class</div>
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader("Choose a CSV file", type=["csv"], key="dataset_upload", label_visibility="collapsed")

    if uploaded is not None:
        df_uploaded = pd.read_csv(uploaded)
        df_uploaded.to_csv(DATA_PATH, index=False)
        st.markdown('<div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; padding: 10px 16px; color: #16A34A; font-size: 13px; font-weight: 500; margin-bottom: 16px;">Dataset uploaded and saved successfully.</div>', unsafe_allow_html=True)

    # --- Load data ---
    if not os.path.exists(DATA_PATH):
        st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 12px; padding: 48px; text-align: center;">
            <div style="font-size: 18px; font-weight: 600; color: #111111; margin-bottom: 8px;">No Dataset Loaded</div>
            <div style="font-size: 14px; color: #6B6B6B;">Upload a CSV file above to get started.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    df = pd.read_csv(DATA_PATH)
    report = validate_dataset(df)

    # --- Validation Report ---
    status_color = "#16A34A" if report["valid"] else "#DC2626"
    status_text = "Valid" if report["valid"] else "Invalid"

    info_card = """
    <div style="background: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 12px;
                padding: 16px 18px; height: 100px;">
        <div style="font-size: 10px; color: #6B6B6B; text-transform: uppercase;
                    letter-spacing: 0.8px; font-weight: 600; white-space: nowrap;">{label}</div>
        <div style="font-size: 22px; font-weight: 700; color: {color}; margin-top: 6px;
                    white-space: nowrap;">{value}</div>
        <div style="font-size: 11px; color: #9CA3AF; margin-top: 3px;">{sub}</div>
    </div>
    """

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.markdown(info_card.format(label="Status", value=status_text, color=status_color, sub="Validation"), unsafe_allow_html=True)
    with c2:
        st.markdown(info_card.format(label="Rows", value=f"{report['total_rows']:,}", color="#111111", sub=f"{report['total_columns']} columns"), unsafe_allow_html=True)
    with c3:
        st.markdown(info_card.format(label="Fraud", value=f"{report['fraud_count']:,}", color="#DC2626", sub=f"{report['fraud_percentage']}%"), unsafe_allow_html=True)
    with c4:
        st.markdown(info_card.format(label="Legitimate", value=f"{report['legit_count']:,}", color="#16A34A", sub=f"{100 - report['fraud_percentage']:.1f}%"), unsafe_allow_html=True)
    with c5:
        st.markdown(info_card.format(label="Missing Values", value=f"{report['missing_values']}", color="#F59E0B" if report['missing_values'] > 0 else "#16A34A", sub="Null cells"), unsafe_allow_html=True)
    with c6:
        st.markdown(info_card.format(label="Duplicates", value=f"{report['duplicate_rows']}", color="#F59E0B" if report['duplicate_rows'] > 0 else "#16A34A", sub="Duplicate rows"), unsafe_allow_html=True)

    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)

    # --- Charts Row ---
    chart_c1, chart_c2 = st.columns(2)

    with chart_c1:
        st.markdown('<div style="background: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 12px; padding: 20px;"><div style="font-size: 16px; font-weight: 600; color: #111111; margin-bottom: 4px;">Class Distribution</div><div style="font-size: 12px; color: #6B6B6B; margin-bottom: 12px;">Fraud vs Legitimate breakdown</div></div>', unsafe_allow_html=True)

        class_data = df["Class"].value_counts().reset_index()
        class_data.columns = ["Class", "Count"]
        class_data["Label"] = class_data["Class"].map({0: "Legitimate", 1: "Fraud"})

        fig_class = px.bar(
            class_data, x="Label", y="Count", color="Label",
            color_discrete_map={"Legitimate": "rgba(22,163,74,0.7)", "Fraud": "rgba(220,38,38,0.7)"},
            text="Count"
        )
        fig_class.update_layout(
            plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
            font=dict(family="Inter, sans-serif", color="#6B6B6B", size=12),
            showlegend=False, margin=dict(l=40, r=10, t=10, b=40), height=280,
            xaxis=dict(showline=False, gridcolor="#F5F5F5"),
            yaxis=dict(showline=False, gridcolor="#F5F5F5")
        )
        fig_class.update_traces(textposition="outside")
        st.plotly_chart(fig_class, use_container_width=True, config={'displayModeBar': False})

    with chart_c2:
        st.markdown('<div style="background: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 12px; padding: 20px;"><div style="font-size: 16px; font-weight: 600; color: #111111; margin-bottom: 4px;">Transaction Amount Distribution</div><div style="font-size: 12px; color: #6B6B6B; margin-bottom: 12px;">Amount spread across all transactions</div></div>', unsafe_allow_html=True)

        fig_amt = px.histogram(
            df, x="Amount", nbins=50,
            color_discrete_sequence=["rgba(22,163,74,0.5)"]
        )
        fig_amt.update_layout(
            plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
            font=dict(family="Inter, sans-serif", color="#6B6B6B", size=12),
            showlegend=False, margin=dict(l=40, r=10, t=10, b=40), height=280,
            xaxis=dict(title="Amount ($)", showline=False, gridcolor="#F5F5F5"),
            yaxis=dict(title="Frequency", showline=False, gridcolor="#F5F5F5")
        )
        st.plotly_chart(fig_amt, use_container_width=True, config={'displayModeBar': False})

    st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)

    # --- Statistical Summary ---
    st.markdown('<div style="background: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 12px; padding: 20px;"><div style="font-size: 16px; font-weight: 600; color: #111111; margin-bottom: 4px;">Statistical Summary</div><div style="font-size: 12px; color: #6B6B6B; margin-bottom: 12px;">Key statistics for Amount and Time features</div></div>', unsafe_allow_html=True)

    stats_df = df[["Time", "Amount"]].describe().round(2).T
    stats_df.insert(0, "Feature", stats_df.index)
    stats_df = stats_df.reset_index(drop=True)
    st.dataframe(stats_df, use_container_width=True, height=120)

    st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)

    # --- Data Preview ---
    st.markdown('<div style="background: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 12px; padding: 20px;"><div style="font-size: 16px; font-weight: 600; color: #111111; margin-bottom: 4px;">Data Preview</div><div style="font-size: 12px; color: #6B6B6B; margin-bottom: 12px;">First rows of the loaded dataset</div></div>', unsafe_allow_html=True)

    preview_rows = st.selectbox("Rows to show", [10, 25, 50, 100], index=0, key="ds_preview_rows")
    st.dataframe(df.head(preview_rows), use_container_width=True, height=400)

    st.markdown(f'<div style="font-size: 12px; color: #9CA3AF; margin-top: 8px; text-align: right;">Showing {min(preview_rows, len(df))} of {len(df):,} rows</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Page Placeholder (for pages not yet built)
# ---------------------------------------------------------------------------
def render_placeholder(page_name):
    st.markdown(f"""
    <div style="padding: 8px 0 24px;">
        <h1 style="font-size: 28px; font-weight: 700; color: #111111; margin-bottom: 4px;">
            {page_name}
        </h1>
        <p style="font-size: 14px; color: #6B6B6B;">
            This page will be built in the next phase.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background: #FFFFFF; border: 1px solid #E5E5E5;
                border-radius: 12px; padding: 48px; text-align: center;">
        <div style="font-size: 16px; color: #6B6B6B;">Coming soon</div>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session Timeout
# ---------------------------------------------------------------------------
def check_timeout():
    if st.session_state["authenticated"]:
        if check_session_timeout(st.session_state.get("last_activity")):
            st.session_state["authenticated"] = False
            st.session_state["user"] = None
            st.warning("Session expired due to inactivity. Please log in again.")
            st.rerun()


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    inject_bonsai_css()
    init_session_state()

    if st.session_state["authenticated"]:
        check_timeout()
        render_sidebar()
        inject_sidebar_toggle()

        page = st.session_state["current_page"]
        if page == "Dashboard":
            render_dashboard()
        elif page == "Dataset":
            render_dataset()
        elif page == "Models":
            from views.models_page import render_models
            render_models()
        elif page == "Predictor":
            from views.predictor_page import render_predictor
            render_predictor()
        elif page == "Profile":
            from views.profile_page import render_profile
            render_profile()
        elif page == "Settings":
            from views.settings_page import render_settings
            render_settings()
        elif page == "Reports":
            from views.reports_page import render_reports
            render_reports()
        else:
            render_placeholder(page)
    else:
        render_auth_screen()


if __name__ == "__main__":
    main()
