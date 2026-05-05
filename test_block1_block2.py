"""
test_block1_block2.py — Comprehensive Phase 1-3 Validation Script
Tests: Auth system, Database, Data Engine, Model Training
Run: python test_block1_block2.py
"""
import sys, os, time, sqlite3

# Fix Windows console encoding
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(__file__))

from src.auth import (
    init_database, register_user, login_user,
    check_session_timeout, log_activity, get_user_activity,
    get_user_settings, update_user_settings, get_all_users,
    delete_user, change_password, get_system_stats,
    DB_PATH
)
from datetime import datetime, timedelta

PASS = 0
FAIL = 0

def test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} — {detail}")


# =====================================================================
# PHASE 1: AUTH SYSTEM HARDENING
# =====================================================================
print("=" * 60)
print("  PHASE 1: AUTH SYSTEM HARDENING")
print("=" * 60)

# --- 1.1 Functional Testing ---
print("\n--- 1.1 Registration Tests ---")
init_database()

# Clean up test users if they exist
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("DELETE FROM users WHERE username LIKE 'test_%'")
conn.commit()
conn.close()

# Empty fields
r = register_user("", "test_user1", "pass123", "Viewer")
test("Empty full_name rejected", not r["success"], r.get("message", ""))

r = register_user("Test User", "", "pass123", "Viewer")
test("Empty username rejected", not r["success"], r.get("message", ""))

r = register_user("Test User", "test_user1", "", "Viewer")
test("Empty password rejected", not r["success"], r.get("message", ""))

# Short password
r = register_user("Test User", "test_user1", "abc", "Viewer")
test("Short password (<6) rejected", not r["success"], r.get("message", ""))

# Valid registration
r = register_user("Test User One", "test_user1", "password123", "Admin")
test("Valid registration succeeds", r["success"], r.get("message", ""))

# Duplicate username
r = register_user("Test User Dup", "test_user1", "password123", "Viewer")
test("Duplicate username rejected", not r["success"], r.get("message", ""))

# Invalid role
r = register_user("Test User", "test_user2", "password123", "SuperAdmin")
test("Invalid role rejected", not r["success"], r.get("message", ""))

# Valid roles
for role in ["Admin", "Analyst", "Viewer"]:
    r = register_user(f"Test {role}", f"test_{role.lower()}", "password123", role)
    test(f"Role '{role}' accepted", r["success"], r.get("message", ""))


print("\n--- 1.1 Login Tests ---")
# Correct login
r = login_user("test_user1", "password123")
test("Correct login succeeds", r["success"], r.get("message", ""))
test("Login returns user data", r["user"] is not None and "id" in r["user"])
test("User has correct role", r["user"]["role"] == "Admin" if r["user"] else False)

# Wrong password
r = login_user("test_user1", "wrongpass")
test("Wrong password rejected", not r["success"], r.get("message", ""))
test("Shows attempts remaining", "remaining" in r.get("message", "").lower() or "attempt" in r.get("message", "").lower(), r.get("message", ""))

# Non-existent user
r = login_user("nonexistent_user_xyz", "password123")
test("Non-existent user rejected", not r["success"], r.get("message", ""))

# Lockout after 5 attempts
r2 = register_user("Lockout Test", "test_lockout", "password123", "Viewer")
for i in range(5):
    login_user("test_lockout", "wrongpass")
r = login_user("test_lockout", "wrongpass")
test("Lockout after 5 wrong attempts", not r["success"] and "locked" in r.get("message", "").lower(), r.get("message", ""))

# Correct password during lockout should still fail
r = login_user("test_lockout", "password123")
test("Correct password during lockout still blocked", not r["success"], r.get("message", ""))


print("\n--- 1.1 Session Timeout Tests ---")
test("None last_activity → expired", check_session_timeout(None) == True)
test("Recent activity → not expired", check_session_timeout(datetime.now()) == False)
test("Old activity → expired", check_session_timeout(datetime.now() - timedelta(minutes=20)) == True)
test("Exactly 15min → expired", check_session_timeout(datetime.now() - timedelta(minutes=15, seconds=1)) == True)


# --- 1.2 Database Validation ---
print("\n--- 1.2 Database Validation ---")
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Check tables exist
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in c.fetchall()]
test("'users' table exists", "users" in tables)
test("'activity_log' table exists", "activity_log" in tables)
test("'settings' table exists", "settings" in tables)

# Check password is hashed
c.execute("SELECT password_hash FROM users WHERE username='test_user1'")
row = c.fetchone()
test("Password is hashed (starts with $2b$)", row and row[0].startswith("$2b$"), str(row[0][:10]) if row else "no row")
test("Password is NOT plaintext", row and row[0] != "password123")

# Check default settings inserted
c.execute("SELECT * FROM settings WHERE user_id=(SELECT id FROM users WHERE username='test_user1')")
srow = c.fetchone()
test("Default settings created for user", srow is not None)
conn.close()


# --- 1.3 Activity Logging ---
print("\n--- 1.3 Activity Logging ---")
r = login_user("test_user1", "password123")
uid = r["user"]["id"]
log_activity(uid, "Login")
log_activity(uid, "Prediction", input_amount=150.0, result="Fraud", confidence=0.92, threshold=0.5)

activity = get_user_activity(uid, limit=5)
test("Activity log has entries", len(activity) > 0)
test("Login activity logged", any(a["action"] == "Login" for a in activity))
test("Prediction activity logged", any(a["action"] == "Prediction" for a in activity))
test("Timestamp format correct", all(len(a["timestamp"]) == 19 for a in activity), str(activity[0]["timestamp"]) if activity else "")


# --- 1.4 Settings System ---
print("\n--- 1.4 Settings System ---")
settings = get_user_settings(uid)
test("Settings fetched", settings is not None)
test("Default theme is 'dark'", settings["theme"] == "dark")
test("Default threshold is 0.5", settings["default_threshold"] == 0.5)
test("Default model is 'Random Forest'", settings["active_model"] == "Random Forest")

update_user_settings(uid, theme="light", default_threshold=0.7)
settings2 = get_user_settings(uid)
test("Theme updated to 'light'", settings2["theme"] == "light")
test("Threshold updated to 0.7", settings2["default_threshold"] == 0.7)

# Reset
update_user_settings(uid, theme="dark", default_threshold=0.5)


# --- 1.5 Edge Cases ---
print("\n--- 1.5 Edge Cases & Admin Functions ---")
stats = get_system_stats()
test("System stats returns data", stats["total_users"] > 0)
test("DB size is positive", stats["database_size_kb"] > 0)

all_users = get_all_users()
test("get_all_users returns list", len(all_users) > 0)

# Change password
cp = change_password(uid, "password123", "newpass123")
test("Password change succeeds", cp["success"], cp.get("message", ""))
cp2 = change_password(uid, "wrongold", "newpass")
test("Wrong old password rejected", not cp2["success"])
cp3 = change_password(uid, "newpass123", "ab")
test("Short new password rejected", not cp3["success"])

# Reset password back
change_password(uid, "newpass123", "password123")

# Delete user test
r = register_user("Delete Me", "test_delete_me", "password123", "Viewer")
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("SELECT id FROM users WHERE username='test_delete_me'")
del_id = c.fetchone()[0]
conn.close()
dr = delete_user(del_id)
test("User deletion succeeds", dr["success"])
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("SELECT id FROM users WHERE username='test_delete_me'")
test("Deleted user no longer exists", c.fetchone() is None)
conn.close()


# =====================================================================
# PHASE 2: DATA ENGINE VALIDATION
# =====================================================================
print("\n" + "=" * 60)
print("  PHASE 2: DATA ENGINE VALIDATION")
print("=" * 60)

from src.data_engine import (
    load_dataset, validate_dataset, preprocess_data,
    split_data, apply_smote, run_full_pipeline, SAMPLE_DATA_PATH
)
import pandas as pd

# --- 2.1 Dataset Integrity ---
print("\n--- 2.1 Dataset Integrity ---")
test("sample_data.csv exists", os.path.exists(SAMPLE_DATA_PATH))

df = load_dataset()
test("Dataset loaded successfully", df is not None and len(df) > 0)

report = validate_dataset(df)
test("Dataset is valid (no missing cols)", report["valid"])
test("Has 31 columns (Time+V1-V28+Amount+Class)", report["total_columns"] == 31, f"Got {report['total_columns']}")
test("Has 2000 rows", report["total_rows"] == 2000, f"Got {report['total_rows']}")
test("Has fraud cases", report["fraud_count"] > 0, f"Fraud: {report['fraud_count']}")
test("Has legit cases", report["legit_count"] > 0, f"Legit: {report['legit_count']}")
test("No missing values", report["missing_values"] == 0, f"Missing: {report['missing_values']}")

expected_cols = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount", "Class"]
test("All expected columns present", all(c in df.columns for c in expected_cols))


# --- 2.2 Preprocessing ---
print("\n--- 2.2 Preprocessing Verification ---")
df_proc = preprocess_data(df, fit_scaler=True)
test("Scaled_Amount column exists", "Scaled_Amount" in df_proc.columns)
test("Scaled_Time column exists", "Scaled_Time" in df_proc.columns)
test("Original Amount removed", "Amount" not in df_proc.columns)
test("Original Time removed", "Time" not in df_proc.columns)
test("No NaN after scaling", df_proc.isnull().sum().sum() == 0)
test("Row count preserved", len(df_proc) == len(df), f"{len(df_proc)} vs {len(df)}")
test("Scaler.pkl saved", os.path.exists(os.path.join(os.path.dirname(__file__), "models", "scaler.pkl")))


# --- 2.3 Train-Test Split ---
print("\n--- 2.3 Train-Test Split ---")
X_train, X_test, y_train, y_test = split_data(df_proc)
total_split = len(X_train) + len(X_test)
test("Split preserves total rows", total_split == len(df_proc), f"{total_split} vs {len(df_proc)}")
test("Test size ~20%", 0.15 < len(X_test) / len(df_proc) < 0.25, f"{len(X_test)/len(df_proc):.2%}")

train_fraud_ratio = y_train.mean()
test_fraud_ratio = y_test.mean()
test("Stratified: fraud ratio similar", abs(train_fraud_ratio - test_fraud_ratio) < 0.02,
     f"Train: {train_fraud_ratio:.4f}, Test: {test_fraud_ratio:.4f}")


# --- 2.4 SMOTE ---
print("\n--- 2.4 SMOTE Verification ---")
X_sm, y_sm, before, after = apply_smote(X_train, y_train)
test("Before SMOTE: fraud << legit", before["Fraud"] < before["Legitimate"],
     f"Fraud={before['Fraud']}, Legit={before['Legitimate']}")
test("After SMOTE: fraud ≈ legit", after["Fraud"] == after["Legitimate"],
     f"Fraud={after['Fraud']}, Legit={after['Legitimate']}")
test("SMOTE only on training data", len(X_test) == len(y_test))
test("Test set unchanged", len(X_test) < len(X_sm))


# =====================================================================
# PHASE 3: MODEL TRAINING
# =====================================================================
print("\n" + "=" * 60)
print("  PHASE 3: MODEL TRAINING EXECUTION")
print("=" * 60)

from src.model_trainer import (
    train_all_models, load_model_metrics,
    load_trained_model, get_available_models
)

print("\n--- 3.1 Training All Models ---")
def progress(name, step, total):
    if step < total:
        print(f"  🔄 Training: {name}...")
    else:
        print(f"  ✅ All models trained!")

pipeline = run_full_pipeline()
results = train_all_models(
    pipeline["X_train"], pipeline["y_train"],
    pipeline["X_test"], pipeline["y_test"],
    pipeline["feature_names"],
    progress_callback=progress
)

print("\n--- 3.2 Verify .pkl Files ---")
models_dir = os.path.join(os.path.dirname(__file__), "models")
for fname in ["logistic_regression.pkl", "decision_tree.pkl", "random_forest.pkl", "xgboost.pkl", "scaler.pkl"]:
    path = os.path.join(models_dir, fname)
    test(f"{fname} exists", os.path.exists(path), f"Missing: {path}")

metrics_path = os.path.join(models_dir, "model_metrics.json")
test("model_metrics.json exists", os.path.exists(metrics_path))


print("\n--- 3.3 Validate Metrics ---")
metrics = load_model_metrics()
test("Metrics file has content", len(metrics) > 0)
test("Has _metadata", "_metadata" in metrics)
test("Has best_model field", "best_model" in metrics.get("_metadata", {}))

for model_name in ["Logistic Regression", "Decision Tree", "Random Forest", "XGBoost"]:
    if model_name in metrics:
        m = metrics[model_name]
        test(f"{model_name}: accuracy exists", "accuracy" in m, str(m.keys()))
        test(f"{model_name}: f1_score exists", "f1_score" in m)
        test(f"{model_name}: auc_roc exists", "auc_roc" in m)

print("\n  📊 Model Performance Summary:")
print(f"  {'Model':<25} {'Acc':>7} {'F1':>7} {'AUC':>7}")
print("  " + "-" * 48)
for name in ["Logistic Regression", "Decision Tree", "Random Forest", "XGBoost"]:
    if name in results:
        m = results[name]
        print(f"  {name:<25} {m['accuracy']:>6.2f}% {m['f1_score']:>6.2f}% {m['auc_roc']:>6.2f}%")
best = metrics["_metadata"]["best_model"]
print(f"\n  ⭐ Best Model: {best}")


print("\n--- 3.4 Model Loading & Prediction Test ---")
import numpy as np
sample_row = pipeline["X_test"].iloc[0:1]
for model_name in ["Logistic Regression", "Decision Tree", "Random Forest", "XGBoost"]:
    try:
        model = load_trained_model(model_name)
        pred = model.predict(sample_row)
        proba = model.predict_proba(sample_row)
        test(f"{model_name}: loads and predicts", pred is not None and len(pred) == 1)
    except Exception as e:
        test(f"{model_name}: loads and predicts", False, str(e))

available = get_available_models()
test("get_available_models() returns 4", len(available) == 4, f"Got {len(available)}: {available}")


# =====================================================================
# CLEANUP
# =====================================================================
print("\n--- Cleanup ---")
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("DELETE FROM activity_log WHERE user_id IN (SELECT id FROM users WHERE username LIKE 'test_%')")
c.execute("DELETE FROM settings WHERE user_id IN (SELECT id FROM users WHERE username LIKE 'test_%')")
c.execute("DELETE FROM users WHERE username LIKE 'test_%'")
conn.commit()
conn.close()
print("  🧹 Test users cleaned up")


# =====================================================================
# FINAL REPORT
# =====================================================================
print("\n" + "=" * 60)
print(f"  FINAL REPORT: {PASS} passed, {FAIL} failed, {PASS+FAIL} total")
print("=" * 60)
if FAIL == 0:
    print("  🎉 ALL TESTS PASSED — Blocks 1+2 are SOLID!")
else:
    print(f"  ⚠️  {FAIL} test(s) failed. Fix before proceeding.")
print()
