"""
predictor.py — Prediction Engine
Handles: Loading models/scalers, preprocessing input, predicting fraud,
         and applying threshold-based classification.
"""
import os
import numpy as np
import pandas as pd
import joblib

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
SCALER_PATH = os.path.join(MODELS_DIR, "scaler.pkl")


def load_model_and_scaler(model_name: str = "Random Forest"):
    """
    Load a trained model and the fitted scaler.
    Returns: (model, scalers_dict)
    """
    model_filename = model_name.lower().replace(" ", "_") + ".pkl"
    model_path = os.path.join(MODELS_DIR, model_filename)

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found: {model_path}")
    if not os.path.exists(SCALER_PATH):
        raise FileNotFoundError(f"Scaler not found: {SCALER_PATH}")

    model = joblib.load(model_path)
    scalers = joblib.load(SCALER_PATH)

    return model, scalers


def preprocess_input(data: dict, scalers: dict) -> pd.DataFrame:
    """
    Preprocess a single transaction input for prediction.

    Args:
        data: dict with keys 'Amount', 'Time', 'V1'-'V28'
        scalers: dict with 'amount_scaler' and 'time_scaler'

    Returns:
        DataFrame ready for model.predict()
    """
    amount = float(data.get("Amount", 0))
    time_val = float(data.get("Time", 0))

    import pandas as _pd
    scaled_amount = scalers["amount_scaler"].transform(_pd.DataFrame([[amount]], columns=["Amount"]))[0][0]
    scaled_time = scalers["time_scaler"].transform(_pd.DataFrame([[time_val]], columns=["Time"]))[0][0]

    features = {}
    for i in range(1, 29):
        features[f"V{i}"] = float(data.get(f"V{i}", 0))

    features["Scaled_Amount"] = scaled_amount
    features["Scaled_Time"] = scaled_time

    df = pd.DataFrame([features])

    expected_order = [f"V{i}" for i in range(1, 29)] + ["Scaled_Amount", "Scaled_Time"]
    df = df[expected_order]

    return df


def predict_transaction(data: dict, threshold: float = 0.5,
                        model_name: str = "Random Forest") -> dict:
    """
    Predict whether a transaction is fraud or legitimate.

    Args:
        data: dict with keys 'Amount', 'Time', 'V1'-'V28'
        threshold: probability cutoff (>= threshold = Fraud)
        model_name: which model to use

    Returns:
        {
            "prediction": "Fraud" / "Legit",
            "probability": 0.87,
            "threshold": 0.5,
            "model_used": "Random Forest"
        }
    """
    model, scalers = load_model_and_scaler(model_name)
    input_df = preprocess_input(data, scalers)

    proba = model.predict_proba(input_df)[0]
    fraud_probability = float(proba[1])

    if fraud_probability >= threshold:
        prediction = "Fraud"
    else:
        prediction = "Legit"

    return {
        "prediction": prediction,
        "probability": round(fraud_probability, 4),
        "threshold": threshold,
        "model_used": model_name
    }


def predict_batch(df: pd.DataFrame, threshold: float = 0.5,
                  model_name: str = "Random Forest") -> pd.DataFrame:
    """
    Predict fraud for a batch of transactions (DataFrame).

    Args:
        df: DataFrame with Time, V1-V28, Amount columns
        threshold: probability cutoff
        model_name: which model to use

    Returns:
        Original df with added 'Prediction' and 'Fraud_Probability' columns
    """
    model, scalers = load_model_and_scaler(model_name)

    df_result = df.copy()

    scaled_amount = scalers["amount_scaler"].transform(df[["Amount"]])
    scaled_time = scalers["time_scaler"].transform(df[["Time"]])

    features = df[[f"V{i}" for i in range(1, 29)]].copy()
    features["Scaled_Amount"] = scaled_amount
    features["Scaled_Time"] = scaled_time

    probas = model.predict_proba(features)[:, 1]

    df_result["Fraud_Probability"] = np.round(probas, 4)
    df_result["Prediction"] = np.where(probas >= threshold, "Fraud", "Legit")

    return df_result
