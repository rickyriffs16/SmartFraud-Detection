"""
data_engine.py — Data Loading, Preprocessing & SMOTE Balancing
Handles: CSV loading, feature scaling (StandardScaler on Amount & Time),
         SMOTE oversampling on training data, and train/test splitting.
"""

import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE
import joblib

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
SAMPLE_DATA_PATH = os.path.join(DATA_DIR, "sample_data.csv")
SCALER_PATH = os.path.join(MODELS_DIR, "scaler.pkl")


# ============================= DATA LOADING ================================
def load_dataset(file_path: str = None) -> pd.DataFrame:
    """
    Load a credit card fraud dataset CSV.
    Expected columns: Time, V1-V28, Amount, Class
    Falls back to sample_data.csv if no path given.
    """
    if file_path is None or not os.path.exists(file_path):
        file_path = SAMPLE_DATA_PATH

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Dataset not found at {file_path}. "
            "Please upload a CSV or ensure sample_data.csv exists in /data."
        )

    df = pd.read_csv(file_path)
    return df


def validate_dataset(df: pd.DataFrame) -> dict:
    """
    Validate that the dataframe has the expected columns and structure.
    Returns a report dict.
    """
    expected_features = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount", "Class"]
    missing_cols = [c for c in expected_features if c not in df.columns]
    extra_cols = [c for c in df.columns if c not in expected_features]

    report = {
        "valid": len(missing_cols) == 0,
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "missing_columns": missing_cols,
        "extra_columns": extra_cols,
        "missing_values": int(df.isnull().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "fraud_count": int(df["Class"].sum()) if "Class" in df.columns else 0,
        "legit_count": int((df["Class"] == 0).sum()) if "Class" in df.columns else 0,
        "fraud_percentage": round(
            (df["Class"].sum() / len(df)) * 100, 4
        ) if "Class" in df.columns and len(df) > 0 else 0,
        "amount_min": round(float(df["Amount"].min()), 2) if "Amount" in df.columns else 0,
        "amount_max": round(float(df["Amount"].max()), 2) if "Amount" in df.columns else 0,
        "amount_mean": round(float(df["Amount"].mean()), 2) if "Amount" in df.columns else 0,
    }
    return report


# ============================= PREPROCESSING ===============================
def preprocess_data(df: pd.DataFrame, fit_scaler: bool = True) -> pd.DataFrame:
    """
    Preprocess the dataset:
    1. Scale 'Amount' and 'Time' using StandardScaler.
    2. Drop original 'Amount' and 'Time', replace with scaled versions.

    If fit_scaler=True, fits a new scaler and saves it.
    If fit_scaler=False, loads the saved scaler (for prediction on new data).
    """
    df = df.copy()

    if fit_scaler:
        scaler = StandardScaler()
        df["Scaled_Amount"] = scaler.fit_transform(df[["Amount"]])

        # Also scale Time
        time_scaler = StandardScaler()
        df["Scaled_Time"] = time_scaler.fit_transform(df[["Time"]])

        # Save scalers
        os.makedirs(MODELS_DIR, exist_ok=True)
        joblib.dump({"amount_scaler": scaler, "time_scaler": time_scaler}, SCALER_PATH)
    else:
        if not os.path.exists(SCALER_PATH):
            raise FileNotFoundError("Scaler not found. Train models first.")
        scalers = joblib.load(SCALER_PATH)
        df["Scaled_Amount"] = scalers["amount_scaler"].transform(df[["Amount"]])
        df["Scaled_Time"] = scalers["time_scaler"].transform(df[["Time"]])

    # Drop originals, keep scaled
    df.drop(["Amount", "Time"], axis=1, inplace=True)

    return df


# ============================= TRAIN/TEST SPLIT ============================
def split_data(df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42):
    """
    Split preprocessed data into X_train, X_test, y_train, y_test.
    """
    X = df.drop("Class", axis=1)
    y = df["Class"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    return X_train, X_test, y_train, y_test


# ============================= SMOTE BALANCING =============================
def apply_smote(X_train: pd.DataFrame, y_train: pd.Series, random_state: int = 42):
    """
    Apply SMOTE oversampling to the TRAINING data only.
    Returns balanced X_train_smote, y_train_smote and before/after counts.
    """
    before_counts = {
        "Legitimate": int((y_train == 0).sum()),
        "Fraud": int((y_train == 1).sum())
    }

    smote = SMOTE(random_state=random_state)
    X_resampled, y_resampled = smote.fit_resample(X_train, y_train)

    after_counts = {
        "Legitimate": int((y_resampled == 0).sum()),
        "Fraud": int((y_resampled == 1).sum())
    }

    return X_resampled, y_resampled, before_counts, after_counts


# ============================= FULL PIPELINE ===============================
def run_full_pipeline(file_path: str = None):
    """
    Complete data pipeline: Load → Validate → Preprocess → Split → SMOTE.
    Returns everything needed for model training.
    """
    # Step 1: Load
    df = load_dataset(file_path)

    # Step 2: Validate
    report = validate_dataset(df)
    if not report["valid"]:
        raise ValueError(f"Dataset validation failed. Missing columns: {report['missing_columns']}")

    # Step 3: Preprocess
    df_processed = preprocess_data(df, fit_scaler=True)

    # Step 4: Split
    X_train, X_test, y_train, y_test = split_data(df_processed)

    # Step 5: SMOTE (training data only)
    X_train_smote, y_train_smote, before_smote, after_smote = apply_smote(X_train, y_train)

    return {
        "X_train": X_train_smote,
        "X_test": X_test,
        "y_train": y_train_smote,
        "y_test": y_test,
        "X_train_original": X_train,
        "y_train_original": y_train,
        "before_smote": before_smote,
        "after_smote": after_smote,
        "validation_report": report,
        "feature_names": list(X_train.columns),
        "raw_df": df,
    }
