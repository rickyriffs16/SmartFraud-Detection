"""Profile Page — User Info, Activity Log, Password Change"""
import streamlit as st
import os
import pandas as pd
from datetime import datetime

def render_profile():
    st.session_state["last_activity"] = datetime.now()
    user = st.session_state["user"]

    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from src.auth import get_user_activity, change_password

    st.markdown("""<div style="padding:8px 0 20px;">
        <h1 style="font-size:28px;font-weight:700;color:#111;margin-bottom:4px;">Profile</h1>
        <p style="font-size:14px;color:#6B6B6B;margin-top:0;">Your account details and activity history.</p>
    </div>""", unsafe_allow_html=True)

    # --- Profile Card ---
    st.markdown(f"""
    <div style="background:#FFF;border:1px solid #E5E5E5;border-radius:12px;padding:24px;margin-bottom:20px;">
        <div style="display:flex;align-items:center;gap:16px;">
            <div style="width:56px;height:56px;background:#16A34A;border-radius:14px;display:flex;
                        align-items:center;justify-content:center;color:white;font-weight:700;font-size:20px;">
                {user['full_name'][0].upper()}
            </div>
            <div>
                <div style="font-size:20px;font-weight:700;color:#111;">{user['full_name']}</div>
                <div style="font-size:13px;color:#6B6B6B;">@{user['username']} · {user['role']}</div>
            </div>
        </div>
        <div style="height:1px;background:#E5E5E5;margin:16px 0;"></div>
        <div style="display:flex;gap:32px;">
            <div>
                <div style="font-size:10px;color:#6B6B6B;text-transform:uppercase;letter-spacing:.8px;font-weight:600;">Role</div>
                <div style="font-size:15px;font-weight:600;color:#111;margin-top:2px;">{user['role']}</div>
            </div>
            <div>
                <div style="font-size:10px;color:#6B6B6B;text-transform:uppercase;letter-spacing:.8px;font-weight:600;">Username</div>
                <div style="font-size:15px;font-weight:600;color:#111;margin-top:2px;">@{user['username']}</div>
            </div>
            <div>
                <div style="font-size:10px;color:#6B6B6B;text-transform:uppercase;letter-spacing:.8px;font-weight:600;">Joined</div>
                <div style="font-size:15px;font-weight:600;color:#111;margin-top:2px;">{user['date_joined']}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Activity Log ---
    st.markdown("""<div style="background:#FFF;border:1px solid #E5E5E5;border-radius:12px;padding:20px;margin-bottom:20px;">
        <div style="font-size:16px;font-weight:600;color:#111;margin-bottom:4px;">Activity Log</div>
        <div style="font-size:12px;color:#6B6B6B;">Your recent actions and predictions</div>
    </div>""", unsafe_allow_html=True)

    activities = get_user_activity(user["id"], limit=100)

    if activities:
        act_data = []
        for a in activities:
            act_data.append({
                "Timestamp": a["timestamp"],
                "Action": a["action"],
                "Amount": f"${a['amount']:.2f}" if a["amount"] is not None else "—",
                "Result": a["result"] if a["result"] else "—",
                "Confidence": f"{a['confidence']*100:.1f}%" if a["confidence"] is not None else "—",
                "Threshold": a["threshold"] if a["threshold"] is not None else "—",
            })
        act_df = pd.DataFrame(act_data)
        st.dataframe(act_df, use_container_width=True, height=300)

        # Download activity CSV
        csv_data = act_df.to_csv(index=False)
        st.download_button("Download Activity Log", csv_data,
            file_name=f"activity_log_{user['username']}.csv", mime="text/csv",
            use_container_width=True, key="download_activity")
    else:
        st.markdown("""<div style="background:#F7F7F5;border:1px solid #E5E5E5;border-radius:8px;
            padding:24px;text-align:center;color:#6B6B6B;font-size:14px;">No activity recorded yet.</div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # --- Change Password ---
    st.markdown("""<div style="background:#FFF;border:1px solid #E5E5E5;border-radius:12px;padding:20px;margin-bottom:20px;">
        <div style="font-size:16px;font-weight:600;color:#111;margin-bottom:4px;">Change Password</div>
        <div style="font-size:12px;color:#6B6B6B;">Update your account password</div>
    </div>""", unsafe_allow_html=True)

    with st.form("change_password_form", clear_on_submit=True):
        old_pw = st.text_input("Current Password", type="password", key="old_pw")
        new_pw = st.text_input("New Password", type="password", placeholder="Min 6 characters", key="new_pw")
        confirm_pw = st.text_input("Confirm New Password", type="password", key="confirm_pw")
        submitted = st.form_submit_button("Update Password", use_container_width=True)

    if submitted:
        if not old_pw or not new_pw or not confirm_pw:
            st.markdown('<div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;padding:10px 16px;color:#DC2626;font-size:13px;font-weight:500;text-align:center;margin-top:8px;">All fields are required.</div>', unsafe_allow_html=True)
        elif new_pw != confirm_pw:
            st.markdown('<div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;padding:10px 16px;color:#DC2626;font-size:13px;font-weight:500;text-align:center;margin-top:8px;">New passwords do not match.</div>', unsafe_allow_html=True)
        else:
            result = change_password(user["id"], old_pw, new_pw)
            if result["success"]:
                st.markdown(f'<div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;padding:10px 16px;color:#16A34A;font-size:13px;font-weight:500;text-align:center;margin-top:8px;">{result["message"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;padding:10px 16px;color:#DC2626;font-size:13px;font-weight:500;text-align:center;margin-top:8px;">{result["message"]}</div>', unsafe_allow_html=True)
