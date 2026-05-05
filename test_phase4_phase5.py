"""
test_phase4_phase5.py — Predictor Engine + Integration Tests
Tests: predictor.py + full end-to-end flow + logging integration
Run: python -X utf8 test_phase4_phase5.py
"""
import sys, os
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import pandas as pd
from src.predictor import load_model_and_scaler, preprocess_input, predict_transaction, predict_batch
from src.data_engine import load_dataset, run_full_pipeline
from src.model_trainer import load_trained_model
from src.auth import init_database, log_activity, get_user_activity, register_user, login_user
import sqlite3

PASS = 0
FAIL = 0

def test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} -- {detail}")


# =====================================================================
# PHASE 4: PREDICTOR ENGINE
# =====================================================================
print("=" * 60)
print("  PHASE 4: PREDICTION ENGINE")
print("=" * 60)

# --- 4.1 Load model and scaler ---
print("\n--- 4.1 Load Model & Scaler ---")
for model_name in ["Logistic Regression", "Decision Tree", "Random Forest", "XGBoost"]:
    try:
        model, scalers = load_model_and_scaler(model_name)
        test(f"Load {model_name}", model is not None and scalers is not None)
    except Exception as e:
        test(f"Load {model_name}", False, str(e))

test("Scaler has amount_scaler", "amount_scaler" in scalers)
test("Scaler has time_scaler", "time_scaler" in scalers)

# --- 4.2 Preprocess input ---
print("\n--- 4.2 Preprocess Input ---")
sample_input = {"Time": 5000, "Amount": 150.0}
for i in range(1, 29):
    sample_input[f"V{i}"] = np.random.randn()

_, scalers = load_model_and_scaler("Random Forest")
processed = preprocess_input(sample_input, scalers)
test("Preprocessed output is DataFrame", isinstance(processed, pd.DataFrame))
test("Has 30 columns (V1-V28 + Scaled_Amount + Scaled_Time)", len(processed.columns) == 30, f"Got {len(processed.columns)}")
test("No NaN in processed input", processed.isnull().sum().sum() == 0)
test("Has Scaled_Amount", "Scaled_Amount" in processed.columns)
test("Has Scaled_Time", "Scaled_Time" in processed.columns)
test("Does NOT have raw Amount", "Amount" not in processed.columns)
test("Does NOT have raw Time", "Time" not in processed.columns)

# --- 4.3 Predict single transaction ---
print("\n--- 4.3 Single Transaction Prediction ---")

# Test with legit-like input (near-zero V features)
legit_input = {"Time": 5000, "Amount": 25.0}
for i in range(1, 29):
    legit_input[f"V{i}"] = 0.0

result = predict_transaction(legit_input, threshold=0.5, model_name="Random Forest")
test("Result has 'prediction' key", "prediction" in result)
test("Result has 'probability' key", "probability" in result)
test("Result has 'threshold' key", "threshold" in result)
test("Result has 'model_used' key", "model_used" in result)
test("Prediction is Fraud or Legit", result["prediction"] in ("Fraud", "Legit"), result["prediction"])
test("Probability is 0-1 range", 0 <= result["probability"] <= 1, f"Got {result['probability']}")
test("Threshold matches input", result["threshold"] == 0.5)
test("Model name matches", result["model_used"] == "Random Forest")
print(f"    -> Legit-like input: {result['prediction']} (p={result['probability']})")

# Test with fraud-like input (shifted V features)
fraud_input = {"Time": 80000, "Amount": 500.0}
fraud_input["V1"] = -3.5
fraud_input["V2"] = 2.8
fraud_input["V3"] = -4.2
fraud_input["V4"] = 3.0
fraud_input["V5"] = -2.0
fraud_input["V7"] = -3.5
fraud_input["V10"] = -4.0
fraud_input["V11"] = 3.5
fraud_input["V12"] = -5.0
fraud_input["V14"] = -5.5
fraud_input["V16"] = -4.0
fraud_input["V17"] = -4.5
for i in range(1, 29):
    if f"V{i}" not in fraud_input:
        fraud_input[f"V{i}"] = 0.0

result_fraud = predict_transaction(fraud_input, threshold=0.5, model_name="Random Forest")
test("Fraud-like input detected as Fraud", result_fraud["prediction"] == "Fraud",
     f"Got {result_fraud['prediction']} (p={result_fraud['probability']})")
print(f"    -> Fraud-like input: {result_fraud['prediction']} (p={result_fraud['probability']})")

# --- Threshold logic ---
print("\n--- 4.3 Threshold Logic ---")
# Low threshold should catch more fraud
result_low = predict_transaction(legit_input, threshold=0.01, model_name="Random Forest")
# High threshold should let more through
result_high = predict_transaction(fraud_input, threshold=0.99, model_name="Random Forest")
test("High threshold (0.99) makes fraud prediction harder",
     result_high["prediction"] == "Legit" or result_high["probability"] >= 0.99,
     f"p={result_high['probability']}, pred={result_high['prediction']}")

# Test all 4 models predict without crashing
print("\n--- 4.3 All Models Predict ---")
for model_name in ["Logistic Regression", "Decision Tree", "Random Forest", "XGBoost"]:
    try:
        r = predict_transaction(legit_input, threshold=0.5, model_name=model_name)
        test(f"{model_name} predicts OK", r["prediction"] in ("Fraud", "Legit"))
    except Exception as e:
        test(f"{model_name} predicts OK", False, str(e))

# --- Batch prediction ---
print("\n--- 4.3 Batch Prediction ---")
df = load_dataset()
batch_df = df.head(20)
result_batch = predict_batch(batch_df, threshold=0.5, model_name="Random Forest")
test("Batch result has Prediction column", "Prediction" in result_batch.columns)
test("Batch result has Fraud_Probability column", "Fraud_Probability" in result_batch.columns)
test("Batch preserves row count", len(result_batch) == 20, f"Got {len(result_batch)}")
test("All predictions are Fraud or Legit",
     set(result_batch["Prediction"].unique()).issubset({"Fraud", "Legit"}))
test("All probabilities in 0-1",
     (result_batch["Fraud_Probability"] >= 0).all() and (result_batch["Fraud_Probability"] <= 1).all())


# =====================================================================
# PHASE 5: INTEGRATION TEST
# =====================================================================
print("\n" + "=" * 60)
print("  PHASE 5: END-TO-END INTEGRATION TEST")
print("=" * 60)

# --- 5.1 Full flow: Load -> Pipeline -> Predict ---
print("\n--- 5.1 Full End-to-End Flow ---")
try:
    # Step 1: Load dataset
    df = load_dataset()
    test("Step 1: Dataset loaded", len(df) > 0)

    # Step 2: Run pipeline
    pipeline = run_full_pipeline()
    test("Step 2: Pipeline completed", pipeline is not None)

    # Step 3: Take a sample row from test set
    sample_row = pipeline["X_test"].iloc[0]
    actual_label = int(pipeline["y_test"].iloc[0])

    # Convert to dict format for predictor
    raw_df = pipeline["raw_df"]
    sample_raw = raw_df.iloc[0].to_dict()

    # Step 4: Predict
    pred_result = predict_transaction(sample_raw, threshold=0.5, model_name="Random Forest")
    test("Step 3-4: Prediction returned", pred_result is not None)
    test("Step 4: Has valid prediction", pred_result["prediction"] in ("Fraud", "Legit"))
    print(f"    -> Sample prediction: {pred_result['prediction']} (p={pred_result['probability']})")

except Exception as e:
    test("End-to-end flow", False, str(e))

# --- 5.2 Test cases ---
print("\n--- 5.2 Specific Test Cases ---")

# Legit transaction
legit = {"Time": 1000, "Amount": 12.50}
for i in range(1, 29):
    legit[f"V{i}"] = np.random.randn() * 0.3  # Small values
r = predict_transaction(legit, threshold=0.5)
test("Legit-like transaction predicts", r["prediction"] in ("Fraud", "Legit"))
print(f"    -> Legit test: {r['prediction']} (p={r['probability']})")

# Fraud-like transaction
fraud = {"Time": 80000, "Amount": 800.0,
         "V1": -3.5, "V2": 2.8, "V3": -4.2, "V4": 3.0, "V5": -2.0,
         "V7": -3.5, "V10": -4.0, "V11": 3.5, "V12": -5.0, "V14": -5.5,
         "V16": -4.0, "V17": -4.5}
for i in range(1, 29):
    if f"V{i}" not in fraud:
        fraud[f"V{i}"] = 0.0
r = predict_transaction(fraud, threshold=0.5)
test("Fraud-like transaction detected", r["prediction"] == "Fraud",
     f"Got {r['prediction']} p={r['probability']}")
print(f"    -> Fraud test: {r['prediction']} (p={r['probability']})")

# Edge: all zeros
zeros = {"Time": 0, "Amount": 0}
for i in range(1, 29):
    zeros[f"V{i}"] = 0.0
r = predict_transaction(zeros, threshold=0.5)
test("All-zero input: no crash", r["prediction"] in ("Fraud", "Legit"))

# Edge: very large amount
big = {"Time": 100000, "Amount": 99999.99}
for i in range(1, 29):
    big[f"V{i}"] = 0.0
r = predict_transaction(big, threshold=0.5)
test("Large amount input: no crash", r["prediction"] in ("Fraud", "Legit"))

# --- 5.3 Logging Integration ---
print("\n--- 5.3 Logging Integration ---")
init_database()

# Create a test user for logging
DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("DELETE FROM users WHERE username='test_integration'")
conn.commit()
conn.close()

reg = register_user("Integration Test", "test_integration", "pass123456", "Analyst")
login_result = login_user("test_integration", "pass123456")
test_uid = login_result["user"]["id"]

# Log a prediction
pred = predict_transaction(fraud, threshold=0.5, model_name="Random Forest")
log_activity(
    user_id=test_uid,
    action_type="Prediction",
    input_amount=fraud["Amount"],
    result=pred["prediction"],
    confidence=pred["probability"],
    threshold=pred["threshold"]
)

# Verify the log
activity = get_user_activity(test_uid, limit=5)
test("Prediction logged to DB", len(activity) > 0)
pred_log = [a for a in activity if a["action"] == "Prediction"]
test("Prediction entry found", len(pred_log) > 0)
if pred_log:
    test("Logged amount correct", pred_log[0]["amount"] == fraud["Amount"])
    test("Logged result correct", pred_log[0]["result"] == pred["prediction"])
    test("Logged confidence exists", pred_log[0]["confidence"] is not None)
    test("Logged threshold exists", pred_log[0]["threshold"] is not None)

# Cleanup
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("DELETE FROM activity_log WHERE user_id=?", (test_uid,))
c.execute("DELETE FROM settings WHERE user_id=?", (test_uid,))
c.execute("DELETE FROM users WHERE username='test_integration'")
conn.commit()
conn.close()
print("  Cleanup done")


# =====================================================================
# FINAL REPORT
# =====================================================================
print("\n" + "=" * 60)
print(f"  FINAL REPORT: {PASS} passed, {FAIL} failed, {PASS+FAIL} total")
print("=" * 60)
if FAIL == 0:
    print("  ALL TESTS PASSED - Phases 4+5 COMPLETE!")
    print("  Block 1+2 is FULLY SOLID. Ready for Block 3.")
else:
    print(f"  {FAIL} test(s) failed. Fix before proceeding.")
print()
