"""
model_trainer.py — Model Training & Evaluation Engine
Trains: Logistic Regression, Decision Tree, Random Forest, XGBoost.
Saves: .pkl model files and model_metrics.json.
"""
import os, json, time
import numpy as np
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, roc_curve
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
METRICS_PATH = os.path.join(MODELS_DIR, "model_metrics.json")


def get_model_configs():
    return {
        "Logistic Regression": {
            "model": LogisticRegression(max_iter=1000, random_state=42, solver="lbfgs"),
            "abbreviation": "LR",
            "description": "Linear model using sigmoid function for fraud probability.",
            "icon": "📊"
        },
        "Decision Tree": {
            "model": DecisionTreeClassifier(max_depth=10, min_samples_split=5, random_state=42),
            "abbreviation": "DT",
            "description": "Tree-based model splitting data using feature thresholds.",
            "icon": "🌳"
        },
        "Random Forest": {
            "model": RandomForestClassifier(n_estimators=100, max_depth=15, min_samples_split=5, random_state=42, n_jobs=-1),
            "abbreviation": "RF",
            "description": "Ensemble of decision trees that votes on each prediction.",
            "icon": "🌲"
        },
        "XGBoost": {
            "model": XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, use_label_encoder=False, eval_metric="logloss", verbosity=0),
            "abbreviation": "XGB",
            "description": "Gradient-boosted trees learning sequentially from errors.",
            "icon": "⚡"
        }
    }


def evaluate_model(model, X_test, y_test):
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else y_pred
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    fpr_arr, tpr_arr, thresh_arr = roc_curve(y_test, y_proba)
    return {
        "accuracy": round(accuracy_score(y_test, y_pred) * 100, 2),
        "precision": round(precision_score(y_test, y_pred, zero_division=0) * 100, 2),
        "recall": round(recall_score(y_test, y_pred, zero_division=0) * 100, 2),
        "f1_score": round(f1_score(y_test, y_pred, zero_division=0) * 100, 2),
        "auc_roc": round(roc_auc_score(y_test, y_proba) * 100, 2),
        "confusion_matrix": {"true_negative": int(tn), "false_positive": int(fp), "false_negative": int(fn), "true_positive": int(tp)},
        "false_positive_rate": round(fp / (fp + tn) * 100, 4) if (fp + tn) > 0 else 0,
        "roc_curve": {"fpr": fpr_arr.tolist(), "tpr": tpr_arr.tolist(), "thresholds": thresh_arr.tolist()}
    }


def get_feature_importance(model, feature_names):
    if hasattr(model, "feature_importances_"):
        imp = model.feature_importances_
    elif hasattr(model, "coef_"):
        imp = np.abs(model.coef_[0])
    else:
        return []
    pairs = sorted(zip(feature_names, imp), key=lambda x: x[1], reverse=True)
    return [{"feature": f, "importance": round(float(v), 6)} for f, v in pairs]


def train_all_models(X_train, y_train, X_test, y_test, feature_names, progress_callback=None):
    os.makedirs(MODELS_DIR, exist_ok=True)
    configs = get_model_configs()
    results = {}
    total = len(configs)

    for idx, (name, cfg) in enumerate(configs.items()):
        if progress_callback:
            progress_callback(name, idx, total)
        t0 = time.time()
        cfg["model"].fit(X_train, y_train)
        train_time = round(time.time() - t0, 3)

        metrics = evaluate_model(cfg["model"], X_test, y_test)
        metrics["training_time_seconds"] = train_time
        metrics["feature_importance"] = get_feature_importance(cfg["model"], feature_names)

        fname = name.lower().replace(" ", "_") + ".pkl"
        joblib.dump(cfg["model"], os.path.join(MODELS_DIR, fname))
        metrics["model_filename"] = fname
        metrics["abbreviation"] = cfg["abbreviation"]
        metrics["description"] = cfg["description"]
        metrics["icon"] = cfg["icon"]
        results[name] = metrics

    if progress_callback:
        progress_callback("Done", total, total)

    # Save metrics JSON (exclude large arrays)
    save_data = {}
    for name, m in results.items():
        save_data[name] = {k: v for k, v in m.items() if k not in ("roc_curve", "feature_importance")}
        if m.get("feature_importance"):
            save_data[name]["top_features"] = m["feature_importance"][:15]

    save_data["_metadata"] = {
        "trained_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "num_train_samples": len(X_train),
        "num_test_samples": len(X_test),
        "num_features": len(feature_names),
        "feature_names": feature_names,
        "best_model": max(results.keys(), key=lambda k: results[k]["f1_score"])
    }
    with open(METRICS_PATH, "w") as f:
        json.dump(save_data, f, indent=2)

    return results


def load_model_metrics():
    if not os.path.exists(METRICS_PATH):
        return {}
    with open(METRICS_PATH, "r") as f:
        return json.load(f)


def load_trained_model(model_name: str):
    fname = model_name.lower().replace(" ", "_") + ".pkl"
    path = os.path.join(MODELS_DIR, fname)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model not found: {path}")
    return joblib.load(path)


def get_available_models():
    if not os.path.exists(MODELS_DIR):
        return []
    pkls = [f for f in os.listdir(MODELS_DIR) if f.endswith(".pkl") and f != "scaler.pkl"]
    return [f.replace(".pkl", "").replace("_", " ").title() for f in pkls]


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from src.data_engine import run_full_pipeline

    print("=" * 60)
    print("  FraudShield — Model Training Pipeline")
    print("=" * 60)

    print("\n[1/3] Loading and preprocessing data...")
    pipeline = run_full_pipeline()
    r = pipeline["validation_report"]
    print(f"  Dataset: {r['total_rows']} rows | Fraud: {r['fraud_count']} ({r['fraud_percentage']}%)")

    print(f"\n[2/3] SMOTE: Before={pipeline['before_smote']} | After={pipeline['after_smote']}")

    print("\n[3/3] Training models...")
    def cb(name, step, total):
        if step < total: print(f"  Training: {name}...")

    res = train_all_models(
        pipeline["X_train"], pipeline["y_train"],
        pipeline["X_test"], pipeline["y_test"],
        pipeline["feature_names"], progress_callback=cb
    )

    print("\n" + "=" * 60)
    print(f"  {'Model':<25} {'Acc':>7} {'Prec':>7} {'Rec':>7} {'F1':>7} {'AUC':>7}")
    print("-" * 60)
    for name, m in res.items():
        print(f"  {name:<25} {m['accuracy']:>6.2f}% {m['precision']:>6.2f}% {m['recall']:>6.2f}% {m['f1_score']:>6.2f}% {m['auc_roc']:>6.2f}%")
    print("=" * 60)
    best = max(res.keys(), key=lambda k: res[k]["f1_score"])
    print(f"\n  Best Model (F1): {best} ({res[best]['f1_score']}%)")
    print(f"  Models saved to: {MODELS_DIR}")
