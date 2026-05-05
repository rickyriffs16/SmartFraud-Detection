"""Reports Page — Exports & Summary Statistics"""
import streamlit as st
import os, json
import pandas as pd
from datetime import datetime

def render_reports():
    st.session_state["last_activity"] = datetime.now()
    user = st.session_state["user"]

    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from src.auth import get_user_activity

    st.markdown("""<div style="padding:8px 0 20px;">
        <h1 style="font-size:28px;font-weight:700;color:#111;margin-bottom:4px;">Reports</h1>
        <p style="font-size:14px;color:#6B6B6B;margin-top:0;">View summaries and download data exports.</p>
    </div>""", unsafe_allow_html=True)

    METRICS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "model_metrics.json")
    DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sample_data.csv")

    # --- Model Performance Summary ---
    st.markdown("""<div style="background:#FFF;border:1px solid #E5E5E5;border-radius:12px;padding:20px;margin-bottom:20px;">
        <div style="font-size:16px;font-weight:600;color:#111;margin-bottom:4px;">Model Performance Summary</div>
        <div style="font-size:12px;color:#6B6B6B;">Overview of the best trained model</div>
    </div>""", unsafe_allow_html=True)

    card = """<div style="background:#FFF;border:1px solid #E5E5E5;border-radius:12px;padding:16px 18px;">
        <div style="font-size:10px;color:#6B6B6B;text-transform:uppercase;letter-spacing:.8px;font-weight:600;">{label}</div>
        <div style="font-size:24px;font-weight:700;color:{color};margin-top:6px;">{value}</div>
        <div style="font-size:11px;color:#9CA3AF;margin-top:4px;">{sub}</div>
    </div>"""

    if os.path.exists(METRICS_PATH):
        with open(METRICS_PATH, "r") as f:
            metrics = json.load(f)
        meta = metrics.get("_metadata", {})
        best_name = meta.get("best_model", "N/A")
        best = metrics.get(best_name, {})

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.markdown(card.format(label="Best Model", value=best_name, color="#111", sub="Highest F1 score"), unsafe_allow_html=True)
        with c2:
            st.markdown(card.format(label="Accuracy", value=f"{best.get('accuracy',0)}%", color="#16A34A", sub="Test set"), unsafe_allow_html=True)
        with c3:
            st.markdown(card.format(label="Precision", value=f"{best.get('precision',0)}%", color="#2563EB", sub="Test set"), unsafe_allow_html=True)
        with c4:
            st.markdown(card.format(label="Recall", value=f"{best.get('recall',0)}%", color="#F59E0B", sub="Test set"), unsafe_allow_html=True)
        with c5:
            st.markdown(card.format(label="F1 Score", value=f"{best.get('f1_score',0)}%", color="#7C3AED", sub="Test set"), unsafe_allow_html=True)
    else:
        st.markdown("""<div style="background:#F7F7F5;border:1px solid #E5E5E5;border-radius:8px;padding:24px;text-align:center;color:#6B6B6B;font-size:14px;">
            No model metrics available. Train models first.</div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # --- Quick Stats ---
    activities = get_user_activity(user["id"], limit=1000)
    predictions = [a for a in activities if a["action"] in ("Prediction", "Batch Prediction")]
    fraud_preds = [a for a in activities if a["result"] == "Fraud"]
    confidences = [a["confidence"] for a in activities if a["confidence"] is not None]
    avg_conf = sum(confidences) / len(confidences) * 100 if confidences else 0

    st.markdown("""<div style="background:#FFF;border:1px solid #E5E5E5;border-radius:12px;padding:20px;margin-bottom:20px;">
        <div style="font-size:16px;font-weight:600;color:#111;margin-bottom:4px;">Your Prediction Stats</div>
        <div style="font-size:12px;color:#6B6B6B;">Summary of your prediction activity</div>
    </div>""", unsafe_allow_html=True)

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(card.format(label="Total Predictions", value=str(len(predictions)), color="#111", sub="All time"), unsafe_allow_html=True)
    with s2:
        st.markdown(card.format(label="Fraud Detected", value=str(len(fraud_preds)), color="#DC2626", sub="Flagged as fraud"), unsafe_allow_html=True)
    with s3:
        st.markdown(card.format(label="Avg Confidence", value=f"{avg_conf:.1f}%", color="#16A34A", sub="Mean probability"), unsafe_allow_html=True)
    with s4:
        st.markdown(card.format(label="Total Actions", value=str(len(activities)), color="#2563EB", sub="Logins + predictions"), unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # --- Export Section ---
    st.markdown("""<div style="background:#FFF;border:1px solid #E5E5E5;border-radius:12px;padding:20px;margin-bottom:20px;">
        <div style="font-size:16px;font-weight:600;color:#111;margin-bottom:4px;">Data Exports</div>
        <div style="font-size:12px;color:#6B6B6B;">Download reports and data as CSV files</div>
    </div>""", unsafe_allow_html=True)

    exp1, exp2, exp3 = st.columns(3)

    # Export 1: Model Metrics CSV
    with exp1:
        st.markdown("""<div style="background:#F7F7F5;border:1px solid #E5E5E5;border-radius:12px;padding:16px;margin-bottom:8px;">
            <div style="font-size:14px;font-weight:600;color:#111;margin-bottom:4px;">Model Metrics</div>
            <div style="font-size:12px;color:#6B6B6B;">Performance scores for all trained models</div>
        </div>""", unsafe_allow_html=True)

        if os.path.exists(METRICS_PATH):
            with open(METRICS_PATH, "r") as f:
                metrics = json.load(f)
            model_names = [k for k in metrics if k != "_metadata"]
            rows = []
            for n in model_names:
                m = metrics[n]
                rows.append({"Model": n, "Accuracy": m.get("accuracy",0), "Precision": m.get("precision",0),
                    "Recall": m.get("recall",0), "F1": m.get("f1_score",0), "AUC-ROC": m.get("auc_roc",0),
                    "Training Time (s)": m.get("training_time_seconds",0)})
            metrics_df = pd.DataFrame(rows)
            st.download_button("Download Metrics", metrics_df.to_csv(index=False),
                file_name="model_metrics.csv", mime="text/csv", use_container_width=True, key="dl_metrics")
        else:
            st.markdown('<div style="font-size:12px;color:#9CA3AF;padding:8px;">No metrics available</div>', unsafe_allow_html=True)

    # Export 2: Flagged Transactions
    with exp2:
        st.markdown("""<div style="background:#F7F7F5;border:1px solid #E5E5E5;border-radius:12px;padding:16px;margin-bottom:8px;">
            <div style="font-size:14px;font-weight:600;color:#111;margin-bottom:4px;">Flagged Transactions</div>
            <div style="font-size:12px;color:#6B6B6B;">All fraud-labeled rows from the dataset</div>
        </div>""", unsafe_allow_html=True)

        if os.path.exists(DATA_PATH):
            df = pd.read_csv(DATA_PATH)
            fraud_df = df[df["Class"] == 1]
            st.download_button(f"Download ({len(fraud_df)} rows)", fraud_df.to_csv(index=False),
                file_name="flagged_transactions.csv", mime="text/csv", use_container_width=True, key="dl_fraud")
        else:
            st.markdown('<div style="font-size:12px;color:#9CA3AF;padding:8px;">No dataset loaded</div>', unsafe_allow_html=True)

    # Export 3: Activity Log
    with exp3:
        st.markdown("""<div style="background:#F7F7F5;border:1px solid #E5E5E5;border-radius:12px;padding:16px;margin-bottom:8px;">
            <div style="font-size:14px;font-weight:600;color:#111;margin-bottom:4px;">Activity Log</div>
            <div style="font-size:12px;color:#6B6B6B;">Your complete action history</div>
        </div>""", unsafe_allow_html=True)

        if activities:
            act_rows = []
            for a in activities:
                act_rows.append({"Timestamp": a["timestamp"], "Action": a["action"],
                    "Amount": a["amount"], "Result": a["result"],
                    "Confidence": a["confidence"], "Threshold": a["threshold"]})
            act_df = pd.DataFrame(act_rows)
            st.download_button(f"Download ({len(act_df)} entries)", act_df.to_csv(index=False),
                file_name="activity_log.csv", mime="text/csv", use_container_width=True, key="dl_activity")
        else:
            st.markdown('<div style="font-size:12px;color:#9CA3AF;padding:8px;">No activity recorded</div>', unsafe_allow_html=True)
