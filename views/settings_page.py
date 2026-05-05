"""Settings Page — Model Config, Admin Panel, System Info"""
import streamlit as st
import os
import pandas as pd
from datetime import datetime

def render_settings():
    st.session_state["last_activity"] = datetime.now()
    user = st.session_state["user"]

    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from src.auth import get_user_settings, update_user_settings, get_all_users, delete_user, get_system_stats

    st.markdown("""<div style="padding:8px 0 20px;">
        <h1 style="font-size:28px;font-weight:700;color:#111;margin-bottom:4px;">Settings</h1>
        <p style="font-size:14px;color:#6B6B6B;margin-top:0;">Configure model preferences and system options.</p>
    </div>""", unsafe_allow_html=True)

    settings = get_user_settings(user["id"])

    # --- Model Configuration ---
    st.markdown("""<div style="background:#FFF;border:1px solid #E5E5E5;border-radius:12px;padding:20px;margin-bottom:20px;">
        <div style="font-size:16px;font-weight:600;color:#111;margin-bottom:4px;">Model Configuration</div>
        <div style="font-size:12px;color:#6B6B6B;">Set your default model and prediction threshold</div>
    </div>""", unsafe_allow_html=True)

    # Check available models
    MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
    model_files = [f for f in os.listdir(MODELS_DIR) if f.endswith(".pkl") and f != "scaler.pkl"] if os.path.exists(MODELS_DIR) else []
    available_models = [f.replace(".pkl","").replace("_"," ").title() for f in model_files]

    if not available_models:
        available_models = ["Random Forest"]

    cfg1, cfg2 = st.columns(2)
    with cfg1:
        current_model = settings.get("active_model", "Random Forest")
        model_idx = available_models.index(current_model) if current_model in available_models else 0
        new_model = st.selectbox("Active Model", available_models, index=model_idx, key="settings_model")
    with cfg2:
        current_threshold = settings.get("default_threshold", 0.5)
        new_threshold = st.slider("Default Threshold", 0.0, 1.0, float(current_threshold), 0.05, key="settings_threshold")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Auto-clear toggle
    auto_clear = st.checkbox("Auto-clear uploaded data on logout",
        value=settings.get("auto_clear_data", False), key="settings_auto_clear")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    if st.button("Save Settings", key="save_settings_btn", use_container_width=True):
        update_user_settings(user["id"],
            active_model=new_model,
            default_threshold=new_threshold,
            auto_clear_data=auto_clear)
        st.markdown('<div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;padding:10px 16px;color:#16A34A;font-size:13px;font-weight:500;text-align:center;margin-top:8px;">Settings saved successfully.</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # --- Admin Panel (only for Admin role) ---
    if user["role"] == "Admin":
        st.markdown("""<div style="background:#FFF;border:1px solid #E5E5E5;border-radius:12px;padding:20px;margin-bottom:20px;">
            <div style="font-size:16px;font-weight:600;color:#111;margin-bottom:4px;">Admin Panel</div>
            <div style="font-size:12px;color:#6B6B6B;">Manage registered users</div>
        </div>""", unsafe_allow_html=True)

        all_users = get_all_users()

        if all_users:
            user_data = []
            for u in all_users:
                user_data.append({
                    "ID": u["id"],
                    "Full Name": u["full_name"],
                    "Username": u["username"],
                    "Role": u["role"],
                    "Joined": u["date_joined"],
                })
            user_df = pd.DataFrame(user_data)
            st.dataframe(user_df, use_container_width=True, height=200)

            # Delete user
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            other_users = [u for u in all_users if u["id"] != user["id"]]
            if other_users:
                del_options = [f"{u['username']} ({u['full_name']})" for u in other_users]
                del_choice = st.selectbox("Select user to remove", del_options, key="del_user_select")

                if st.button("Delete User", key="del_user_btn"):
                    idx = del_options.index(del_choice)
                    target_id = other_users[idx]["id"]
                    result = delete_user(target_id)
                    if result["success"]:
                        st.markdown(f'<div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;padding:10px 16px;color:#16A34A;font-size:13px;font-weight:500;text-align:center;margin-top:8px;">{result["message"]}</div>', unsafe_allow_html=True)
                        st.rerun()
                    else:
                        st.markdown(f'<div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;padding:10px 16px;color:#DC2626;font-size:13px;font-weight:500;text-align:center;margin-top:8px;">{result["message"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="font-size:13px;color:#9CA3AF;">No other users to manage.</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # --- System Info ---
    st.markdown("""<div style="background:#FFF;border:1px solid #E5E5E5;border-radius:12px;padding:20px;margin-bottom:20px;">
        <div style="font-size:16px;font-weight:600;color:#111;margin-bottom:4px;">System Information</div>
        <div style="font-size:12px;color:#6B6B6B;">Current system status and statistics</div>
    </div>""", unsafe_allow_html=True)

    stats = get_system_stats()
    card = """<div style="background:#FFF;border:1px solid #E5E5E5;border-radius:12px;padding:16px 18px;">
        <div style="font-size:10px;color:#6B6B6B;text-transform:uppercase;letter-spacing:.8px;font-weight:600;">{label}</div>
        <div style="font-size:24px;font-weight:700;color:{color};margin-top:6px;">{value}</div>
        <div style="font-size:11px;color:#9CA3AF;margin-top:4px;">{sub}</div>
    </div>"""

    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown(card.format(label="Registered Users", value=stats["total_users"], color="#111", sub="Active accounts"), unsafe_allow_html=True)
    with s2:
        st.markdown(card.format(label="Total Actions", value=stats["total_predictions"], color="#16A34A", sub="All activity logged"), unsafe_allow_html=True)
    with s3:
        st.markdown(card.format(label="Database Size", value=f"{stats['database_size_kb']} KB", color="#2563EB", sub="SQLite storage"), unsafe_allow_html=True)
