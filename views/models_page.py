"""Models Page — Training, Metrics, Visualization"""
import streamlit as st
import json, os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

CARD = """
<div style="background:#FFF;border:1px solid #E5E5E5;border-radius:12px;padding:14px 16px;">
  <div style="font-size:10px;color:#6B6B6B;text-transform:uppercase;letter-spacing:.8px;font-weight:600;">{label}</div>
  <div style="font-size:22px;font-weight:700;color:{color};margin-top:4px;">{value}</div>
</div>"""

def render_models():
    st.session_state["last_activity"] = datetime.now()
    st.markdown("""<div style="padding:8px 0 20px;">
        <h1 style="font-size:28px;font-weight:700;color:#111;margin-bottom:4px;">Models</h1>
        <p style="font-size:14px;color:#6B6B6B;margin-top:0;">Train, evaluate, and compare machine learning models.</p>
    </div>""", unsafe_allow_html=True)

    METRICS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "model_metrics.json")

    # --- Train Button ---
    st.markdown("""<div style="background:#FFF;border:1px solid #E5E5E5;border-radius:12px;padding:20px;margin-bottom:20px;">
        <div style="font-size:16px;font-weight:600;color:#111;margin-bottom:4px;">Model Training</div>
        <div style="font-size:12px;color:#6B6B6B;">Train all models using the current dataset with SMOTE balancing.</div>
    </div>""", unsafe_allow_html=True)

    c1, c2 = st.columns([1, 3])
    with c1:
        train_clicked = st.button("Train All Models", key="train_btn", use_container_width=True)

    if train_clicked:
        try:
            import sys
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            from src.data_engine import run_full_pipeline
            from src.model_trainer import train_all_models
            status = st.empty()
            pbar = st.progress(0)
            status.markdown('<div style="font-size:13px;color:#6B6B6B;">Loading data...</div>', unsafe_allow_html=True)
            pipeline = run_full_pipeline()
            pbar.progress(0.2)
            st.session_state["smote_before"] = pipeline["before_smote"]
            st.session_state["smote_after"] = pipeline["after_smote"]

            def cb(name, step, total):
                if step < total:
                    pbar.progress(0.2 + (step+1)/total*0.8)
                    status.markdown(f'<div style="font-size:13px;color:#6B6B6B;">Training: {name}...</div>', unsafe_allow_html=True)
                else:
                    pbar.progress(1.0)
                    status.markdown('<div style="font-size:13px;color:#16A34A;font-weight:600;">Training complete!</div>', unsafe_allow_html=True)

            results = train_all_models(pipeline["X_train"], pipeline["y_train"],
                pipeline["X_test"], pipeline["y_test"], pipeline["feature_names"], progress_callback=cb)
            st.session_state["training_results"] = results
            st.rerun()
        except Exception as e:
            st.error(str(e))
            return

    if not os.path.exists(METRICS_PATH):
        st.markdown("""<div style="background:#FFF;border:1px solid #E5E5E5;border-radius:12px;padding:48px;text-align:center;">
            <div style="font-size:18px;font-weight:600;color:#111;margin-bottom:8px;">No Models Trained</div>
            <div style="font-size:14px;color:#6B6B6B;">Click "Train All Models" to start.</div>
        </div>""", unsafe_allow_html=True)
        return

    with open(METRICS_PATH, "r") as f:
        metrics = json.load(f)
    meta = metrics.get("_metadata", {})
    model_names = [k for k in metrics if k != "_metadata"]

    # --- Info Banner ---
    st.markdown(f"""<div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;padding:12px 16px;margin-bottom:20px;">
        <div style="font-size:13px;color:#16A34A;font-weight:500;">
            Trained: {meta.get('trained_at','N/A')} | {meta.get('num_train_samples',0):,} train / {meta.get('num_test_samples',0):,} test samples | Best: {meta.get('best_model','N/A')}
        </div></div>""", unsafe_allow_html=True)

    # --- SMOTE Chart ---
    if "smote_before" in st.session_state:
        st.markdown("""<div style="background:#FFF;border:1px solid #E5E5E5;border-radius:12px;padding:20px;margin-bottom:20px;">
            <div style="font-size:16px;font-weight:600;color:#111;margin-bottom:4px;">SMOTE Balancing</div>
            <div style="font-size:12px;color:#6B6B6B;">Before and after oversampling</div></div>""", unsafe_allow_html=True)
        b = st.session_state["smote_before"]
        a = st.session_state["smote_after"]
        sdf = pd.DataFrame([
            {"Stage":"Before","Class":"Legitimate","Count":b["Legitimate"]},
            {"Stage":"Before","Class":"Fraud","Count":b["Fraud"]},
            {"Stage":"After","Class":"Legitimate","Count":a["Legitimate"]},
            {"Stage":"After","Class":"Fraud","Count":a["Fraud"]},
        ])
        fig = px.bar(sdf, x="Stage", y="Count", color="Class", barmode="group",
            color_discrete_map={"Legitimate":"rgba(22,163,74,0.7)","Fraud":"rgba(220,38,38,0.7)"}, text="Count")
        fig.update_layout(plot_bgcolor="#FFF",paper_bgcolor="#FFF",font=dict(family="Inter",color="#6B6B6B",size=12),
            legend=dict(orientation="h",y=1.02,x=1,xanchor="right"),margin=dict(l=40,r=10,t=10,b=40),height=260,
            xaxis=dict(showline=False,gridcolor="#F5F5F5"),yaxis=dict(showline=False,gridcolor="#F5F5F5"))
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar':False}, key="smote_chart")

    # --- Leaderboard ---
    st.markdown("""<div style="background:#FFF;border:1px solid #E5E5E5;border-radius:12px;padding:20px;margin-bottom:20px;">
        <div style="font-size:16px;font-weight:600;color:#111;margin-bottom:4px;">Model Leaderboard</div>
        <div style="font-size:12px;color:#6B6B6B;">All models ranked by F1 score</div></div>""", unsafe_allow_html=True)
    rows = []
    for n in model_names:
        m = metrics[n]
        rows.append({"Model":n,"Accuracy":m.get("accuracy",0),"Precision":m.get("precision",0),
            "Recall":m.get("recall",0),"F1":m.get("f1_score",0),"AUC-ROC":m.get("auc_roc",0),"Time(s)":m.get("training_time_seconds",0)})
    ldf = pd.DataFrame(rows).sort_values("F1",ascending=False).reset_index(drop=True)
    ldf.index += 1
    st.dataframe(ldf, use_container_width=True, height=200)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # --- Per-Model Details ---
    st.markdown("""<div style="background:#FFF;border:1px solid #E5E5E5;border-radius:12px;padding:20px;margin-bottom:12px;">
        <div style="font-size:16px;font-weight:600;color:#111;margin-bottom:4px;">Model Details</div>
        <div style="font-size:12px;color:#6B6B6B;">Expand to view confusion matrix and feature importance</div></div>""", unsafe_allow_html=True)

    best = meta.get("best_model","")
    for idx, name in enumerate(model_names):
        m = metrics[name]
        tag = " [BEST]" if name == best else ""
        with st.expander(f"{name}{tag} — F1: {m.get('f1_score',0)}%"):
            st.markdown(f'<div style="font-size:13px;color:#6B6B6B;margin-bottom:16px;">{m.get("description","")}</div>', unsafe_allow_html=True)
            mc = st.columns(5)
            labels = ["Accuracy","Precision","Recall","F1 Score","AUC-ROC"]
            keys = ["accuracy","precision","recall","f1_score","auc_roc"]
            colors = ["#16A34A","#2563EB","#F59E0B","#7C3AED","#DC2626"]
            for i in range(5):
                with mc[i]:
                    st.markdown(CARD.format(label=labels[i],value=f"{m.get(keys[i],0)}%",color=colors[i]), unsafe_allow_html=True)
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

            d1, d2 = st.columns(2)
            with d1:
                cm = m.get("confusion_matrix",{})
                z = [[cm.get("true_negative",0),cm.get("false_positive",0)],[cm.get("false_negative",0),cm.get("true_positive",0)]]
                fig_cm = go.Figure(data=go.Heatmap(z=z,x=["Pred Legit","Pred Fraud"],y=["Actual Legit","Actual Fraud"],
                    text=[[str(v) for v in r] for r in z],texttemplate="%{text}",textfont=dict(size=16,color="white"),
                    colorscale=[[0,"rgba(22,163,74,0.3)"],[1,"#16A34A"]],showscale=False,hoverinfo="skip"))
                fig_cm.update_layout(title=dict(text="Confusion Matrix",font=dict(size=14,color="#111",family="Inter")),
                    plot_bgcolor="#FFF",paper_bgcolor="#FFF",font=dict(family="Inter",color="#6B6B6B",size=12),
                    margin=dict(l=10,r=10,t=40,b=10),height=280,yaxis=dict(autorange="reversed"))
                st.plotly_chart(fig_cm, use_container_width=True, config={'displayModeBar':False}, key=f"cm_{idx}")
            with d2:
                feats = m.get("top_features",[])
                if feats:
                    fdf = pd.DataFrame(feats[:10]).sort_values("importance",ascending=True)
                    fig_f = px.bar(fdf,x="importance",y="feature",orientation="h",color_discrete_sequence=["rgba(22,163,74,0.7)"])
                    fig_f.update_layout(title=dict(text="Feature Importance",font=dict(size=14,color="#111",family="Inter")),
                        plot_bgcolor="#FFF",paper_bgcolor="#FFF",font=dict(family="Inter",color="#6B6B6B",size=12),
                        margin=dict(l=10,r=10,t=40,b=10),height=280,showlegend=False,
                        xaxis=dict(showline=False,gridcolor="#F5F5F5"),yaxis=dict(showline=False))
                    st.plotly_chart(fig_f, use_container_width=True, config={'displayModeBar':False}, key=f"feat_{idx}")

            # ROC curve if training was done this session
            if "training_results" in st.session_state and name in st.session_state["training_results"]:
                roc = st.session_state["training_results"][name].get("roc_curve",{})
                if roc:
                    fig_r = go.Figure()
                    fig_r.add_trace(go.Scatter(x=roc["fpr"],y=roc["tpr"],mode="lines",name=f"AUC={m.get('auc_roc',0)}%",line=dict(color="#16A34A",width=2)))
                    fig_r.add_trace(go.Scatter(x=[0,1],y=[0,1],mode="lines",name="Random",line=dict(color="#E5E5E5",dash="dash")))
                    fig_r.update_layout(title=dict(text="ROC Curve",font=dict(size=14,color="#111",family="Inter")),
                        plot_bgcolor="#FFF",paper_bgcolor="#FFF",font=dict(family="Inter",color="#6B6B6B",size=12),
                        margin=dict(l=40,r=10,t=40,b=40),height=280,
                        xaxis=dict(title="FPR",gridcolor="#F5F5F5"),yaxis=dict(title="TPR",gridcolor="#F5F5F5"))
                    st.plotly_chart(fig_r, use_container_width=True, config={'displayModeBar':False}, key=f"roc_{idx}")
