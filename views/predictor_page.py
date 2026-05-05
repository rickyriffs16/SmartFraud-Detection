"""Predictor Page — Single & Batch Fraud Prediction"""
import streamlit as st
import os, json
import pandas as pd
import numpy as np
from datetime import datetime

def render_predictor():
    st.session_state["last_activity"] = datetime.now()
    user = st.session_state["user"]

    st.markdown("""<div style="padding:8px 0 20px;">
        <h1 style="font-size:28px;font-weight:700;color:#111;margin-bottom:4px;">Predictor</h1>
        <p style="font-size:14px;color:#6B6B6B;margin-top:0;">Run fraud predictions on individual or batch transactions.</p>
    </div>""", unsafe_allow_html=True)

    # Check if models exist
    MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
    model_files = [f for f in os.listdir(MODELS_DIR) if f.endswith(".pkl") and f != "scaler.pkl"] if os.path.exists(MODELS_DIR) else []

    if not model_files:
        st.markdown("""<div style="background:#FFF;border:1px solid #E5E5E5;border-radius:12px;padding:48px;text-align:center;">
            <div style="font-size:18px;font-weight:600;color:#111;margin-bottom:8px;">No Models Available</div>
            <div style="font-size:14px;color:#6B6B6B;">Go to the Models page and train models first.</div>
        </div>""", unsafe_allow_html=True)
        return

    available_models = [f.replace(".pkl","").replace("_"," ").title() for f in model_files]

    tab_single, tab_batch = st.tabs(["Single Transaction", "Batch Upload"])

    # ===================== SINGLE TRANSACTION =====================
    with tab_single:
        st.markdown("""<div style="background:#FFF;border:1px solid #E5E5E5;border-radius:12px;padding:20px;margin:16px 0;">
            <div style="font-size:16px;font-weight:600;color:#111;margin-bottom:4px;">Transaction Input</div>
            <div style="font-size:12px;color:#6B6B6B;">Enter transaction features to predict fraud probability.</div>
        </div>""", unsafe_allow_html=True)

        # Model & Threshold
        cfg1, cfg2 = st.columns(2)
        with cfg1:
            model_choice = st.selectbox("Model", available_models,
                index=available_models.index("Random Forest") if "Random Forest" in available_models else 0,
                key="pred_model")
        with cfg2:
            threshold = st.slider("Threshold", 0.0, 1.0, 0.5, 0.05, key="pred_threshold",
                help="Probability >= threshold = Fraud")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # Amount & Time
        at1, at2 = st.columns(2)
        with at1:
            amount = st.number_input("Amount ($)", min_value=0.0, value=100.0, step=1.0, key="pred_amount")
        with at2:
            time_val = st.number_input("Time (seconds)", min_value=0.0, value=0.0, step=1.0, key="pred_time")

        # V1-V28 in 4 columns
        st.markdown("""<div style="background:#FFF;border:1px solid #E5E5E5;border-radius:12px;padding:16px;margin:12px 0;">
            <div style="font-size:14px;font-weight:600;color:#111;margin-bottom:8px;">PCA Features (V1 - V28)</div>
            <div style="font-size:11px;color:#9CA3AF;margin-bottom:12px;">Default values are 0. Adjust as needed.</div>
        </div>""", unsafe_allow_html=True)

        v_values = {}
        cols_per_row = 4
        for row_start in range(1, 29, cols_per_row):
            cols = st.columns(cols_per_row)
            for i, col in enumerate(cols):
                v_idx = row_start + i
                if v_idx <= 28:
                    with col:
                        v_values[f"V{v_idx}"] = st.number_input(f"V{v_idx}", value=0.0, step=0.1,
                            key=f"pred_v{v_idx}", label_visibility="visible")

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        # Predict button
        if st.button("Predict", key="pred_single_btn", use_container_width=True):
            try:
                import sys
                sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
                from src.predictor import predict_transaction
                from src.auth import log_activity

                data = {"Amount": amount, "Time": time_val}
                data.update(v_values)

                result = predict_transaction(data, threshold=threshold, model_name=model_choice)

                # Log the prediction
                log_activity(
                    user["id"], "Prediction",
                    input_amount=amount,
                    result=result["prediction"],
                    confidence=result["probability"],
                    threshold=threshold
                )

                # Display result
                is_fraud = result["prediction"] == "Fraud"
                color = "#DC2626" if is_fraud else "#16A34A"
                bg = "#FEF2F2" if is_fraud else "#F0FDF4"
                border = "#FECACA" if is_fraud else "#BBF7D0"
                prob_pct = round(result["probability"] * 100, 2)

                st.markdown(f"""
                <div style="background:{bg};border:2px solid {border};border-radius:12px;padding:24px;margin-top:16px;text-align:center;">
                    <div style="font-size:12px;color:#6B6B6B;text-transform:uppercase;letter-spacing:1px;font-weight:600;margin-bottom:8px;">Prediction Result</div>
                    <div style="font-size:36px;font-weight:800;color:{color};margin-bottom:4px;">{result['prediction'].upper()}</div>
                    <div style="font-size:16px;color:{color};font-weight:600;margin-bottom:16px;">Fraud Probability: {prob_pct}%</div>
                    <div style="background:#E5E5E5;border-radius:99px;height:12px;width:80%;margin:0 auto;overflow:hidden;">
                        <div style="background:{color};height:100%;width:{prob_pct}%;border-radius:99px;transition:width 0.5s;"></div>
                    </div>
                    <div style="font-size:12px;color:#9CA3AF;margin-top:12px;">
                        Model: {result['model_used']} | Threshold: {result['threshold']} | Amount: ${amount:.2f}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            except Exception as e:
                st.markdown(f'<div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;padding:10px 16px;color:#DC2626;font-size:13px;margin-top:12px;">{str(e)}</div>', unsafe_allow_html=True)

    # ===================== BATCH UPLOAD =====================
    with tab_batch:
        st.markdown("""<div style="background:#FFF;border:1px solid #E5E5E5;border-radius:12px;padding:20px;margin:16px 0;">
            <div style="font-size:16px;font-weight:600;color:#111;margin-bottom:4px;">Batch Prediction</div>
            <div style="font-size:12px;color:#6B6B6B;">Upload a CSV with Time, V1-V28, and Amount columns.</div>
        </div>""", unsafe_allow_html=True)

        bcfg1, bcfg2 = st.columns(2)
        with bcfg1:
            batch_model = st.selectbox("Model", available_models,
                index=available_models.index("Random Forest") if "Random Forest" in available_models else 0,
                key="batch_model")
        with bcfg2:
            batch_threshold = st.slider("Threshold", 0.0, 1.0, 0.5, 0.05, key="batch_threshold")

        uploaded = st.file_uploader("Upload CSV", type=["csv"], key="batch_upload", label_visibility="collapsed")

        if uploaded is not None:
            try:
                df = pd.read_csv(uploaded)
                required = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount"]
                missing = [c for c in required if c not in df.columns]

                if missing:
                    st.markdown(f'<div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;padding:10px 16px;color:#DC2626;font-size:13px;">Missing columns: {", ".join(missing)}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div style="font-size:13px;color:#6B6B6B;margin:8px 0;">Loaded {len(df):,} transactions</div>', unsafe_allow_html=True)

                    if st.button("Run Batch Predictions", key="batch_predict_btn", use_container_width=True):
                        import sys
                        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
                        from src.predictor import predict_batch
                        from src.auth import log_activity

                        with st.spinner("Running predictions..."):
                            results_df = predict_batch(df, threshold=batch_threshold, model_name=batch_model)

                        fraud_count = (results_df["Prediction"] == "Fraud").sum()
                        legit_count = (results_df["Prediction"] == "Legit").sum()

                        # Log batch prediction
                        log_activity(user["id"], "Batch Prediction",
                            result=f"{fraud_count} fraud / {legit_count} legit",
                            threshold=batch_threshold)

                        # Summary cards
                        sc1, sc2, sc3 = st.columns(3)
                        card = """<div style="background:#FFF;border:1px solid #E5E5E5;border-radius:12px;padding:16px;">
                            <div style="font-size:10px;color:#6B6B6B;text-transform:uppercase;letter-spacing:.8px;font-weight:600;">{l}</div>
                            <div style="font-size:24px;font-weight:700;color:{c};margin-top:4px;">{v}</div></div>"""
                        with sc1:
                            st.markdown(card.format(l="Total",v=f"{len(results_df):,}",c="#111"), unsafe_allow_html=True)
                        with sc2:
                            st.markdown(card.format(l="Fraud Detected",v=str(fraud_count),c="#DC2626"), unsafe_allow_html=True)
                        with sc3:
                            st.markdown(card.format(l="Legitimate",v=str(legit_count),c="#16A34A"), unsafe_allow_html=True)

                        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

                        # Results table
                        display = results_df[["Time","Amount","Prediction","Fraud_Probability"]].copy()
                        display["Fraud_Probability"] = (display["Fraud_Probability"] * 100).round(2)
                        display.columns = ["Time","Amount ($)","Prediction","Fraud Prob (%)"]
                        st.dataframe(display, use_container_width=True, height=400)

                        # Download button
                        csv_data = results_df.to_csv(index=False)
                        st.download_button("Download Results CSV", csv_data,
                            file_name="batch_predictions.csv", mime="text/csv",
                            use_container_width=True, key="batch_download")

            except Exception as e:
                st.markdown(f'<div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;padding:10px 16px;color:#DC2626;font-size:13px;">{str(e)}</div>', unsafe_allow_html=True)
